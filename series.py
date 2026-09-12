from collections import defaultdict
import re

from api import get_media_details
from database import get_all_library, get_connection, save_anime

SERIES_RELATIONS = {"PREQUEL", "SEQUEL", "PARENT", "SIDE_STORY", "SUMMARY", "FULL_STORY"}


def _series_key(title):
    value = (title or "").lower().strip()
    value = re.sub(r"\s*[:\-–—]?\s*(the\s+)?final\s+season(?:\s+part\s+\d+)?\s*$", "", value)
    value = re.sub(r"\s*[:\-–—]?\s*(?:season|series)\s*(?:\d+|[ivx]+)(?:\s+part\s+\d+)?\s*$", "", value)
    value = re.sub(r"\s*[:\-–—]?\s*(?:part|cour)\s*\d+\s*$", "", value)
    value = re.sub(r"\s+(?:ii|iii|iv|v|vi|2nd|3rd|4th|5th)\s*(?:season)?\s*$", "", value)
    value = re.sub(r"\s+\d+$", "", value)
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def _bundle_summary(members):
    counts = defaultdict(int)
    for member in members:
        fmt = str(member.get("format") or "").upper() if hasattr(member, "get") else str(member["format"] or "").upper()
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


def _search_relation_getter(item):
    result = []
    for edge in (item.get("relations") or {}).get("edges", []):
        target_id = (edge.get("node") or {}).get("id")
        if target_id:
            result.append((edge.get("relationType"), int(target_id)))
    return result


def group_media_results(results):
    """Group search results only when AniList explicitly relates them."""
    if not results:
        return []

    ids = {int(item["id"]) for item in results}
    parent = {item_id: item_id for item_id in ids}

    def find(item_id):
        while parent[item_id] != item_id:
            parent[item_id] = parent[parent[item_id]]
            item_id = parent[item_id]
        return item_id

    def union(left, right):
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for item in results:
        for relation_type, target_id in _search_relation_getter(item):
            if relation_type in SERIES_RELATIONS and target_id in ids:
                union(int(item["id"]), target_id)

    groups = defaultdict(list)
    for item in results:
        groups[find(int(item["id"]))].append(item)

    grouped = []
    for members in groups.values():
        members.sort(key=lambda item: (
            (item.get("startDate") or {}).get("year") is None,
            (item.get("startDate") or {}).get("year") or 9999,
            int(item["id"]),
        ))
        representative = dict(members[0])
        representative["_series_count"] = len(members)
        representative["_series_members"] = members
        representative["_bundle_summary"] = _bundle_summary(members)
        grouped.append(representative)
    return grouped


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


def sync_library_relations():
    """Fill missing relation data for current library entries.

    Network work is deliberately isolated here so Library rendering never blocks
    application startup or normal local browsing.
    """
    rows = list(get_all_library())
    if len(rows) < 2:
        return False

    ids = {int(row["id"]) for row in rows}
    existing = {int(row["source_id"]) for row in _relation_data_for(ids)} | {
        int(row["target_id"]) for row in _relation_data_for(ids)
    }

    changed = False
    for work_id in ids - existing:
        try:
            details = get_media_details(work_id)
            if details:
                save_anime(details)
                changed = True
        except Exception:
            continue
    return changed


def get_library_series():
    """Return library works grouped locally using cached relationships."""
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
        members.sort(key=lambda row: (row["start_year"] is None, row["start_year"] or 9999, row["id"]))
        group = dict(members[0])
        status_values = {row["status"] for row in members}
        if "Watching" in status_values:
            group["status"] = "Watching"
        elif status_values and status_values == {"Completed"}:
            group["status"] = "Completed"
        else:
            group["status"] = "Planning"
        group["_series_count"] = len(members)
        group["_series_members"] = members
        group["_series_episode_total"] = sum(int(row["episodes"] or 0) for row in members)
        group["_series_progress"] = sum(int(row["progress_episodes"] or 0) for row in members)
        group["_bundle_summary"] = _bundle_summary(members)
        result.append(group)
    return result
