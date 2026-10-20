# Progress Dashboard for Claude Code

A live progress page for long Claude tasks. Open it once in your browser and leave it open.
It refreshes every 10 seconds and shows:

- every step, and whether it is done, working or stuck
- questions waiting on you, with the default Claude is taking so the work never stops
- files Claude made, as clickable links
- a tab for every project, each with every Claude session running in it

Claude starts it on its own for any task with more than 5 steps or over 30 minutes.

![Progress dashboard](https://raw.githubusercontent.com/billmote/claude-progress-dashboard/main/docs/screenshot.png)

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
- Two hooks: a one-time reminder when a session starts, and a one-time nudge if Claude tries to
  stop while a dashboard session touched in the last 30 minutes still says "working"

Requires `python3`.

## Turning off the nudges

Add either key to `~/.claude/progress-dashboard/style.json`:

```json
{"remind": false, "finish_check": false}
```

## Change your look

Delete `~/.claude/progress-dashboard/style.json` and you will be asked again.

## License

MIT

## Changelog

### 1.4.0 (2026-10-20)
- Gentler hooks. The reminder now appears once when a session starts instead of on every
  message. The end-of-task check nudges at most once per session, only for dashboard sessions
  touched in the last 30 minutes, so another running session can no longer keep blocking yours.
- Both can be turned off in `style.json` (`"remind": false`, `"finish_check": false`).

### 1.3.0 (2026-10-13)
- "Waiting on you" no longer piles up. Each card has a **Done** button (remembered in that
  browser), and questions from finished sessions fold away after 7 days (`expire_days`).
- Claude now marks a question answered the moment you answer it, sweeps open questions at the
  start of every session, and drops questions whose default was simply taken when a session ends.

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
