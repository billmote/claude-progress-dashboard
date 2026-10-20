#!/usr/bin/env python3
# SessionStart: remind the session once that the dashboard is expected on long tasks.
# Turn off with "remind": false in ~/.claude/progress-dashboard/style.json.
import json, os, sys
try:
    with open(os.path.expanduser("~/.claude/progress-dashboard/style.json")) as f:
        if json.load(f).get("remind") is False:
            sys.exit(0)
except Exception:
    pass
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext":
 "PROGRESS DASHBOARD: for a task with more than 5 steps or likely over 30 minutes, invoke the "
 "progress-dashboard skill before the first step, update it as steps finish, and mark it finished "
 "before the final reply. Skip it for quick asks."}}))
