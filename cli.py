"""
Command-line entry point.

    gh-resume octocat
    gh-resume octocat --token ghp_xxx
    gh-resume --demo
    gh-resume octocat --output resume.md
"""

from __future__ import annotations

import argparse
import os
import sys

from rich.console import Console

from . import __version__
from .display import render
from .export import to_markdown
from .github_client import GitHubAPIError, GitHubClient
from .resume import ResumeBuilder


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gh-resume",
        description="Generate a terminal resume from a GitHub profile.",
    )
    parser.add_argument(
        "username", nargs="?", help="GitHub username to build a resume for"
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub personal access token (or set GITHUB_TOKEN env var). "
        "Required to read pinned repos.",
    )
    parser.add_argument(
        "--output",
        metavar="FILE.md",
        help="Also write the resume to a Markdown file.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run against bundled sample data — no token or network needed.",
    )
    parser.add_argument(
        "--version", action="version", version=f"gh-resume {__version__}"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    console = Console()

    if not args.demo and not args.username:
        parser.error("username is required unless --demo is used")

    if not args.demo and not args.token:
        console.print(
            "[yellow]Warning:[/yellow] no GITHUB_TOKEN set — pinned repositories "
            "can't be fetched (GitHub only exposes them via an authenticated "
            "GraphQL call), and you're limited to 60 unauthenticated requests/hour. "
            "Falling back to top starred repos for the Projects section.\n"
        )

    if args.demo:
        from .demo_client import DemoGitHubClient

        client = DemoGitHubClient()
        username = "octocat"
    else:
        client = GitHubClient(token=args.token)
        username = args.username

    try:
        resume = ResumeBuilder(client).build(username)
    except GitHubAPIError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1
    except Exception as e:  # network errors, etc.
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        return 1

    render(resume, console)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(to_markdown(resume))
        console.print(f"\n[green]Saved Markdown resume to {args.output}[/green]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
