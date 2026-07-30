"""
Assembles a Resume object out of the raw data returned by GitHubClient.

Design notes
------------
- Pinned repos are treated as "projects" (that's what the user curated
  for their profile README/homepage — the closest GitHub concept to
  "projects I want to show off").
- If a user has no pinned repos (new account, or pins not set), we
  fall back to their top repos by stars so the resume never comes up
  empty.
- Language stats are pulled from a capped number of repos (default 8)
  to keep API usage reasonable — this is a resume, not a full audit.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .github_client import GitHubClient, Repo
from .skills import build_skill_set


@dataclass
class Project:
    name: str
    description: str | None
    url: str
    language: str | None
    stars: int
    forks: int
    topics: list[str]


@dataclass
class Resume:
    username: str
    name: str | None
    bio: str | None
    location: str | None
    email: str | None
    blog: str | None
    company: str | None
    followers: int
    following: int
    public_repos: int
    profile_url: str
    avatar_url: str
    joined_year: str
    languages: list[str] = field(default_factory=list)
    tools_and_topics: list[str] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    used_fallback_projects: bool = False


class ResumeBuilder:
    def __init__(self, client: GitHubClient, language_sample_size: int = 8):
        self.client = client
        self.language_sample_size = language_sample_size

    def build(self, username: str) -> Resume:
        user = self.client.get_user(username)
        all_repos = self.client.get_public_repos(username)
        non_forks = [r for r in all_repos if not r.get("fork")]

        pinned = self.client.get_pinned_repos(username)
        used_fallback = False
        if pinned:
            project_repos = pinned
        else:
            used_fallback = True
            top_by_stars = sorted(
                non_forks, key=lambda r: r.get("stargazers_count", 0), reverse=True
            )[:6]
            project_repos = [
                Repo(
                    name=r["name"],
                    description=r.get("description"),
                    url=r["html_url"],
                    language=r.get("language"),
                    stars=r.get("stargazers_count", 0),
                    forks=r.get("forks_count", 0),
                    topics=r.get("topics", []) or [],
                )
                for r in top_by_stars
            ]

        language_bytes = self._aggregate_languages(username, non_forks)
        skills = build_skill_set(language_bytes, project_repos)

        return Resume(
            username=username,
            name=user.get("name"),
            bio=user.get("bio"),
            location=user.get("location"),
            email=user.get("email"),
            blog=user.get("blog") or None,
            company=user.get("company"),
            followers=user.get("followers", 0),
            following=user.get("following", 0),
            public_repos=user.get("public_repos", 0),
            profile_url=user.get("html_url", f"https://github.com/{username}"),
            avatar_url=user.get("avatar_url", ""),
            joined_year=(user.get("created_at") or "????")[:4],
            languages=skills["languages"],
            tools_and_topics=skills["tools_and_topics"],
            projects=[
                Project(
                    name=r.name,
                    description=r.description,
                    url=r.url,
                    language=r.language,
                    stars=r.stars,
                    forks=r.forks,
                    topics=r.topics,
                )
                for r in project_repos
            ],
            used_fallback_projects=used_fallback,
        )

    def _aggregate_languages(self, username: str, repos: list[dict]) -> dict[str, int]:
        """Sum language byte-counts across the N most recently updated repos."""
        totals: dict[str, int] = {}
        sample = repos[: self.language_sample_size]
        for r in sample:
            lang_bytes = self.client.get_repo_languages(username, r["name"])
            for lang, count in lang_bytes.items():
                totals[lang] = totals.get(lang, 0) + count
        return totals
