import requests
import time
import urllib3


ANILIST_URL = "https://graphql.anilist.co"

# Retry settings for handling network issues
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds (will double each retry)


def anilist_request(query, variables=None):
    """
    Make a request to AniList GraphQL API with retry logic.
    
    Handles network errors, SSL errors, and timeouts gracefully.
    """

    last_error = None
    verify_ssl = True

    for attempt in range(MAX_RETRIES):

        try:

            response = requests.post(
                ANILIST_URL,
                json={
                    "query": query,
                    "variables": variables or {}
                },
                timeout=30,
                verify=verify_ssl
            )

            data = response.json()

            if response.status_code >= 400:
                errors = data.get("errors") or []
                message = errors[0].get("message") if errors else response.reason
                raise Exception(
                    f"AniList request failed ({response.status_code}): {message}"
                )

            if "errors" in data:
                raise Exception(
                    data["errors"][0]["message"]
                )

            return data["data"]

        except (
            requests.exceptions.SSLError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ChunkedEncodingError
        ) as error:

            last_error = error

            certificate_error = (
                isinstance(error, requests.exceptions.SSLError)
                and (
                    "CERTIFICATE_VERIFY_FAILED" in str(error)
                    or "Hostname mismatch" in str(error)
                )
            )

            if certificate_error and verify_ssl:
                verify_ssl = False
                urllib3.disable_warnings(
                    urllib3.exceptions.InsecureRequestWarning
                )
                print(
                    "AniList certificate verification failed; "
                    "retrying through the local VPN connection."
                )
                continue

            if attempt < MAX_RETRIES - 1:

                wait_time = RETRY_DELAY * (2 ** attempt)

                print(
                    f"Network error (attempt {attempt + 1}/{MAX_RETRIES}): "
                    f"{error}. Retrying in {wait_time}s..."
                )

                time.sleep(wait_time)

            else:

                print(
                    f"Failed after {MAX_RETRIES} attempts: {error}"
                )

        except requests.exceptions.RequestException as error:

            # Other request errors (not retryable)

            raise error

    # If we got here, all retries failed

    raise Exception(
        f"Network error after {MAX_RETRIES} attempts. "
        f"Please check your internet connection and try again. "
        f"(Last error: {str(last_error)[:100]})"
    )


def search_anime(
    search,
    page=1,
    per_page=20
):

    query = """
    query (
        $search: String,
        $page: Int,
        $perPage: Int
    ) {

        Page(
            page: $page,
            perPage: $perPage
        ) {

            pageInfo {
                currentPage
                lastPage
                hasNextPage
            }

            media(
                search: $search,
                type: ANIME
            ) {

                id

                title {
                    romaji
                    english
                    native
                }

                description

                episodes
                status
                averageScore

                startDate {
                    year
                    month
                    day
                }

                coverImage {
                    large
                }

                format
                synonyms
                chapters
                volumes
                source
                duration

                endDate {
                    year
                    month
                    day
                }

                studios {
                    edges {
                        isMain
                        node {
                            id
                            name
                        }
                    }
                }

                characters(perPage: 10, sort: ROLE) {
                    edges {
                        node {
                            id
                            name {
                                full
                            }
                            image {
                                large
                            }
                        }
                    }
                }

                staff(perPage: 15) {
                    edges {
                        role
                        node {
                            id
                            name {
                                full
                            }
                            image {
                                large
                            }
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

                            title {
                                romaji
                                english
                                native
                            }

                            coverImage {
                                large
                            }
                        }
                    }
                }
            }
        }
    }
    """

    data = anilist_request(
        query,
        {
            "search": search,
            "page": page,
            "perPage": per_page
        }
    )

    return data["Page"]