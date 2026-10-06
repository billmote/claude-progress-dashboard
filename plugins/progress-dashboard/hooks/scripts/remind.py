#!/usr/bin/env python3
# Every prompt: remind the session the dashboard is mandatory on long tasks.
import json
print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext":
 "PROGRESS DASHBOARD RULE: if this request is a task with more than 5 steps or likely over 30 minutes, "
 "invoke the progress-dashboard skill BEFORE the first step, update it after every step and sub-step "
 "(and at least every 10 minutes), and mark it finished before the final reply. The user should never have to ask."}}))
