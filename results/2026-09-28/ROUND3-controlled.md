# Round 3 (controlled) — same task, with vs. without the graph tool (2026-09-28)

The controlled piece of Round 3: the verification mission of [ROUND3.md](ROUND3.md) scoped to
one bounded task — **10 questions about the Medusa payment contract, answered from the source
clone** — executed by identical agents under two conditions:

- **Arm A (baseline)**: grep/rg + direct file reads only.
- **Arm B (treatment)**: same, **plus** the pre-built Graft index on the clone (`graft grep`).

Same model, same prompt (except the tools paragraph), same questions, 2 runs per arm, all four
launched in parallel. Grading: 1 point per question against the answer key (below), 0.5 for
partial.

## Results

| run | arm | tokens | tool uses | wall (s) | score /10 | graft self-reported "saved" |
|---|---|---|---|---|---|---|
| A1 | baseline | 363,041 | 46 | 191 | **10** | — |
| A2 | baseline | 317,319 | 30 | 166 | **10** | — |
| B1 | graft | 467,617 | 44 | 433 | **10** | ~6,617 tok |
| B2 | graft | 397,103 | 48 | 233 | **10** | ~5,930 tok |
| **median** | **A** | **340,180** | 38 | **178.5** | 10 | |
| **median** | **B** | **432,360** | 46 | **333** | 10 | |

**Outcome: a tie on correctness, and the tool arm cost more** — median **+27% tokens** and
**+87% wall time** for the graft arm. Treatment checks passed (baseline runs' command logs show
no graft usage; treatment runs used `graft grep` first).

## Reading it honestly

- **The task class favors grep.** The clone's payment surface lives in a handful of files a
  symbol grep finds instantly (`abstract-payment-provider.ts`, `payment-webhook.ts`,
  `payment-session.ts`, four route files). Both arms converge on the same reads; the graph adds
  a per-call startup cost (Round 1: ~2 s/call) and a verbose output header on every invocation,
  and appears to invite slightly wider exploration (B1 also mined the repo CHANGELOG — useful
  enrichment, not free).
- **The self-reported "tokens saved" (~5.9–6.6k/run) is real per-call but dwarfed by the net**:
  the graft arm ended ~92k median tokens *more expensive*. Per-call savings ≠ net savings.
- **Contrast with Round 2**: on the *whole* corpus with a hard method-level lookup, Graft found
  what CodeGraph missed. Here, with a small answerable surface, neither advantage applies. The
  tool's value is task-dependent, and on verification tasks over a sparse clone the baseline
  wins on cost at equal correctness.
- **Fairness note**: B's index was pre-built (Round 2, 167 s + 75 MB) — build cost amortized to
  zero here; a first-day agent would pay it.

## Answer key (grading)

1. 10 abstract methods (`capturePayment`, `authorizePayment`, `cancelPayment`, `initiatePayment`,
   `deletePayment`, `getPaymentStatus`, `refundPayment`, `retrievePayment`, `updatePayment`,
   `getWebhookActionAndData`); static `validateOptions` with empty body — abstract-payment-provider.ts:53,207–711
2. Only `authorized`/`captured` run `processPaymentWorkflow`; all other actions early-return —
   subscribers/payment-webhook.ts:47–62
3. `data.session_id` required; without it the event is dropped — payment-webhook.ts:43–45
4. Delay 5000 ms / 3 attempts, configurable via `webhook_delay`/`webhook_retries` —
   api/hooks/payment/[provider]/route.ts:22–31
5. `POST /admin/payment-collections/:id/mark-as-paid` → `markPaymentCollectionAsPaid`; default
   manual provider (`pp_system_default`) — route.ts:18–24 + js-sdk payment-collection.ts:84–99
6. `authorized, captured, pending, requires_more, error, canceled, pending_authorization` —
   payment-session.ts:6–36
7. Yes: optional positive `amount` — admin/payments/validators.ts:50–54
8. `POST /admin/orders/:id/payment-sessions/authorize` (2.17+), returns `{ is_authorized }` —
   admin/orders/[id]/payment-sessions/authorize/route.ts:12–35
9. `payment.captured`, `payment.refunded` (+ internal `payment.webhook_received`); no
   `payment.authorized` — core-flows/events.ts:977–1000
10. 2.21.1 — packages/medusa/package.json:3

All four runs hit every point; notable divergences: A1 hedged slightly on Q9 ("indiretamente")
but concluded correctly; B1 uniquely cited the CHANGELOG for the `provider_id` parameter
history on Q5 (correct and richer).

## Limits

- **n = 2 per arm, one task, one repo, one model.** Directional, not a claim about the tools in
  general — it claims what it measured: on a grep-friendly verification task, the graph layer
  added cost without adding correctness.
- Wall time includes model latency variance (within-arm spread B: 233–433 s), so the +87% is
  the weakest number here; the token delta (+27%) is the more robust one.
- Full transcripts live in the operator session; published here are scores, command logs
  (treatment checks) and the divergences above. Prompts were identical except the tools
  paragraph, reproduced in operator notes.
