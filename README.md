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
