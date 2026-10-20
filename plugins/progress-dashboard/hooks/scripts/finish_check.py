#!/usr/bin/env python3
# Stop: nudge once per Claude session if a dashboard session file touched in the last
# 30 minutes is still not marked finished. Never blocks twice in the same session.
# Turn off with "finish_check": false in ~/.claude/progress-dashboard/style.json.
import json, os, sys, glob, time

HOME = os.path.expanduser("~/.claude/progress-dashboard")
WINDOW = 30 * 60

def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(d, dict) or d.get("stop_hook_active"):
        return 0
    try:
        with open(os.path.join(HOME, "style.json")) as f:
            if json.load(f).get("finish_check") is False:
                return 0
    except Exception:
        pass
    sid = "".join(c for c in str(d.get("session_id") or "") if c.isalnum() or c in "-_")
    state = os.path.join(HOME, "state")
    marker = os.path.join(state, "stop-" + sid) if sid else None
    if marker and os.path.exists(marker):
        return 0
    now = time.time()
    dirs = {os.path.join(d.get("cwd") or os.getcwd(), ".dashboard", "sessions"), os.path.expanduser("~/.dashboard/sessions")}
    for dd in dirs:
        for f in glob.glob(os.path.join(dd, "*.json")) + glob.glob(os.path.join(dd, "*", "*.json")):
            try:
                if not os.access(f, os.W_OK) or now - os.path.getmtime(f) > WINDOW:
                    continue
                with open(f) as fh:
                    s = json.load(fh)
            except Exception:
                continue
            if not isinstance(s, dict) or s.get("finished"):
                continue
            if marker:
                try:
                    os.makedirs(state, exist_ok=True)
                    for old in glob.glob(os.path.join(state, "stop-*")):
                        if now - os.path.getmtime(old) > 7 * 86400:
                            os.remove(old)
                    open(marker, "w").close()
                except Exception:
                    pass
            print(f"The progress dashboard still shows {s.get('id', os.path.basename(f))} as running. "
                  "If this session's task is done or stopped, set \"finished\": true and re-run render.py. "
                  "If it belongs to another session, ignore this.", file=sys.stderr)
            return 2
    return 0

sys.exit(main())
