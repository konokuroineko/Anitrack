from collections import defaultdict

from database import get_all_library, get_connection


SEASON_RELATIONS = {"PREQUEL", "SEQUEL"}


def get_library_series():
    """Return library works grouped into connected sequel/prequel series."""
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

    connection = get_connection()
    relations = connection.execute(
        """
        SELECT source_id, target_id
        FROM work_relations
        WHERE relation_type IN ('PREQUEL', 'SEQUEL')
        """
    ).fetchall()
    connection.close()

    for relation in relations:
        source_id, target_id = int(relation["source_id"]), int(relation["target_id"])
        if source_id in ids and target_id in ids:
            union(source_id, target_id)

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
