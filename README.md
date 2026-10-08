# Progress Dashboard for Claude Code

A live progress page for long Claude tasks. Open it once in your browser and leave it open.
It refreshes every 10 seconds and shows:

- every step, and whether it is done, working or stuck
- questions waiting on you, with the default Claude is taking so the work never stops
- files Claude made, as clickable links
- a tab for every project, each with every Claude session running in it

Claude starts it on its own for any task with more than 5 steps or over 30 minutes.

## Install

In Claude Code, run:

```
/plugin marketplace add https://github.com/billmote/claude-progress-dashboard.git
/plugin install progress-dashboard@progress-dashboard
```

Restart Claude Code. The first long task asks you three things once (dark or light, dense or
airy, accent color) and remembers them in `~/.claude/progress-dashboard/style.json`.

## Where the page lives

One page for all your projects, one folder above them: if your projects are in `~/code/`, the
page is `~/code/.dashboard/index.html`. Claude tells you the path the first time. Each project
keeps its own session data in `.dashboard/` and its own `index.html` there just forwards to the
one page. Add `.dashboard/` to your `.gitignore` if you work in a git repo.

Projects somewhere else? Add `"root": "/path/to/projects"` to
`~/.claude/progress-dashboard/style.json`.

## What is inside

- `progress-dashboard` skill: when to update, and the small JSON file Claude writes per session
- `scripts/render.py`: builds the page from every project's session files. No model, no
  dependencies, under a second, so updates cost nothing
- Two hooks: a reminder on every message, and a check that stops Claude from ending a task while
  the page still says "working"

Requires `python3`.

## Change your look

Delete `~/.claude/progress-dashboard/style.json` and you will be asked again.

## License

MIT

## Changelog

### 1.2.0 (2026-10-08)
- The page is now built by a small Python script (`scripts/render.py`) instead of a model. Each
  update takes under a second and costs nothing.
- Removed the `dashboard-builder` agent and its folder fence hook.
- Light theme and dense layout options; accent color, title, owner and time zone are configurable.

### 1.1.0 (2026-10-08)
- One page for all projects, one folder above them, with a tab per project. Each tab still shows
  every running session.
- Each project's own page now forwards to the one page.
- Optional `"root"` setting for projects kept somewhere else.

### 1.0.1 (2026-10-06)
- Install instructions use the full repository URL.

### 1.0.0 (2026-10-06)
- First public version: live progress page, questions waiting on you, deliverables, stuck
  sessions, first-run style questions.
