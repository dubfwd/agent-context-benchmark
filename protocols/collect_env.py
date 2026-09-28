#!/usr/bin/env python3
"""Snapshot the machine once per round-set → environment.json (METHODOLOGY.md §5)."""
import json, os, platform, subprocess, sys
from datetime import datetime, timezone

out = sys.argv[1] if len(sys.argv) > 1 else "environment.json"
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)

def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=15).stdout.strip()
    except Exception as e:
        return f"error: {e}"

env = {
    "date_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "os": f"macOS {run(['sw_vers', '-productVersion'])}",
    "kernel": platform.release(),
    "arch": run(["uname", "-m"]),
    "chip": run(["sysctl", "-n", "machdep.cpu.brand_string"]),
    "ram_bytes": run(["sysctl", "-n", "hw.memsize"]),
    "cores": run(["sysctl", "-n", "hw.ncpu"]),
    "df_data_volume": run(["df", "-h", "/System/Volumes/Data"]),
    "node": run(["node", "--version"]),
    "graft": run(["graft", "--version"]),
    "codegraph": run(["codegraph", "--version"]),
    "node_path": run(["which", "node"]),
    "note": "npm global prefix is ~/.npm-global (house .npmrc); node via nvm v22.12.0 "
            "(host has a broken node v22.22.3 on default PATH).",
}
json.dump(env, open(out, "w"), indent=2)
print(json.dumps(env, indent=2))
