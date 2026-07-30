"""
A drop-in stand-in for GitHubClient that serves fixture data instead of
hitting the network. Lets anyone try the CLI's output/formatting with
`--demo`, with no token and no internet connection required.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .github_client import Repo

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "demo_data.json"


class DemoGitHubClient:
    def __init__(self, *_args, **_kwargs):
        with open(FIXTURE_PATH, encoding="utf-8") as f:
            self._data = json.load(f)

    def get_user(self, username: str) -> dict[str, Any]:
        return self._data["user"]

    def get_public_repos(self, username: str) -> list[dict[str, Any]]:
        return self._data["repos"]

    def get_repo_languages(self, owner: str, repo: str) -> dict[str, int]:
        return self._data["languages"].get(repo, {})

    def get_pinned_repos(self, username: str) -> list[Repo]:
        return [Repo(**r) for r in self._data["pinned"]]
