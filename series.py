from collections import defaultdict
import re

from database import get_all_library, get_connection

# Relations that can connect entries belonging to the same bundle/series.
SERIES_RELATIONS = {"PREQUEL", "SEQUEL", "PARENT", "SIDE_STORY", "SUMMARY", "FULL_STORY"}


def _series_key(title):
    """Conservative title normalization for season-title variants."""
    value = (title or "").lower().strip()
    value = re.sub(r"\s*[:\-–—]?\s*(the\s+)?final\s+season(?:\s+part\s+\d+)?\s*$", "", value)
    value = re.sub(r"\s*[:\-–—]?\s*(?:season|series)\s*(?:\d+|[ivx]+)(?:\s+part\s+\d+)?\s*$", "", value)
    value = re.sub(r"\s*[:\-–—]?\s*(?:part|cour)\s*\d+\s*$", "", value)
    value = re.sub(r"\s+(?:ii|iii|iv|v|vi|2nd|3rd|4th|5th)\s*(?:season)?\s*$", "", value)
    value = re.sub(r"\s+\d+$", "", value)
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def _relation_data_for(ids):
    if not ids:
        return []

    placeholders = ",".join("?" for _ in ids)
    relation_types = ",".join(repr(value) for value in SERIES_RELATIONS)
    connection = get_connection()
    rows = connection.execute(
        f"""
        SELECT source_id, target_id, relation_type
        FROM work_relations
        WHERE relation_type IN ({relation_types})
          AND (source_id IN ({placeholders}) OR target_id IN ({placeholders}))
        """,
        [*ids, *ids],
    ).fetchall()
    connection.close()
    return rows


def _bundle_summary(members):
    """Build a compact human-readable breakdown for a bundle."""
    counts = defaultdict(int)
    for member in members:
        fmt = str(member["format"] or "").upper()
        if fmt in {"TV", "TV_SHORT"}:
            counts["seasons"] += 1
        elif fmt == "OVA":
            counts["OVAs"] += 1
        elif fmt == "ONA":
            counts["ONAs"] += 1
        elif fmt == "MOVIE":
            counts["movies"] += 1
        elif fmt == "SPECIAL":
            counts["specials"] += 1
        elif fmt == "MUSIC":
            counts["music"] += 1
        elif fmt:
            counts[fmt.lower()] += 1
        else:
            counts["entries"] += 1

    order = ["seasons", "OVAs", "ONAs", "movies", "specials", "music"]
    parts = [f"{counts[key]} {key}" for key in order if counts[key]]
    extras = [f"{count} {key}" for key, count in counts.items() if key not in order]
    return " · ".join(parts + extras)


def get_library_series():
    """Return library works grouped locally using already-cached relations and titles.

    This function deliberately does no network I/O. Library rendering must remain
    instant and usable offline; relation syncing belongs to explicit import/search
    workflows, not application startup.
    """
    rows = list(get_all_library())
    if not rows:
        return []

    ids = {int(row["id"]) for row in rows}
    parent = {work_id: work_id for work_id in ids}

    def find(work_id):
        while parent[work_id] != work_id:
            parent[work_id] = parent[parent[work_id]]
            work_id = parent[work_id]
        return work_id

    def union(left, right):
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for relation in _relation_data_for(ids):
        source_id = int(relation["source_id"])
        target_id = int(relation["target_id"])
        if source_id in ids and target_id in ids:
            union(source_id, target_id)

    # Fall back to obvious season-title variants for entries that pre-date relation storage.
    by_title = {}
    for row in rows:
        key = _series_key(row["title"])
        if not key:
            continue
        if key in by_title:
            union(int(row["id"]), by_title[key])
        else:
            by_title[key] = int(row["id"])

    groups = defaultdict(list)
    for row in rows:
        groups[find(int(row["id"]))].append(row)

    result = []
    for members in groups.values():
        members.sort(key=lambda row: (
            row["start_year"] is None,
            row["start_year"] or 9999,
            row["id"],
        ))
        representative = members[0]
        status_values = {row["status"] for row in members}
        if "Watching" in status_values:
            status = "Watching"
        elif status_values and status_values == {"Completed"}:
            status = "Completed"
        else:
            status = "Planning"

        group = dict(representative)
        group["status"] = status
        group["_series_count"] = len(members)
        group["_series_members"] = members
        group["_series_episode_total"] = sum(int(row["episodes"] or 0) for row in members)
        group["_series_progress"] = sum(int(row["progress_episodes"] or 0) for row in members)
        group["_bundle_summary"] = _bundle_summary(members)
        result.append(group)

    return result
