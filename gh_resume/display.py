"""Renders a Resume object as a clean terminal layout using rich."""

from __future__ import annotations

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .resume import Resume


def render(resume: Resume, console: Console | None = None) -> None:
    console = console or Console()

    console.print(_header_panel(resume))
    console.print()

    if resume.languages:
        console.print(_skills_panel(resume))
        console.print()

    console.print(_projects_panel(resume))
    console.print()

    console.print(_footer(resume))


def _header_panel(r: Resume) -> Panel:
    title = r.name or r.username
    lines = [Text(title, style="bold cyan")]
    lines.append(Text(f"@{r.username}", style="dim"))

    if r.bio:
        lines.append(Text(""))
        lines.append(Text(r.bio, style="italic"))

    meta_bits = []
    if r.location:
        meta_bits.append(f"📍 {r.location}")
    if r.company:
        meta_bits.append(f"🏢 {r.company}")
    if r.email:
        meta_bits.append(f"✉ {r.email}")
    if r.blog:
        meta_bits.append(f"🔗 {r.blog}")
    if meta_bits:
        lines.append(Text(""))
        lines.append(Text("   ".join(meta_bits), style="green"))

    stats = (
        f"{r.public_repos} public repos   "
        f"{r.followers} followers   "
        f"{r.following} following   "
        f"on GitHub since {r.joined_year}"
    )
    lines.append(Text(""))
    lines.append(Text(stats, style="yellow"))
    lines.append(Text(r.profile_url, style="dim underline"))

    return Panel(Group(*lines), title="GitHub Resume", border_style="cyan", expand=False)


def _skills_panel(r: Resume) -> Panel:
    table = Table(show_header=True, header_style="bold magenta", box=None, expand=False)
    table.add_column("Languages")
    table.add_column("Tools / Topics")

    rows = max(len(r.languages), len(r.tools_and_topics))
    for i in range(rows):
        lang = r.languages[i] if i < len(r.languages) else ""
        topic = r.tools_and_topics[i] if i < len(r.tools_and_topics) else ""
        table.add_row(lang, topic)

    return Panel(table, title="Skills", border_style="magenta", expand=False)


def _projects_panel(r: Resume) -> Panel:
    label = "Projects (pinned)" if not r.used_fallback_projects else "Projects (top repos by stars)"
    groups = []
    for p in r.projects:
        header = Text()
        header.append(p.name, style="bold white")
        if p.language:
            header.append(f"  [{p.language}]", style="blue")
        header.append(f"   ★ {p.stars}", style="yellow")
        if p.forks:
            header.append(f"   ⑂ {p.forks}", style="grey58")
        groups.append(header)

        if p.description:
            groups.append(Text(p.description, style="white"))
        if p.topics:
            groups.append(Text("  ".join(f"#{t}" for t in p.topics), style="dim green"))
        groups.append(Text(p.url, style="dim underline"))
        groups.append(Text(""))

    if not groups:
        groups = [Text("No public repositories found.", style="dim")]

    return Panel(Group(*groups), title=label, border_style="blue", expand=False)


def _footer(r: Resume) -> Text:
    return Text(
        f"Generated with gh-resume · data pulled live from api.github.com/users/{r.username}",
        style="dim italic",
    )
