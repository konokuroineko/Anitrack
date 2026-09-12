import re
from collections import defaultdict
import requests
import time


ANILIST_URL = "https://graphql.anilist.co"

MAX_RETRIES = 3
RETRY_DELAY = 1
SERIES_RELATIONS = {"PREQUEL", "SEQUEL", "PARENT", "SIDE_STORY", "SUMMARY", "FULL_STORY"}


def anilist_request(query, variables=None):
    """Make a request to AniList GraphQL API with retry logic."""
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                ANILIST_URL,
                json={"query": query, "variables": variables or {}},
                timeout=30,
            )
            data = response.json()

            if response.status_code >= 400:
                errors = data.get("errors") or []
                message = errors[0].get("message") if errors else response.reason
                raise Exception(f"AniList request failed ({response.status_code}): {message}")

            if "errors" in data:
                raise Exception(data["errors"][0]["message"])

            return data["data"]

        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ChunkedEncodingError,
        ) as error:
            last_error = error
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_DELAY * (2 ** attempt)
                print(f"Network error (attempt {attempt + 1}/{MAX_RETRIES}): {error}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"Failed after {MAX_RETRIES} attempts: {error}")
        except requests.exceptions.RequestException as error:
            raise error

    raise Exception(
        f"Network error after {MAX_RETRIES} attempts. Please check your internet connection and try again. "
        f"(Last error: {str(last_error)[:100]})"
    )


def _media_fields(include_details=False):
    """Return GraphQL fields shared by search and detail queries."""
    base = """
        id
        type
        title { romaji english native }
        episodes
        averageScore
        startDate { year month day }
        coverImage { large }
        format
    """
    if not include_details:
        return base + """
        relations {
            edges {
                relationType
                node {
                    id
                    type
                    format
                    title { romaji english native }
                    coverImage { large }
                }
            }
        }
        """

    return base + """
        description
        status
        endDate { year month day }
        synonyms
        chapters
        volumes
        source
        duration
        studios {
            edges {
                isMain
                node { id name }
            }
        }
        characters(perPage: 10, sort: ROLE) {
            edges {
                node {
                    id
                    name { full }
                    image { large }
                    voiceActors(perPage: 10) {
                        id
                        name { full }
                        languageV2
                        image { large }
                    }
                }
                role
            }
        }
        staff(perPage: 15) {
            edges {
                role
                node {
                    id
                    name { full }
                    image { large }
                }
            }
        }
        relations {
            edges {
                relationType
                node {
                    id
                    type
                    format
                    title { romaji english native }
                    coverImage { large }
                }
            }
        }
    """


def _season_key(title):
    value = (title or "").lower().strip()
    value = re.sub(r"\s*[:\-–—]?\s*(the\s+)?final\s+season(?:\s+part\s+\d+)?\s*$", "", value)
    value = re.sub(r"\s*[:\-–—]?\s*(?:season|series)\s*(?:\d+|[ivx]+)(?:\s+part\s+\d+)?\s*$", "", value)
    value = re.sub(r"\s*[:\-–—]?\s*(?:part|cour)\s*\d+\s*$", "", value)
    value = re.sub(r"\s+(?:ii|iii|iv|v|vi|2nd|3rd|4th|5th)\s*(?:season)?\s*$", "", value)
    value = re.sub(r"\s+\d+$", "", value)
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def _group_search_results(results):
    """Collapse related seasons and OVAs into a single media result."""
    if not results:
        return results

    ids = {int(work["id"]) for work in results}
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

    for work in results:
        for edge in (work.get("relations") or {}).get("edges", []):
            if edge.get("relationType") not in SERIES_RELATIONS:
                continue
            target = edge.get("node") or {}
            target_id = target.get("id")
            if target_id in ids:
                union(int(work["id"]), int(target_id))

    # Catch straightforward season-title variants even when AniList did not return
    # their relation edge in the same search page.
    by_title = {}
    for work in results:
        title = work.get("title") or {}
        text = title.get("english") or title.get("romaji") or title.get("native") or ""
        key = _season_key(text)
        if key:
            if key in by_title:
                union(int(work["id"]), by_title[key])
            else:
                by_title[key] = int(work["id"])

    groups = defaultdict(list)
    for work in results:
        groups[find(int(work["id"]))].append(work)

    grouped = []
    for members in groups.values():
        members.sort(key=lambda work: (
            (work.get("startDate") or {}).get("year") is None,
            (work.get("startDate") or {}).get("year") or 9999,
            int(work["id"]),
        ))
        representative = dict(members[0])
        representative["_series_count"] = len(members)
        representative["_series_members"] = members
        grouped.append(representative)

    return grouped


def search_anime(search, page=1, per_page=50, media_type="ANIME", media_format=None):
    """Search AniList for anime, manga, or novel media."""
    if media_type not in {"ANIME", "MANGA"}:
        raise ValueError("media_type must be ANIME or MANGA")

    if media_type == "ANIME":
        query = """
        query ($search: String, $page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    currentPage
                    lastPage
                    hasNextPage
                }
                media(search: $search, type: ANIME) {
                    %s
                }
            }
        }
        """ % _media_fields(include_details=False)
        variables = {
            "search": search,
            "page": page,
            "perPage": per_page,
        }
    else:
        if media_format not in {None, "MANGA", "NOVEL", "ONE_SHOT"}:
            raise ValueError("Invalid manga media_format")

        query = """
        query ($search: String, $page: Int, $perPage: Int, $format: MediaFormat) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    currentPage
                    lastPage
                    hasNextPage
                }
                media(search: $search, type: MANGA, format: $format) {
                    %s
                }
            }
        }
        """ % _media_fields(include_details=False)
        variables = {
            "search": search,
            "page": page,
            "perPage": per_page,
            "format": media_format,
        }

    data = anilist_request(query, variables)
    page_data = data["Page"]
    page_data["media"] = _group_search_results(page_data["media"])
    return page_data


def get_media_details(media_id):
    """Fetch the complete media record needed by detail/import workflows."""
    query = """
    query ($id: Int) {
        Media(id: $id) {
            %s
            airingSchedule(perPage: 50) {
                nodes {
                    airingAt
                    episode
                }
            }
        }
    }
    """ % _media_fields(include_details=True)
    data = anilist_request(query, {"id": media_id})
    return data["Media"]
