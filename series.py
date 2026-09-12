from collections import defaultdict
import re

from api import get_media_details
from database import get_all_library, get_connection, save_anime

SEASON_RELATIONS = {"PREQUEL", "SEQUEL"}

# Avoid repeatedly asking AniList about the same title during one app session.
_relation_hydrated_ids = set()


def _series_key(title):
    """Conservative title normalization for seasons when relation data is unavailable."""
    value = (title or "").lower().strip()
    value = re.sub(r"\s*[:\-–—]?\s*(the\s+)?final\s+season(?:\s+part\s+\d+)?\s*$", "", value)
    value = re.sub(r"\s*[:\-–—]?\s*(?:season|series)\s*(?:\d+|[ivx]+)(?:\s+part\s+\d+)?\s*$", "", value)
    value = re.sub(r"\s*[:\-–—]?\s*(?:part|cour)\s*\d+\s*$", "", value)
    value = re.sub(r"\s+(?:ii|iii|iv|v|vi|2nd|3rd|4th|5th)\s*(?:season)?\s*$", "", value)
    value = re.sub(r"\s+\d+$", "", value)
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def _relation_data_for(ids):
    if not ids:
        return set(), []

    placeholders = ",".join("?" for _ in ids)
    connection = get_connection()
    rows = connection.execute(
        f"""
        SELECT source_id, target_id, relation_type
        FROM work_relations
        WHERE relation_type IN ('PREQUEL', 'SEQUEL')
          AND (source_id IN ({placeholders}) OR target_id IN ({placeholders}))
        """,
        [*ids, *ids],
    ).fetchall()
    connection.close()

    connected = set()
    for row in rows:
        connected.add(int(row["source_id"]))
        connected.add(int(row["target_id"]))
    return connected, rows


def _hydrate_missing_relations(rows):
    """Fetch full AniList data for existing library entries whose relations were never saved."""
    ids = {int(row["id"]) for row in rows}
    connected, _ = _relation_data_for(ids)
    missing = ids - connected - _relation_hydrated_ids

    for work_id in missing:
        try:
            details = get_media_details(work_id)
            if details:
                save_anime(details)
                _relation_hydrated_ids.add(work_id)
        except Exception:
            # A temporary AniList/network failure should not prevent the library from opening.
            continue


def get_library_series():
    """Return library works grouped into connected sequel/prequel seasons."""
    rows = list(get_all_library())
    if not rows:
        return []

    # Older entries were often saved from lightweight search results, which do not
    # contain the relation graph. Repair those entries automatically so existing
    # libraries do not need to be deleted and re-added.
    if len(rows) > 1:
        _hydrate_missing_relations(rows)
        rows = list(get_all_library())

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

    _, relations = _relation_data_for(ids)
    for relation in relations:
        source_id = int(relation["source_id"])
        target_id = int(relation["target_id"])
        if source_id in ids and target_id in ids:
            union(source_id, target_id)

    # Also merge obvious season-title variants. This covers older entries that
    # may still have no usable relation data after a failed network request.
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
        result.append(group)

    return result
