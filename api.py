import requests
import time


ANILIST_URL = "https://graphql.anilist.co"

MAX_RETRIES = 3
RETRY_DELAY = 1


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
                }
                role
                voiceActors {
                    id
                    name { full }
                    language
                    image { large }
                }
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


def search_anime(search, page=1, per_page=20, media_type="ANIME", media_format=None):
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
    return data["Page"]


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
