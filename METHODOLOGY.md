# Methodology — Agent Context Tooling Benchmark

> Status of this document: **v1.0 (2026-09-28)**. This is the protocol every published round-set
> must follow. Raw data is always published alongside claims — no cherry-picking, no deleted
> rounds.

## 1. Goals

Measure, with reproducible protocol and enough rounds to trust, how local code-graph tools for
AI coding agents perform on this workspace's repositories — and publish everything needed for a
third party to reproduce or refute the numbers.

Round 1 compares:

| Tool | Version | Install route | Kernel |
|---|---|---|---|
| [Graft](https://github.com/trailhq/Graft) (`@nanonets/graft`) | 0.20.0 | `npm i -g` | TypeScript + tree-sitter (native grammars) |
| [CodeGraph](https://github.com/colbymchenry/codegraph) (`@colbymchenry/codegraph`) | 1.6.0 | `npm i -g` | Rust kernel, bundled runtime |

## 2. Test matrix (multi-repo)

| Target | Role | Languages | Tracked files | Status |
|---|---|---|---|---|
| `medusa-pos/` | POS frontend (Tauri + React 18) | TS, TSX, Rust (src-tauri) | ~347 | Round 1 ✓ |
| `store-b2c-boilerplate/` | Backend (Medusa 2.19) + storefront (Next 15) | TS, TSX | ~330 | Round 1 ✓ |
| `medusa-plugins/` | Backend plugin (`@narisolutions/medusa-plugin-pos`) | TS | ~25 | Round 1 ✓ |
| `medusa-plugin-pos-payments/` | Future payments plugin | TS | — | **TODO — Fase 1** (added to the matrix the day the repo exists) |
| `.cache-medusa-src/` | Reference corpus: sparse clone of `medusajs/medusa` (v2.19.0/develop) | TS | 3,672 ts/tsx | Round 2 ✓ single-pair field test (full multi-round protocol **TODO**) |
| `.cache-pagarme/` + siblings | Markdown research corpora (scraped portals) | md | 178 (mostly .md) | **not indexable** — Round 2 ✗ (both tools parsed 1/178 files; excluded from the matrix) |

Each **round-set** = one `(target, tool)` pair executed by
[`protocols/run_benchmark.py`](protocols/run_benchmark.py) with:

1. **Cold builds ×5** — index directory deleted before every run. Measures from-scratch cost.
2. **Warm rebuild ×1** — no changes; Graft replays its parse cache, CodeGraph runs `sync`.
   Measures the steady-state cost agents pay continuously.
3. **Mutation sync ×1** — one new source file added (a 3-line typed function), tool updates the
   index, file removed, index re-converged. Measures reaction to real edits.
4. **Query latency ×3 per query** — a fixed, committed query set per target (3 queries). Wall
   clock per call; first output saved verbatim as a quality artifact.
5. **Quality artifact ×1** — Graft: `graft map` output; CodeGraph: `codegraph explore` on query 1.
   Both saved so readers can judge output quality, not just speed.

### 2b. Round 2 — real-task protocol (field data)

Round 2 inverts the direction: the workspace's **actual pending work** is executed with the
tools in the loop, and the tools' contribution is recorded as field data
([results/2026-09-28/ROUND2.md](results/2026-09-28/ROUND2.md)):

- Tasks are the repos' real backlog (CI drift, docs consistency), executed once each —
  **no A/B baseline, no cross-tool comparison claimed**; the controlled agent-task
  comparison is Round 3.
- Per task, record: what the tools were asked, what they returned, what actually unblocked
  the work, findings that corrected prior beliefs, files changed, and the verification run.
- Corpora viability is a Round 2 deliverable: a corpus joins the matrix only if a tool can
  parse it (markdown corpora failed — 1/178 files; the Medusa source corpus passed).
- Tool-reported token estimates are recorded verbatim, never converted (same rule as §3).

## 3. Metrics

| Metric | Source | Notes |
|---|---|---|
| Wall time | `time.perf_counter()` around subprocess | primary speed metric |
| CPU (user+sys) | `resource.getrusage(RUSAGE_CHILDREN)` deltas | distinguishes IO-bound from CPU-bound |
| Max RSS | `/usr/bin/time -l` (`maximum resident set size`, bytes on macOS) | memory ceiling |
| Index size | `du -sk` of the tool's index directory | persistent disk cost |
| Graph size | files / nodes / edges parsed from each tool's own summary line | comparable only loosely — each tool counts differently |
| Query latency | wall clock per call, median of 3 | |
| Token estimate | tool-reported when available (Graft prints it) | recorded as reported, never converted |

## 4. Statistical treatment

- **Never publish a single run.** Every claim is backed by ≥5 cold rounds (script default 5;
  minimum 3 with an explicit note).
- Report **median, min, max, stdev** for every timed metric. All raw rounds are committed.
- A claim like "tool A is faster than tool B" requires **≥20% median delta AND non-overlapping
  interquartile ranges** across rounds. Otherwise the result is reported as "parity".
- Outliers are **investigated and explained, never silently dropped** (a known cause — e.g. a
  macOS file-cache purge, a background process — is annotated in the round's JSON).
- Tools update fast: **versions are pinned per round-set** and printed in every summary. A new
  tool version means a new round-set, never an in-place edit.

## 5. Fairness controls

- Same machine, same day, sequential runs; **disk free logged before and after** every round-set
  (both tools are sensitive to ENOSPC — one Graft install was already lost to it during setup).
- Tool **defaults everywhere** — no tuning flags, no custom ignore rules.
- Index directories are deleted between cold rounds; **OS file cache is not purged** (that is
  realistic daily usage; "true cold" would require `sudo purge` and is out of scope).
- Tool **telemetry disabled** before measuring (`graft telemetry disable`,
  `codegraph telemetry off`) so measurement traffic doesn't pollute timing or privacy.
- The query sets are committed in this repo and never edited between rounds; quality artifacts
  are saved verbatim.
- Node/runtime path is pinned (nvm `v22.12.0` on the Round 1 machine) because the host has broken
  node installs on PATH — recorded in `environment.json` so readers can replicate.

## 6. Threats to validity (honest list)

- Single machine, single author (n=1 operator). Reproduction instructions are the mitigation.
- Tool-reported node/edge counts are **not comparable across tools** (different definitions of
  "node"); they are only comparable per-tool across rounds/repos.
- Warm rebuilds benefit from OS file cache; first-ever cold build on a fresh machine will be
  slower than published cold numbers.
- Graft's parse cache makes "warm rebuild" nearly free — that is a design difference, reported
  as measured.
- Round 1 targets are small repos (25–347 tracked files). Claims do not extrapolate to monorepos
  100× larger; the future plugin repo and bigger targets will be added per the matrix above.

## 7. Reproduce

```bash
# 0. tools (pin the versions above), telemetry off
npm i -g @nanonets/graft@0.20.0 @colbymchenry/codegraph@1.6.0
graft telemetry disable && codegraph telemetry off

# 1. environment snapshot (once per round-set)
python3 protocols/collect_env.py results/<date>/environment.json

# 2. one (target, tool) pair per invocation — 5 cold rounds + warm + mutation + queries
python3 protocols/run_benchmark.py --repo ../medusa-pos          --tool graft     --rounds 5 \
  --queries "payment dialog provider_id;register session expected cash;draft order parked sales" \
  --out results/<date>/medusa-pos
python3 protocols/run_benchmark.py --repo ../medusa-pos          --tool codegraph --rounds 5 ... # idem

# 3. aggregate everything into summary.md
python3 protocols/summarize.py results/<date>
```

## 8. Where claims end

This benchmark measures **indexing mechanics** (speed, size, memory, latency, artifacts). It
does **not** yet measure end-to-end agent-task success (does the context actually make the agent
solve tasks better/cheaper?) — that requires a task suite and an agent harness, planned as
**Round 3**; Round 2 (§2b) supplies field data from real tasks. Numbers here answer "what does
the tool cost and return", not "which makes the agent smarter".
