from typing import Any

from arcade_github.tools.constants import ENDPOINTS, GITHUB_API_BASE_URL


def get_github_json_headers(token: str | None) -> dict:
    """
    Generate common headers for GitHub API requests.

    :param token: The authorization token
    :return: A dictionary of headers
    """
    token = token or ""
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_github_diff_headers(token: str | None) -> dict:
    """
    Generate headers for GitHub API requests for diff content.

    :param token: The authorization token
    :return: A dictionary of headers
    """
    token = token or ""
    return {
        "Accept": "application/vnd.github.diff",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def remove_none_values(params: dict) -> dict:
    """
    Remove None values from a dictionary.

    :param params: The dictionary to clean
    :return: A new dictionary with None values removed
    """
    return {k: v for k, v in params.items() if v is not None}


def get_url(endpoint: str, **kwargs: Any) -> str:
    """
    Get the full URL for a given endpoint.

    :param endpoint: The endpoint key from ENDPOINTS
    :param kwargs: The parameters to format the URL with
    :return: The full URL
    """
    return f"{GITHUB_API_BASE_URL}{ENDPOINTS[endpoint].format(**kwargs)}"
