#!/usr/bin/env python3
# Keeps the dashboard-builder agent inside .dashboard/. Every other caller passes through.
import json, os, sys
d = json.load(sys.stdin)
if d.get("agent_type") != "dashboard-builder":
    sys.exit(0)
i = d.get("tool_input", {})
p = os.path.realpath(os.path.expanduser(i.get("file_path") or i.get("path") or os.getcwd()))
if "/.dashboard" in p + "/":
    sys.exit(0)
print("dashboard-builder may only use .dashboard/", file=sys.stderr)
sys.exit(2)
