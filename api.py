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
                raise Exception(
                    f"AniList request failed ({response.status_code}): {message}"
                )

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
                print(
                    f"Network error (attempt {attempt + 1}/{MAX_RETRIES}): "
                    f"{error}. Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                print(f"Failed after {MAX_RETRIES} attempts: {error}")
        except requests.exceptions.RequestException as error:
            raise error

    raise Exception(
        f"Network error after {MAX_RETRIES} attempts. "
        f"Please check your internet connection and try again. "
        f"(Last error: {str(last_error)[:100]})"
    )


def _media_fields(include_details=False):
    """Return GraphQL fields shared by search and detail queries."""
    base = """
        id
        type
        title { romaji english native }
        description
        episodes
        status
        averageScore
        startDate { year month day }
        endDate { year month day }
        coverImage { large }
        format
        synonyms
        chapters
        volumes
        source
        duration
    """
    if not include_details:
        return base

    return base + """
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


def search_anime(search, page=1, per_page=20, media_type="ANIME"):
    """Search AniList for anime or manga-based media."""
    if media_type not in {"ANIME", "MANGA"}:
        raise ValueError("media_type must be ANIME or MANGA")

    query = f"""
    query ($search: String, $page: Int, $perPage: Int, $type: MediaType) {{
        Page(page: $page, perPage: $perPage) {{
            pageInfo {{
                currentPage
                lastPage
                hasNextPage
            }}
            media(search: $search, type: $type) {{
                {_media_fields(include_details=False)}
            }}
        }}
    }}
    """

    data = anilist_request(
        query,
        {
            "search": search,
            "page": page,
            "perPage": per_page,
            "type": media_type,
        },
    )
    return data["Page"]


def get_media_details(media_id):
    """Fetch the complete media record needed by detail/import workflows."""
    query = f"""
    query ($id: Int) {{
        Media(id: $id) {{
            {_media_fields(include_details=True)}
            airingSchedule(perPage: 50) {{
                nodes {{
                    airingAt
                    episode
                }}
            }}
        }}
    }}
    """
    data = anilist_request(query, {"id": media_id})
    return data["Media"]
