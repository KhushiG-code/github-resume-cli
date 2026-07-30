"""
Turns raw repository data into a ranked skills list.

Two signals are combined:
  1. Language bytes-of-code across the user's repos (weighted, so a
     10,000-line repo counts more than a 50-line one).
  2. Repository topics (tags the user themselves attached), which
     often name frameworks/tools that never show up as a "language"
     (e.g. "docker", "react", "postgresql").
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from .github_client import Repo


def rank_languages(language_bytes: dict[str, int], top_n: int = 8) -> list[str]:
    ranked = sorted(language_bytes.items(), key=lambda kv: kv[1], reverse=True)
    return [lang for lang, _ in ranked[:top_n]]


def rank_topics(repos: Iterable[Repo], top_n: int = 12) -> list[str]:
    counter: Counter[str] = Counter()
    for repo in repos:
        counter.update(repo.topics)
    return [topic for topic, _ in counter.most_common(top_n)]


def build_skill_set(language_bytes: dict[str, int], repos: Iterable[Repo]) -> dict[str, list[str]]:
    """Returns {"languages": [...], "tools_and_topics": [...]}."""
    return {
        "languages": rank_languages(language_bytes),
        "tools_and_topics": rank_topics(repos),
    }
