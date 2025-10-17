import json
from typing import Annotated

import httpx
from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import GitHub

from arcade_github.tools.models import IssueSortProperty, IssueState, SortDirection
from arcade_github.tools.utils import (
    get_github_json_headers,
    get_url,
    remove_none_values,
)


# Implements https://docs.github.com/en/rest/issues/issues?apiVersion=2022-11-28#create-an-issue
# Example `arcade chat` usage:
#   "create an issue in the <REPO> repo owned by <OWNER> titled
#   'Found a bug' with the body 'I'm having a problem with this.'
#   Assign it to <USER> and label it 'bug'"
@tool(requires_auth=GitHub())
async def create_issue(
    context: ToolContext,
    owner: Annotated[str, "The account owner of the repository. The name is not case sensitive."],
    repo: Annotated[
        str,
        "The name of the repository without the .git extension. The name is not case sensitive.",
    ],
    title: Annotated[str, "The title of the issue."],
    body: Annotated[str | None, "The contents of the issue."] = None,
    assignees: Annotated[list[str] | None, "Logins for Users to assign to this issue."] = None,
    milestone: Annotated[
        int | None, "The number of the milestone to associate this issue with."
    ] = None,
    labels: Annotated[list[str] | None, "Labels to associate with this issue."] = None,
    include_extra_data: Annotated[
        bool,
        "If true, return all the data available about the pull requests. "
        "This is a large payload and may impact performance - use with caution.",
    ] = False,
) -> Annotated[
    str,
    "A JSON string containing the created issue's details, including id, url, title, body, state, "
    "html_url, creation and update timestamps, user, assignees, and labels. "
    "If include_extra_data is True, returns all available data about the issue.",
]:
    """
    Create an issue in a GitHub repository.

    Example:
    ```
    create_issue(
        owner="octocat",
        repo="Hello-World",
        title="Found a bug",
        body="I'm having a problem with this.",
        assignees=["octocat"],
        milestone=1,
        labels=["bug"],
    )
    ```
    """
    url = get_url("repo_issues", owner=owner, repo=repo)
    data = {
        "title": title,
        "body": body,
        "labels": labels,
        "milestone": milestone,
        "assignees": assignees,
    }
    data = remove_none_values(data)
    headers = get_github_json_headers(
        context.authorization.token if context.authorization and context.authorization.token else ""
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)

    response.raise_for_status()

    issue_data = response.json()
    if include_extra_data:
        return json.dumps(issue_data)

    important_info = {
        "id": issue_data.get("id"),
        "url": issue_data.get("url"),
        "title": issue_data.get("title"),
        "body": issue_data.get("body"),
        "state": issue_data.get("state"),
        "html_url": issue_data.get("html_url"),
        "created_at": issue_data.get("created_at"),
        "updated_at": issue_data.get("updated_at"),
        "user": issue_data.get("user", {}).get("login"),
        "assignees": [assignee.get("login") for assignee in issue_data.get("assignees", [])],
        "labels": [label.get("name") for label in issue_data.get("labels", [])],
    }
    return json.dumps(important_info)


# Implements https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#create-an-issue-comment
# Example `arcade chat` usage:
#   "create a comment in the vscode repo owned by microsoft for issue 1347 that says 'Me too'"
@tool(requires_auth=GitHub())
async def create_issue_comment(
    context: ToolContext,
    owner: Annotated[str, "The account owner of the repository. The name is not case sensitive."],
    repo: Annotated[
        str,
        "The name of the repository without the .git extension. The name is not case sensitive.",
    ],
    issue_number: Annotated[int, "The number that identifies the issue."],
    body: Annotated[str, "The contents of the comment."],
    include_extra_data: Annotated[
        bool,
        "If true, return all the data available about the pull requests. "
        "This is a large payload and may impact performance - use with caution.",
    ] = False,
) -> Annotated[
    str,
    "A JSON string containing the created comment's details, including id, url, body, user, "
    "and creation and update timestamps. If include_extra_data is True, returns all available "
    "data about the comment.",
]:
    """
    Create a comment on an issue in a GitHub repository.

    Example:
    ```
    create_issue_comment(owner="octocat", repo="Hello-World", issue_number=1347, body="Me too")
    ```
    """
    url = get_url("repo_issue_comments", owner=owner, repo=repo, issue_number=issue_number)
    data = {
        "body": body,
    }
    headers = get_github_json_headers(
        context.authorization.token if context.authorization and context.authorization.token else ""
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)

    response.raise_for_status()

    comment_data = response.json()
    if include_extra_data:
        return json.dumps(comment_data)

    important_info = {
        "id": comment_data.get("id"),
        "url": comment_data.get("url"),
        "body": comment_data.get("body"),
        "user": comment_data.get("user", {}).get("login"),
        "created_at": comment_data.get("created_at"),
        "updated_at": comment_data.get("updated_at"),
    }
    return json.dumps(important_info)


# Implements https://docs.github.com/en/rest/issues/issues?apiVersion=2022-11-28#list-repository-issues
# Example `arcade chat` usage:
#   "list issues in the <REPO> repo owned by <OWNER>"
@tool(requires_auth=GitHub())
async def list_issues(
    context: ToolContext,
    owner: Annotated[str, "The account owner of the repository. The name is not case sensitive."],
    repo: Annotated[
        str,
        "The name of the repository without the .git extension. The name is not case sensitive.",
    ],
    state: Annotated[
        IssueState | None,
        "Indicates the state of the issues to return. Can be either open, closed, or all. "
        "Default: open",
    ] = IssueState.OPEN,
    labels: Annotated[
        str | None,
        "A list of comma separated label names. Example: bug,ui,@high",
    ] = None,
    sort: Annotated[
        IssueSortProperty | None,
        "What to sort results by. Can be either created, updated, or comments. Default: created",
    ] = IssueSortProperty.CREATED,
    direction: Annotated[
        SortDirection | None,
        "The direction to sort the results by. Can be either asc or desc. Default: desc",
    ] = SortDirection.DESC,
    since: Annotated[
        str | None,
        "Only show notifications updated after the given time. "
        "This is a timestamp in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ.",
    ] = None,
    per_page: Annotated[
        int | None,
        "The number of results per page (max 100). Default: 30",
    ] = 30,
    page: Annotated[
        int | None,
        "Page number of the results to fetch. Default: 1",
    ] = 1,
    include_extra_data: Annotated[
        bool,
        "If true, return all the data available about the issues. "
        "This is a large payload and may impact performance - use with caution.",
    ] = False,
) -> Annotated[
    str,
    "A JSON string containing a list of issues with their details, including id, url, title, body, "
    "state, html_url, creation and update timestamps, user, assignees, and labels. "
    "If include_extra_data is True, returns all available data about each issue.",
]:
    """
    List issues in a GitHub repository.

    Example:
    ```
    list_issues(owner="octocat", repo="Hello-World", state="open")
    ```
    """
    url = get_url("repo_issues", owner=owner, repo=repo)
    params = {
        "state": state.value if state else None,
        "labels": labels,
        "sort": sort.value if sort else None,
        "direction": direction.value if direction else None,
        "since": since,
        "per_page": per_page,
        "page": page,
    }
    params = remove_none_values(params)
    headers = get_github_json_headers(
        context.authorization.token if context.authorization and context.authorization.token else ""
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)

    response.raise_for_status()

    issues_data = response.json()
    if include_extra_data:
        return json.dumps(issues_data)

    response_data = []
    for issue in issues_data:
        response_data.append({
            "id": issue.get("id"),
            "number": issue.get("number"),
            "url": issue.get("url"),
            "title": issue.get("title"),
            "body": issue.get("body"),
            "state": issue.get("state"),
            "html_url": issue.get("html_url"),
            "created_at": issue.get("created_at"),
            "updated_at": issue.get("updated_at"),
            "user": issue.get("user", {}).get("login"),
            "assignees": [assignee.get("login") for assignee in issue.get("assignees", [])],
            "labels": [label.get("name") for label in issue.get("labels", [])],
        })
    return json.dumps(response_data)


# Implements https://docs.github.com/en/rest/issues/issues?apiVersion=2022-11-28#get-an-issue
# Example `arcade chat` usage:
#   "get issue #1347 from the <REPO> repo owned by <OWNER>"
@tool(requires_auth=GitHub())
async def get_issue(
    context: ToolContext,
    owner: Annotated[str, "The account owner of the repository. The name is not case sensitive."],
    repo: Annotated[
        str,
        "The name of the repository without the .git extension. The name is not case sensitive.",
    ],
    issue_number: Annotated[int, "The number that identifies the issue."],
    include_extra_data: Annotated[
        bool,
        "If true, return all the data available about the issue. "
        "This is a large payload and may impact performance - use with caution.",
    ] = False,
) -> Annotated[
    str,
    "A JSON string containing the issue's details, including id, url, title, body, state, "
    "html_url, creation and update timestamps, user, assignees, and labels. "
    "If include_extra_data is True, returns all available data about the issue.",
]:
    """
    Get a specific issue from a GitHub repository.

    Example:
    ```
    get_issue(owner="octocat", repo="Hello-World", issue_number=1347)
    ```
    """
    url = get_url("repo_issue", owner=owner, repo=repo, issue_number=issue_number)
    headers = get_github_json_headers(
        context.authorization.token if context.authorization and context.authorization.token else ""
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    response.raise_for_status()

    issue_data = response.json()
    if include_extra_data:
        return json.dumps(issue_data)

    important_info = {
        "id": issue_data.get("id"),
        "number": issue_data.get("number"),
        "url": issue_data.get("url"),
        "title": issue_data.get("title"),
        "body": issue_data.get("body"),
        "state": issue_data.get("state"),
        "html_url": issue_data.get("html_url"),
        "created_at": issue_data.get("created_at"),
        "updated_at": issue_data.get("updated_at"),
        "user": issue_data.get("user", {}).get("login"),
        "assignees": [assignee.get("login") for assignee in issue_data.get("assignees", [])],
        "labels": [label.get("name") for label in issue_data.get("labels", [])],
    }
    return json.dumps(important_info)
