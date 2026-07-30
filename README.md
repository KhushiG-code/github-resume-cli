# gh-resume

A terminal-based resume generator that builds a clean, readable resume
directly from a GitHub profile — pinned repos become "projects,"
languages and repo topics become "skills."

```
╭──────────────────────────── GitHub Resume ─────────────────────────────╮
│ The Octocat                                                            │
│ @octocat                                                               │
│                                                                         │
│ GitHub's mascot. I ship changelogs and chase laser pointers.           │
│                                                                         │
│ 📍 San Francisco, CA   🏢 @github   ✉ octocat@github.com               │
│                                                                         │
│ 8 public repos   9821 followers   9 following   on GitHub since 2011  │
│ https://github.com/octocat                                            │
╰─────────────────────────────────────────────────────────────────────────╯
```

## Why it's built this way

**Pinned repos = projects.** GitHub already gives users a curation
tool for "the work I want people to see" — the six repos they pin to
their profile. That's a better signal of "my best projects" than,
say, "most starred" (which rewards old viral repos) or "most recently
updated" (which rewards busywork). The REST API doesn't expose pinned
repos at all, so this tool talks to GitHub's **GraphQL** API for that
one call and falls back to REST for everything else — and if a user
has no pins set (or no token is supplied), it falls back to their
top-starred repos so the resume is never empty.

**Skills = languages + topics, not a hardcoded list.** Language stats
are pulled per-repo and weighted by bytes of code (a 10k-line repo
says more about your Python skills than a 50-line one). Topics are
tags the user themselves attached to their repos, which catch
frameworks and tools that never show up as a "language" — Docker,
PostgreSQL, React, Terraform, etc.

**Never a dead end.** No token? It still works (REST-only, top repos
instead of pinned, clearly labeled as such). No internet or token at
all? `--demo` renders the exact same UI against bundled sample data,
so anyone reviewing this can see the output in five seconds.

## Setup

```bash
git clone <this-repo-url>
cd gh-resume-cli
pip install -r requirements.txt
```

Optional but recommended — install it as a proper CLI command:

```bash
pip install -e .
```

### GitHub token (optional, recommended)

Pinned repos require an authenticated GraphQL request, and
unauthenticated REST calls are capped at 60/hour. Create a token at
<https://github.com/settings/tokens> — no scopes are needed for
public data, a bare token is enough:

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

(or copy `.env.example` to `.env` and load it however you prefer).

## Usage

```bash
# Try it instantly, no token/network needed
python -m gh_resume.cli --demo

# Build a real resume (uses GITHUB_TOKEN from the environment)
python -m gh_resume.cli octocat

# Or pass the token explicitly
python -m gh_resume.cli octocat --token ghp_xxx

# Also save a Markdown copy
python -m gh_resume.cli octocat --output resume.md

# If you installed with `pip install -e .`:
gh-resume octocat
```

### CLI options

| Flag | Description |
|---|---|
| `username` | GitHub username (omit only when using `--demo`) |
| `--token TOKEN` | GitHub personal access token (or set `GITHUB_TOKEN`) |
| `--output FILE.md` | Also write the resume as Markdown |
| `--demo` | Render bundled sample data, no network/token required |
| `--version` | Print version and exit |

## Architecture

```
gh_resume/
├── cli.py            entry point — argument parsing, orchestration, error handling
├── github_client.py  REST + GraphQL calls to api.github.com (GitHubClient, Repo)
├── demo_client.py     same interface as GitHubClient, serves fixtures/demo_data.json
├── resume.py          ResumeBuilder: raw API data -> Resume/Project dataclasses
├── skills.py           ranks languages (by bytes) and topics (by frequency)
├── display.py          renders a Resume as rich panels/tables in the terminal
├── export.py            renders a Resume as Markdown (--output)
└── fixtures/
    └── demo_data.json   sample profile used by --demo
```

**Data flow:** `cli.py` picks `GitHubClient` or `DemoGitHubClient` →
hands it to `ResumeBuilder.build()` → gets back one `Resume`
dataclass → passes that to `display.render()` (terminal) and/or
`export.to_markdown()` (file). `display.py` and `export.py` never
call the network themselves — they only know how to draw a `Resume`
object, which keeps rendering, data-fetching, and data-shaping fully
decoupled and independently testable.

## Testing

`gh_resume/skills.py` has no network dependency, so it's covered by
plain unit tests:

```bash
pip install pytest
pytest tests/
```

## Known limitations

- GitHub's REST API doesn't return byte-level language stats for
  forked repos differently from owned ones beyond the `fork` flag,
  so forks are simply excluded from the language tally.
- Language aggregation samples the 8 most recently updated repos (not
  all of them) to keep API usage light — adjust
  `ResumeBuilder(client, language_sample_size=...)` if you want more.
- Private repos and organizations aren't included; this reflects
  what's visible on a public profile, the same thing a recruiter
  would see.

---

## Submission notes (demo & architecture videos)

This repo is the source-code deliverable. The other two deliverables
are recordings, which should be captured after cloning and trying the
CLI locally:

**Demo video (2–3 min) — suggested script:**
1. `pip install -r requirements.txt`
2. `python -m gh_resume.cli --demo` — show the instant sample output.
3. `export GITHUB_TOKEN=...` then `python -m gh_resume.cli <your-username>`
   — show a real profile being rendered, pinned repos and skills
   populated live from GitHub.
4. `python -m gh_resume.cli <your-username> --output resume.md` — open
   the generated Markdown file to show the export.
5. Run once without `GITHUB_TOKEN` set to show the graceful fallback
   warning and top-starred-repos behavior.

**Architecture walkthrough video (2–3 min) — suggested script:**
1. Draw the module diagram above (Excalidraw/draw.io/Figma) and walk
   through the data flow: `cli.py → GitHubClient/DemoGitHubClient →
   ResumeBuilder → Resume → display.py / export.py`.
2. Explain the REST-vs-GraphQL split and *why* pinned repos need
   GraphQL.
3. Explain the skills-ranking approach (bytes-of-code + topic
   frequency) and the fallback behavior when there's no token or no
   pinned repos.
