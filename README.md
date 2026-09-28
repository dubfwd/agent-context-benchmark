# Agent Context Tooling Benchmark

Reproducible, multi-round benchmark of **local code-graph tools for AI coding agents**, run on a
real multi-repo product workspace: a Tauri/React POS frontend, a Medusa v2 backend + Next.js
storefront, and a Medusa backend plugin. Published raw — every round, every machine state.

- **Methodology:** [METHODOLOGY.md](METHODOLOGY.md) (multi-round protocol, fairness controls,
  statistical treatment, threats to validity)
- **Protocol:** [`protocols/`](protocols/) — `run_benchmark.py` (one target×tool pair),
  `collect_env.py`, `summarize.py`
- **Round 1 data:** [`results/2026-09-28/`](results/2026-09-28/) — raw logs, `rounds.json`,
  `summary.md`

## Why

Tools like Graft and CodeGraph claim to make coding agents faster/cheaper via a local code
graph. Most published numbers are single-run screenshots. This benchmark runs **≥5 cold rounds +
warm + mutation + query latency** per (repo × tool), publishes all raw rounds, and states claims
only where the METHODOLOGY's statistical bar is met.

## Round 1 (2026-09-28) — Graft 0.20.0 vs CodeGraph 1.6.0

Machine: macOS, `environment.json` has the full snapshot (chip, RAM, disk). Telemetry disabled
on both tools. Index dirs deleted between cold rounds. Raw rounds: `results/2026-09-28/*/`.

| Repo (role) | Tool | Cold build med (s), min–max, σ | CPU med (s) | RSS peak (MB) | Index (KB) | files / nodes / edges | Warm (s) | Mutation (s) | Query med (s) |
|---|---|---|---|---|---|---|---|---|---|
| **medusa-plugins** (backend plugin) | codegraph 1.6.0 | **5.82** (4.798–5.893, σ 0.55) | 4.46 | 171.8 | 280 | 14 / 55 / 77 | 1.654 | 3.792 | 1.759 |
| **medusa-plugins** (backend plugin) | graft 0.20.0 | **3.11** (2.495–3.374, σ 0.33) | 2.48 | 83.8 | 93 | 11 / 27 / 44 | 2.904 | 3.924 | 2.112 |
| **medusa-pos** (POS frontend) | codegraph 1.6.0 | **9.27** (8.727–11.037, σ 0.88) | 10.47 | 231.8 | 7992 | 231 / 2628 / 6758 | 2.01 | 3.149 | 1.816 |
| **medusa-pos** (POS frontend) | graft 0.20.0 | **15.48** (14.277–18.78, σ 1.77) | 14.31 | 190.4 | 4365 | 223 / 1018 / 2810 | 3.482 | 3.446 | 2.217 |
| **store-b2c-boilerplate** (backend + storefront) | codegraph 1.6.0 | **9.22** (8.248–9.96, σ 0.7) | 10.09 | 225.3 | 7768 | 296 / 2558 / 5092 | 1.857 | 3.291 | 2.059 |
| **store-b2c-boilerplate** (backend + storefront) | graft 0.20.0 | **15.9** (13.441–16.986, σ 1.34) | 12.75 | 170.7 | 4305 | 288 / 875 / 1950 | 2.946 | 3.333 | 2.066 |

**Findings that pass the §4 bar (≥20% median delta + non-overlapping IQR):**

1. **CodeGraph builds ~40% faster on the two real-size repos** — 9.27s vs 15.48s on `medusa-pos`
   (−40%) and 9.22s vs 15.90s on `store-b2c-boilerplate` (−42%), non-overlapping ranges across
   all 10 rounds. On the tiny `medusa-plugins` (14–25 files) the order flips: Graft 3.11s vs
   CodeGraph 5.82s (+87%) — CodeGraph pays a fixed kernel/startup cost that dominates small
   targets.
2. **Graft's index is ~45% smaller** on `medusa-pos` (4.3 MB vs 7.8 MB) and 4.1 vs 7.6 MB on
   `store-b2c-boilerplate` — at the cost of a sparser graph (1,018 vs 2,628 nodes).
3. **CodeGraph captures ~2.5× more symbols** (own definition of "node"; per-tool comparison
   only).
4. **Warm rebuild**: CodeGraph `sync` ~1.9–2.0s vs Graft build-with-cache ~2.9–3.5s across all
   repos.
5. **Memory**: CodeGraph peaks higher (172–232 MB vs 84–190 MB) — matters on small-RAM dev
   machines.
6. **Query latency**: parity territory (1.6–2.3s across all pairs) — both are fast enough that
   latency is not the differentiator; output *content* is (see `quality-artifact.txt` per pair).

**Parity / not claimable:** query latency differences (all <20% consistently); anything about
agent-task success (Round 3).


### Reading the numbers

- `wall med` = median cold-build wall time across 5 rounds; `min–max`/`σ` show spread.
- Node/edge counts are **each tool's own definition** — compare per-tool across repos, never
  across tools.
- Warm rebuild: Graft replays a parse cache (near-free by design); CodeGraph `sync` is
  incremental.
- Query latency uses each tool's own search (`graft grep` / `codegraph query`) — directionally
  comparable, definitions differ.
- Quality artifacts (saved verbatim per pair): Graft's `map` output, CodeGraph's `explore`
  output (blast radius with callers and tests).

## Round 2 (2026-09-28) — real-task field test + corpora viability

Round 1 measured the tools on synthetic workloads. Round 2 executed the workspace's **actual
pending work** (CI-drift fixes across the 3 repos) with the tools in the loop, and settled the
corpora question. Full log: [`results/2026-09-28/ROUND2.md`](results/2026-09-28/ROUND2.md).

Field findings (single operator, tasks run once — no cross-tool winner claimed; that is
Round 3's controlled job):

- Both tools are **blind to GitHub Actions YAML** — `graft grep` returned 0 hits for a string
  sitting in `release.yml`. The CI work ran on plain grep, `git ls-remote` and a
  `raw.githubusercontent.com` verification; the graph added nothing for this task class.
- **Markdown research corpora are not indexable** by either tool (`.cache-pagarme`: Graft
  parsed 1/178 files, CodeGraph 1/178) — ripgrep stays the corpora tool.
- The **code corpus** (sparse clone of `medusajs/medusa`, 3,672 ts/tsx files, ~16× the largest
  Round 1 target) is the only viable new target:

  | tool | build (s) | files | index (MB) | max RSS (MB) | query on a real lookup |
  |---|---|---|---|---|---|
  | graft 0.20.0 | 167.0 | 3,672/3,672 parsed | 75 | 761 | found the symbol (4 hits, exact lines) |
  | codegraph 1.6.0 | 34.0 | 3,676 indexed, **10,003 unparseable (73% of scanned)** | 113 | 966 | found the class, **missed the abstract method** |

- The task work itself produced a **severity correction**: tauri-action v1's
  `uploadUpdaterJson` defaults to `true`, so the dead `includeUpdaterJson` input never lost
  the updater feed — the workspace's engineering doc claimed otherwise and was fixed.

## Reproduce

See [METHODOLOGY.md §7](METHODOLOGY.md#7-reproduce). One command per (repo × tool); everything
else is collected automatically.

## Roadmap

- **Round 3 (complete, 2026-09-28):** **full-surface verification mission** — the workspace's
  actual backlog executed with the tools in the loop
  ([ROUND3.md](results/2026-09-28/ROUND3.md)), **plus the controlled piece**: same task with vs.
  without the graph tool, 2 runs per arm — correctness tie (10/10 both arms), graft arm median
  **+27% tokens / +87% wall** on a grep-friendly verification task
  ([ROUND3-controlled.md](results/2026-09-28/ROUND3-controlled.md)).
- **New targets:** `@voolulabs/medusajs-plugin-pos-payments` joins the matrix when the repo
  exists (Fase 1 of the product plan); the Medusa source corpus gets the full multi-round
  protocol (Round 2 was a single-pair field test).
- New tool versions ⇒ new round-set, never in-place edits.

## License / provenance

Data collected on the authors' machine; scripts MIT. Tool names and trademarks belong to their
owners. This folder is self-contained and can be published as its own repository.
