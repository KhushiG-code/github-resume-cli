"""Optional export of a Resume to a Markdown file (--output flag)."""

from __future__ import annotations

from .resume import Resume


def to_markdown(r: Resume) -> str:
    lines: list[str] = []
    lines.append(f"# {r.name or r.username}")
    lines.append(f"**@{r.username}** — [{r.profile_url}]({r.profile_url})")
    if r.bio:
        lines.append(f"\n*{r.bio}*")

    meta = []
    if r.location:
        meta.append(f"📍 {r.location}")
    if r.company:
        meta.append(f"🏢 {r.company}")
    if r.email:
        meta.append(f"✉ {r.email}")
    if r.blog:
        meta.append(f"🔗 {r.blog}")
    if meta:
        lines.append("\n" + " | ".join(meta))

    lines.append(
        f"\n{r.public_repos} public repos · {r.followers} followers · "
        f"{r.following} following · on GitHub since {r.joined_year}"
    )

    if r.languages:
        lines.append("\n## Skills")
        lines.append(f"**Languages:** {', '.join(r.languages)}")
        if r.tools_and_topics:
            lines.append(f"**Tools / Topics:** {', '.join(r.tools_and_topics)}")

    label = "Projects (pinned)" if not r.used_fallback_projects else "Projects (top repos by stars)"
    lines.append(f"\n## {label}")
    for p in r.projects:
        stats = f"★ {p.stars}"
        if p.forks:
            stats += f" · ⑂ {p.forks}"
        lang = f" `{p.language}`" if p.language else ""
        lines.append(f"\n### [{p.name}]({p.url}){lang} — {stats}")
        if p.description:
            lines.append(p.description)
        if p.topics:
            lines.append(" ".join(f"`{t}`" for t in p.topics))

    lines.append("\n---\n*Generated with gh-resume*")
    return "\n".join(lines)
