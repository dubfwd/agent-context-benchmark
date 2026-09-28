# Token consumption analysis — Round 3 controlled experiment

Companion to [ROUND3-controlled.md](ROUND3-controlled.md). Focus: what the tool arms actually
cost in tokens, why the tools' own "tokens saved" claims don't net out, and how robust the
token numbers are. All runs: same 10-question verification task over the Medusa source clone,
n = 2 per arm, tokens as reported by the harness for each subagent loop (input + output across
all its turns).

## 1. Raw numbers

| arm | runs (tokens) | median | vs. baseline |
|---|---|---|---|
| A — grep only | 317,319 / 363,041 | **340,180** | — |
| B — + Graft | 397,103 / 467,617 | **432,360** | **+27%** |
| C — + CodeGraph | 445,103 / 490,015 | **467,559** | **+37%** |

## 2. Separation from the baseline is clean

Despite n = 2, the token ranges **do not overlap with the baseline**: the worst baseline run
(363k) cost less than the best tool run (397k). All four pairwise baseline-vs-tool comparisons
agree in direction. B and C do overlap each other (445k < 467.6k) — the two tools are
statistically indistinguishable from one another here, but neither is distinguishable from
"costs more than grep". The wall-time column does not share this property (433 s outlier inside
arm B); tokens are the robust metric in this experiment.

## 3. Why a "token-saving" tool costs more tokens

Three mechanisms, in likely order of magnitude:

1. **Agent-loop re-ingestion.** Every tool output enters the agent's context and is re-read by
   the model on every subsequent turn of that run. A graph tool that prints a fixed verbose
   frame per call (Graft: header/footer with usage guidance and the "🌱 graft saved ~N tokens"
   line; CodeGraph: box-drawn result frames) pays that fixed cost again on every remaining
   turn. A ~200-token frame repeated across dozens of turns is a real tax, and it compounds
   with the outputs of every other tool the agent uses afterwards.
2. **The savings claim is measured against a strawman.** Graft's per-run estimate
   ("~6,617" and "~5,930 tokens saved", as printed) compares against *reading the covered files
   whole*. The realistic counterfactual for this task was not whole-file reads — it was a
   targeted `grep` returning a few lines. Against grep, a graph call loses before the agent
   even follows up. Measured against the wrong baseline, "98% saved" is true and irrelevant.
3. **Availability invites exploration.** Equipping the agent changed its behavior, not just its
   tools: B1 mined the repository CHANGELOG (a genuinely useful enrichment for one answer —
   and priced in), and both tool arms roamed slightly wider. Usage reflects this: the treatment
   arms used the graph tool only 1–4 times per run (CodeGraph: **exactly once**, the class
   lookup) and did everything else with grep — yet finished ~90–130k tokens above baseline.

Net effect: per-call savings (~6k, claimed) are **10–20× smaller** than the net cost
(~90–130k, measured).

## 4. Mission-scale reference (not a controlled comparison)

The same day's full verification mission (4 parallel fronts, ~4.5M subagent tokens total) split
as: markdown corpora 1.77M, webhook corpora 0.74M, Medusa source **with Graft available** 0.97M,
app/plugin code 1.02M. Tempting but wrong to read "the Graft front was cheapest": fronts differ
in material (portal pages are far more verbose than source files), so the mission numbers carry
a task confound the controlled experiment was built to remove.

## 5. The one case where the graph won tokens

Round 2's pathological lookup — a hard method-level query across the whole corpus — is the only
token win observed: Graft resolved `getWebhookActionAndData` with exact lines and reported
~6.7k tokens saved where the honest grep alternative needed the right query shape to hit
(CodeGraph missed it entirely). The pattern across the day is consistent: **the graph pays for
itself on hard, wide lookups over large code surfaces, and loses on narrow, grep-friendly
tasks** — and real work contains both kinds.

## 6. Caveats

- n = 2 per arm, one task, one repo, one model, one day. Directional evidence with clean
  baseline separation — not a general claim about the tools.
- `subagent_tokens` is the harness's report of the subagent loop; it is not broken down into
  input vs. output, so mechanism 1 (re-ingestion) is inferred from how agent loops work, not
  directly measured.
- The orchestrator's own token spend (reading the four reports, grading) is not counted — it is
  identical across arms by design and cancels out.
- Both tool arms ran with pre-built indices; first-day costs (Graft 167 s / 75 MB from Round 2;
  CodeGraph 25.6 s / 113 MB / 914 MB peak RSS, recorded when rebuilt for arm C) are real but
  amortize across many runs.
