---
name: progress-dashboard
description: This skill should be used at the START of any task with more than 5 steps or expected to take longer than 30 minutes (a big migration, a multi-file refactor, a data cleanup, a report build), and after every step of such a task. It keeps one live progress page for all projects, a tab per project, rebuilt by a script.
---

# Progress dashboard

Run this for any task with more than 5 steps or longer than 30 minutes. Skip it for quick asks.

## Update rule (this is the whole point)
The user watches the page, not the chat. A page that lags the real work is a failure, and a page
that still says "working" after the task is done is the worst failure. Update it:
- **Before step 1**, so the page exists.
- **After every step AND every sub-step**, any time a line on the page would change state.
- **At least every 10 minutes** during a long step, even if only the "doing now" line changes.
- **Before asking the user anything** and right after they answer.
- **At the end**, marking the session finished, BEFORE the final chat reply.
Never batch several finished steps into one update. Never let two steps pass without one.

## How it works
- You only write one small JSON file per session. The plugin's script, `scripts/render.py` (two
  folders up from this skill), turns every session file in every project into the page in under
  a second, with no model. Never write or edit the HTML yourself.
- **Root** = the folder holding all the user's projects. Default: the parent of the current
  folder. A `"root"` path in `~/.claude/progress-dashboard/style.json` overrides it.
- **Session file**: `<root>/<project>/.dashboard/sessions/<id>.json`.
- **The page**: `<root>/.dashboard/index.html`, a tab per project that has a `.dashboard/` folder.
  The script turns each project's own `.dashboard/index.html` into a page that forwards there.
- **Render**: `python3 <plugin>/scripts/render.py <root>`. It prints one line when done.

## Session file
```json
{
  "id": "db-migration-20261008-1415",
  "title": "Move orders to the new database",
  "started": "2026-10-08T14:15:02-04:00",
  "last_update": "2026-10-08T14:22:40-04:00",
  "finished": false,
  "finished_at": null,
  "doing_now": "Copying the orders table",
  "summary": "One plain sentence. Set it when finished.",
  "steps": [
    {"name": "Back up the old database", "status": "done", "note": "2.1 GB"},
    {"name": "Copy tables", "status": "working", "sub": [{"name": "customers", "status": "done"}]},
    {"name": "Switch the app over", "status": "not started"}
  ],
  "questions": [{"q": "Drop the old tables afterwards?", "default": "Keeping them for now", "at": "..."}],
  "stuck": ["One plain sentence per thing that is stuck"],
  "deliverables": [{"label": "Migration log", "value": "logs/migrate.txt", "at": "..."}],
  "panels": [{"title": "Numbers", "rows": [{"label": "Rows copied", "value": "1,204,331"}]}],
  "log": [{"at": "...", "text": "Started."}]
}
```
Step status is `done`, `working`, `stuck` or `not started`. A deliverable `value` is a path inside
the project, an absolute path, or a URL. Take every time from `date '+%Y-%m-%dT%H:%M:%S%z'`; never
make one up. Plain English everywhere, no jargon.

## Before the first step
1. **Style.** Read `~/.claude/progress-dashboard/style.json`. If it does not exist, ask the user
   once with AskUserQuestion, one picker with three questions: dark or light, dense or airy, one
   accent color (offer four; they can type any hex). Save `{"theme", "density", "accent"}` there.
   Optional keys: `title` (default "Work Board"), `owner` (default "you"), `timezone`, `root`.
2. **Session id.** `<task-slug>-<YYYYMMDD-HHMM>` in the user's local time.
3. **Write the session file and render.** Then tell the user once, in one line, the full path to
   `<root>/.dashboard/index.html`: open it in a browser and leave it open.

## Every update
Edit the session file (step states, `doing_now`, questions, deliverables, a log line, a fresh
`last_update`), then run the render command. Do not narrate dashboard updates in chat.

If Claude runs somewhere other than the user's computer (a cloud workspace linked to it), write
the session file to the user's computer, compare checksums on both sides, and run the script
there. Copy from a new, unique folder each time; reusing a path can silently deliver a stale copy.

## Decisions
When a decision is needed from the user, add it to `questions` with the default being taken,
update the page, then keep working with that default. Do not stop and wait.

## Finish
1. Set every step's final state, `"finished": true`, `finished_at`, and a one-sentence `summary`.
2. Render, and confirm the session file contains `"finished": true`.
3. Only then give the normal short summary in chat.
