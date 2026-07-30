import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gh_resume.github_client import Repo
from gh_resume.skills import build_skill_set, rank_languages, rank_topics


def test_rank_languages_orders_by_bytes_desc():
    langs = {"Python": 500, "JavaScript": 5000, "HTML": 100}
    assert rank_languages(langs) == ["JavaScript", "Python", "HTML"]


def test_rank_languages_caps_at_top_n():
    langs = {f"Lang{i}": i for i in range(20)}
    assert len(rank_languages(langs, top_n=5)) == 5


def test_rank_topics_counts_frequency_across_repos():
    repos = [
        Repo("a", None, "u", "Python", 0, 0, ["cli", "api"]),
        Repo("b", None, "u", "Python", 0, 0, ["api", "docker"]),
    ]
    ranked = rank_topics(repos, top_n=3)
    assert ranked[0] == "api"  # appears in both repos -> highest frequency
    assert set(ranked) == {"api", "cli", "docker"}


def test_build_skill_set_combines_languages_and_topics():
    langs = {"Go": 1000}
    repos = [Repo("a", None, "u", "Go", 0, 0, ["kubernetes"])]
    result = build_skill_set(langs, repos)
    assert result["languages"] == ["Go"]
    assert result["tools_and_topics"] == ["kubernetes"]


def test_empty_inputs_return_empty_lists():
    result = build_skill_set({}, [])
    assert result == {"languages": [], "tools_and_topics": []}
