---
name: progress-dashboard
description: This skill should be used at the START of any task with more than 5 steps or expected to take longer than 30 minutes (a big migration, a multi-file refactor, a data cleanup, a report build), and after every step of such a task. It keeps one live progress page for all projects, a tab per project, via the dashboard-builder agent.
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

## Where things live
- **Root** = the folder that holds all the user's projects. Default: the parent of the current
  folder. If `~/.claude/progress-dashboard/style.json` has a `"root"` path, use that instead.
- **The page**: `<root>/.dashboard/index.html`, one page for every project.
- **Session data stays in each project**: `<project>/.dashboard/sessions/<id>.json`.
- **Each project's own** `.dashboard/index.html` is a small page that forwards to the root page
  (`<meta http-equiv="refresh" content="0; url=../../.dashboard/index.html">`).

## Before the first step
1. **Style.** Read `~/.claude/progress-dashboard/style.json`. If it does not exist, ask the user
   once with AskUserQuestion, one picker with three questions: dark or light, dense or airy, one
   accent color (offer four common colors; they can type any hex). Save the answers to that file
   as `{"theme": ..., "density": ..., "accent": ...}`. Never ask again once saved.
2. **Session id.** `<task-slug>-<YYYYMMDD-HHMM>` in the user's local time, from `date`.
3. **Build.** Call the `dashboard-builder` agent with: the session id, the root path, this
   project's folder name, the style, the task list
   (with sub-steps where a step is long), and the output of `date '+%Y-%m-%dT%H:%M:%S%z'`.
4. **Tell the user once**, in one line, the full path to `<root>/.dashboard/index.html`: open it in a
   browser and leave it open. It refreshes itself.

## After every update
Call `dashboard-builder` with the same id, what changed, any new deliverable paths, and a fresh
`date`. Do not narrate dashboard updates in chat.

## If the session runs somewhere other than the user's computer
Some setups run Claude in a cloud workspace linked to the user's computer. Then the page has to
be copied over after every update. Copy from a new, unique folder each time (reusing a path can
silently deliver a stale copy), and compare checksums on both sides. An update is not done until
they match. Also copy other sessions' files from the user's `.dashboard/sessions/` into the
working copy first, so the page shows every running session.

## Decisions
When a decision is needed from the user, add it to the page's questions list together with the
default being taken, then keep working with that default. Do not stop and wait.

## Finish
1. Tell `dashboard-builder` the session is finished and every step's final state.
2. Confirm `<project>/.dashboard/sessions/<id>.json` contains `"finished": true`.
3. Only then give the normal short summary in chat.
