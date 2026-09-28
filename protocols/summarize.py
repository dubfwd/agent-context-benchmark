#!/usr/bin/env python3
"""Aggregate a round-set directory → summary.md + summary.json (METHODOLOGY.md §4)."""
import glob, json, os, statistics, sys

root = sys.argv[1] if len(sys.argv) > 1 else "."
rows = []
for meta_path in sorted(glob.glob(os.path.join(root, "*", "*", "meta.json"))):
    d = os.path.dirname(meta_path)
    meta = json.load(open(meta_path))
    rounds = json.load(open(os.path.join(d, "rounds.json")))
    cold = [r for r in rounds if r["phase"] == "cold" and r["returncode"] == 0]
    warm = next((r for r in rounds if r["phase"] == "warm"), {})
    mut = next((r for r in rounds if r["phase"] == "mutation_sync"), {})
    if not cold:
        continue
    walls = [r["wall_s"] for r in cold]
    sizes = [r["index_size_kb"] for r in cold]
    last = cold[-1]
    lat = [q["median_s"] for q in meta.get("queries", [])]
    rows.append({
        "repo": meta["repo_name"], "tool": meta["tool"], "version": meta["tool_version"],
        "rounds_ok": f"{len(cold)}/{meta['rounds']}",
        "wall_median_s": round(statistics.median(walls), 2),
        "wall_min_s": min(walls), "wall_max_s": max(walls),
        "wall_stdev_s": round(statistics.stdev(walls), 2) if len(walls) > 1 else 0.0,
        "cpu_median_s": round(statistics.median([r["cpu_user_s"] + r["cpu_sys_s"] for r in cold]), 2),
        "rss_peak_mb": round(max(r["max_rss_bytes"] for r in cold) / 1048576, 1),
        "index_kb_median": round(statistics.median(sizes)),
        "files": last.get("files", ""), "nodes": last.get("nodes", ""), "edges": last.get("edges", ""),
        "warm_s": warm.get("wall_s", ""), "mutation_s": mut.get("wall_s", ""),
        "query_median_s": round(statistics.median(lat), 3) if lat else "",
    })

lines = [
    "# Round summary", "",
    "All cold rounds are committed (`rounds.json` per pair) — nothing dropped. Per",
    "METHODOLOGY.md §4: speed claims need ≥20% median delta and non-overlapping IQR; otherwise",
    "report parity.", "",
    "| repo | tool | ver | rounds ok | wall med (s) | min–max | σ | cpu med (s) | RSS peak (MB) | index (KB) | files | nodes | edges | warm (s) | mutation (s) | query med (s) |",
    "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
]
for r in rows:
    lines.append("| {repo} | {tool} | {version} | {rounds_ok} | {wall_median_s} | "
                 "{wall_min_s}–{wall_max_s} | {wall_stdev_s} | {cpu_median_s} | {rss_peak_mb} | "
                 "{index_kb_median} | {files} | {nodes} | {edges} | {warm_s} | {mutation_s} | "
                 "{query_median_s} |".format(**r))
out_md = os.path.join(root, "summary.md")
open(out_md, "w").write("\n".join(lines) + "\n")
json.dump(rows, open(os.path.join(root, "summary.json"), "w"), indent=2)
print("\n".join(lines))
print(f"\n→ {out_md}")
