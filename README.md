# Progress Dashboard for Claude Code

A live progress page for long Claude tasks. Open it once in your browser and leave it open.
It refreshes every 10 seconds and shows:

- every step, and whether it is done, working or stuck
- questions waiting on you, with the default Claude is taking so the work never stops
- files Claude made, as clickable links
- every Claude session running in the same folder, one card each

Claude starts it on its own for any task with more than 5 steps or over 30 minutes.

## Install

In Claude Code, run:

```
/plugin marketplace add billmote/claude-progress-dashboard
/plugin install progress-dashboard@progress-dashboard
```

Restart Claude Code. The first long task asks you three things once (dark or light, dense or
airy, accent color) and remembers them in `~/.claude/progress-dashboard/style.json`.

## Where the page lives

`.dashboard/index.html` in the folder you started Claude in. Claude tells you the path the first
time. Add `.dashboard/` to your `.gitignore` if you work in a git repo.

## What is inside

- `progress-dashboard` skill: when to run and when to update
- `dashboard-builder` agent: builds the page; can only touch `.dashboard/`
- Three hooks: a reminder on every message, a fence that keeps the builder inside
  `.dashboard/`, and a check that stops Claude from ending a task while the page still says
  "working"

Requires `python3` for the hooks.

## Change your look

Delete `~/.claude/progress-dashboard/style.json` and you will be asked again.

## License

MIT
