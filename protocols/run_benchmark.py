#!/usr/bin/env python3
"""Run one (target, tool) benchmark pair per METHODOLOGY.md.

5 cold builds + 1 warm rebuild + 1 mutation sync + query latency + 1 quality artifact.
Writes rounds.json + meta.json + raw logs under --out.

Usage:
  python3 run_benchmark.py --repo ../medusa-pos --tool graft --rounds 5 \
      --queries "q1;q2;q3" --out results/2026-09-28/medusa-pos/graft
"""
import argparse, json, os, re, shutil, subprocess, sys, time
from datetime import datetime, timezone

TOOLS = {
    "graft": {
        "build": ["graft", "build"],
        "sync": ["graft", "build"],          # cache replay
        "query": ["graft", "grep"],
        "quality": ["graft", "map"],
        "index_dir": "graft",
        "re": {"nodes": r"(\d+) nodes", "edges": r"(\d+) edges", "files": r"(\d+) of (\d+) files"},
    },
    "codegraph": {
        "build": ["codegraph", "init", "-y"],
        "sync": ["codegraph", "sync"],
        "query": ["codegraph", "query"],
        "quality": ["codegraph", "explore"],
        "index_dir": ".codegraph",
        "re": {"files": r"Indexed (\d+) files", "nodes": r"([\d,]+) nodes", "edges": r"([\d,]+) edges"},
    },
}

def sh(cmd, cwd, timeout=900):
    """Run cmd; return (wall_s, user_s, sys_s, rss_bytes, stdout, stderr, returncode)."""
    before = os.times()  # includes children? no — use getrusage deltas instead
    import resource
    r0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    t0 = time.perf_counter()
    t = subprocess.run(["/usr/bin/time", "-l"] + cmd, cwd=cwd,
                       capture_output=True, text=True, timeout=timeout)
    dt = time.perf_counter() - t0
    r1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    rss = 0
    m = re.search(r"(\d+)\s+maximum resident set size", t.stderr)
    if m:
        rss = int(m.group(1))  # macOS reports bytes
    return {
        "wall_s": round(dt, 3),
        "cpu_user_s": round(r1.ru_utime - r0.ru_utime, 3),
        "cpu_sys_s": round(r1.ru_stime - r0.ru_stime, 3),
        "max_rss_bytes": rss,
        "stdout_tail": "\n".join(t.stdout.strip().splitlines()[-6:]),
        "stderr_tail": "\n".join(t.stderr.strip().splitlines()[-4:]),
        "returncode": t.returncode,
        "stdout_full": t.stdout,
        "stderr_full": t.stderr,
    }

def counts(tool, out):
    pats = TOOLS[tool]["re"]
    r = {}
    for k, pat in pats.items():
        m = re.search(pat, out)
        if m:
            r[k] = int(m.group(1).replace(",", ""))
    return r

def du_kb(path):
    if not os.path.isdir(path):
        return 0
    total = 0
    for dp, _, fns in os.walk(path):
        for fn in fns:
            try:
                total += os.path.getsize(os.path.join(dp, fn))
            except OSError:
                pass
    return total // 1024

def df_free_kb(path):
    st = os.statvfs(path)
    return (st.f_bavail * st.f_frsize) // 1024

def version(tool):
    try:
        return subprocess.run([tool, "--version"], capture_output=True, text=True,
                              timeout=30).stdout.strip().splitlines()[0]
    except Exception as e:
        return f"unknown ({e})"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--tool", required=True, choices=["graft", "codegraph"])
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--queries", default="", help="';'-separated query set")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    repo = os.path.abspath(a.repo)
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    tool = TOOLS[a.tool]
    idx = os.path.join(repo, tool["index_dir"])
    queries = [q.strip() for q in a.queries.split(";") if q.strip()]

    def git(field):
        try:
            return subprocess.run(["git", "-C", repo, field], capture_output=True,
                                  text=True, timeout=15).stdout.strip()
        except Exception:
            return ""

    meta = {
        "date_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repo": repo,
        "repo_name": os.path.basename(repo),
        "tool": a.tool,
        "tool_version": version(a.tool),
        "node": version("node"),
        "rounds": a.rounds,
        "git_head": git("rev-parse HEAD"),
        "git_dirty_files": len([x for x in git("status --porcelain").splitlines() if x.strip()]),
        "df_free_kb_start": df_free_kb(repo),
        "telemetry": "off (graft telemetry disable / codegraph telemetry off, set once per machine)",
    }
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), indent=2)

    rounds = []
    # ---- cold builds ----
    for n in range(1, a.rounds + 1):
        if os.path.isdir(idx):
            shutil.rmtree(idx)
        r = sh(tool["build"], repo)
        r.pop("stdout_full"), r.pop("stderr_full")
        blob = r["stdout_tail"] + r["stderr_tail"]
        r.update(counts(a.tool, r["stdout_tail"]) or counts(a.tool, blob))
        r["index_size_kb"] = du_kb(idx)
        r["phase"] = "cold"
        r["round"] = n
        rounds.append(r)
        open(os.path.join(out, f"cold-{n:02d}.log"), "w").write(
            json.dumps(r, indent=2, ensure_ascii=False))
        print(f"[{a.tool}/{meta['repo_name']}] cold {n}/{a.rounds}: "
              f"wall={r['wall_s']}s size={r['index_size_kb']}kb rc={r['returncode']}")
        if r["returncode"] != 0:
            print("  !! build failed — stderr tail: " + r["stderr_tail"][-300:])

    # ---- warm rebuild ----
    r = sh(tool["sync"], repo)
    r.pop("stdout_full"); r.pop("stderr_full")
    r.update({"phase": "warm", "round": a.rounds + 1, "index_size_kb": du_kb(idx)})
    rounds.append(r)

    # ---- mutation sync ----
    marker = os.path.join(repo, "acx_bench_marker.ts")
    with open(marker, "w") as f:
        f.write("// benchmark mutation probe — safe to delete\n"
                "export function acxBenchMarker(n: number): number {\n  return n * 2;\n}\n")
    r = sh(tool["sync"], repo)
    r.pop("stdout_full"); r.pop("stderr_full")
    r.update({"phase": "mutation_sync", "round": a.rounds + 2, "index_size_kb": du_kb(idx)})
    rounds.append(r)
    os.remove(marker)
    sh(tool["sync"], repo)  # converge (untimed)

    # ---- query latency ----
    qresults = []
    for q in queries:
        lat = []
        for i in range(3):
            t0 = time.perf_counter()
            subprocess.run(tool["query"] + [q], cwd=repo, capture_output=True, text=True, timeout=120)
            lat.append(round(time.perf_counter() - t0, 3))
        qresults.append({"query": q, "latency_s": lat, "median_s": sorted(lat)[1]})
        print(f"[{a.tool}] query '{q}': {sorted(lat)[1]}s (median of 3)")
    # quality artifact
    if queries:
        try:
            qa = subprocess.run(tool["quality"] + ([queries[0]] if a.tool == "codegraph" else []),
                                cwd=repo, capture_output=True, text=True, timeout=120)
            open(os.path.join(out, "quality-artifact.txt"), "w").write(qa.stdout[-20000:])
        except Exception as e:
            print("quality artifact failed:", e)

    meta["df_free_kb_end"] = df_free_kb(repo)
    meta["queries"] = qresults
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), indent=2)
    json.dump(rounds, open(os.path.join(out, "rounds.json"), "w"), indent=2)
    print(f"[{a.tool}/{meta['repo_name']}] done → {out}")

if __name__ == "__main__":
    main()
