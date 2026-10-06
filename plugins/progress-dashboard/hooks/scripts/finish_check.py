#!/usr/bin/env python3
# Stop: refuse to end the turn while the dashboard still shows this machine's session as
# unfinished and it was updated in the last 6 hours. Blocks once per stop attempt chain.
import json, os, sys, glob, datetime
d = json.load(sys.stdin)
if d.get("stop_hook_active"):
    sys.exit(0)
dirs = {os.path.join(d.get("cwd") or os.getcwd(), ".dashboard/sessions"), os.path.expanduser("~/.dashboard/sessions")}
now = datetime.datetime.now(datetime.timezone.utc)
for dd in dirs:
    for f in glob.glob(os.path.join(dd, "*.json")):
        if not os.access(f, os.W_OK):   # other sessions' copies are read-only
            continue
        try:
            s = json.load(open(f))
        except Exception:
            continue
        if s.get("finished"):
            continue
        age = now - datetime.datetime.fromtimestamp(os.path.getmtime(f), datetime.timezone.utc)
        if age < datetime.timedelta(hours=6):
            print(f"The progress dashboard session {s.get('id', os.path.basename(f))} is not marked finished. "
                  "If the task is done (or stopped), tell dashboard-builder it is finished, then end. "
                  "If work is still running, update the dashboard now.", file=sys.stderr)
            sys.exit(2)
sys.exit(0)
