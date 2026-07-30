"""
Thin wrapper around the GitHub REST and GraphQL APIs.

Only the calls needed for the resume are implemented:
  - user profile          (REST  /users/{username})
  - public repositories    (REST  /users/{username}/repos)
  - per-repo language stats(REST  /repos/{owner}/{repo}/languages)
  - pinned repositories    (GraphQL, REST has no endpoint for this)

A GitHub personal access token is required for the GraphQL call
(pinned repos are not exposed anywhere in REST). A token also raises
the REST rate limit from 60 to 5000 requests/hour, so it's used for
every call when available.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

import requests

REST_ROOT = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"

PINNED_QUERY = """
query PinnedItems($login: String!) {
  user(login: $login) {
    pinnedItems(first: 6, types: [REPOSITORY]) {
      nodes {
        ... on Repository {
          name
          description
          url
          isFork
          stargazerCount
          forkCount
          primaryLanguage { name }
          repositoryTopics(first: 10) {
            nodes { topic { name } }
          }
        }
      }
    }
  }
}
"""


class GitHubAPIError(Exception):
    """Raised for any non-recoverable GitHub API failure."""


@dataclass
class Repo:
    name: str
    description: str | None
    url: str
    language: str | None
    stars: int
    forks: int
    topics: list[str]
    is_fork: bool = False


class GitHubClient:
    def __init__(self, token: str | None = None, timeout: int = 15):
        self.token = token
        self.timeout = timeout
        self.session = requests.Session()
        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.session.headers.update(headers)

    # ------------------------------------------------------------------ #
    # REST calls
    # ------------------------------------------------------------------ #
    def get_user(self, username: str) -> dict[str, Any]:
        resp = self.session.get(f"{REST_ROOT}/users/{username}", timeout=self.timeout)
        if resp.status_code == 404:
            raise GitHubAPIError(f"GitHub user '{username}' was not found.")
        self._raise_for_rate_limit(resp)
        resp.raise_for_status()
        return resp.json()

    def get_public_repos(self, username: str, per_page: int = 100) -> list[dict[str, Any]]:
        resp = self.session.get(
            f"{REST_ROOT}/users/{username}/repos",
            params={"sort": "updated", "per_page": per_page, "type": "owner"},
            timeout=self.timeout,
        )
        self._raise_for_rate_limit(resp)
        resp.raise_for_status()
        return resp.json()

    def get_repo_languages(self, owner: str, repo: str) -> dict[str, int]:
        """Returns {language: bytes_of_code}."""
        resp = self.session.get(
            f"{REST_ROOT}/repos/{owner}/{repo}/languages", timeout=self.timeout
        )
        if resp.status_code != 200:
            return {}
        return resp.json()

    # ------------------------------------------------------------------ #
    # GraphQL call (pinned repos)
    # ------------------------------------------------------------------ #
    def get_pinned_repos(self, username: str) -> list[Repo]:
        if not self.token:
            # Pinned repos require an authenticated GraphQL call.
            return []

        resp = self.session.post(
            GRAPHQL_URL,
            json={"query": PINNED_QUERY, "variables": {"login": username}},
            timeout=self.timeout,
        )
        self._raise_for_rate_limit(resp)
        resp.raise_for_status()
        payload = resp.json()

        if "errors" in payload:
            msg = "; ".join(e.get("message", "unknown error") for e in payload["errors"])
            raise GitHubAPIError(f"GitHub GraphQL error: {msg}")

        user = payload.get("data", {}).get("user")
        if not user:
            return []

        nodes = user["pinnedItems"]["nodes"]
        repos = []
        for n in nodes:
            topics = [t["topic"]["name"] for t in n["repositoryTopics"]["nodes"]]
            repos.append(
                Repo(
                    name=n["name"],
                    description=n["description"],
                    url=n["url"],
                    language=(n["primaryLanguage"] or {}).get("name"),
                    stars=n["stargazerCount"],
                    forks=n["forkCount"],
                    topics=topics,
                    is_fork=n["isFork"],
                )
            )
        return repos

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _raise_for_rate_limit(resp: requests.Response) -> None:
        if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
            raise GitHubAPIError(
                "GitHub API rate limit exceeded. Set GITHUB_TOKEN to raise the "
                "limit from 60 to 5000 requests/hour."
            )
        if resp.status_code == 401:
            raise GitHubAPIError("GitHub rejected the token. Check GITHUB_TOKEN and try again.")
