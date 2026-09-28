# Round 3 — full-surface verification mission (2026-09-28)

Round 3 is the benchmark's answer to "does any of this help the actual mission?" The mission:
re-verify the whole product surface **as if nothing had been mapped yet** — the 4 in-scope
acquirer APIs (Mercado Pago Point, SumUp, Stone Connect, Cielo Conecta/Pix), the Medusa 2.x
backend contract, the narisolutions plugin surface, and the POS app contract — so that building
`@voolulabs/medusajs-plugin-pos-payments` has no uncharted rough edges. Anything newly
discovered must be folded back into the workspace docs; the execution itself is the benchmark
data.

## Execution shape (operational metrics)

- **4 parallel research fronts** (read-only subagents over the local corpora + source clone),
  each returning facts with `file:line` evidence AND an explicit "NOT FOUND" list:
  - A — transaction limits, TTLs, idempotency, refunds, rate limits, receipt fields (corpora)
  - B — webhook signature/retry/events/re-fetch per acquirer (corpora + official plugin code)
  - C — Medusa payment contract at the source (`.cache-medusa-src`, graft index available)
  - D — POS app + narisolutions plugin contract (code)
- **Dispatch failure is data**: the first parallel dispatch lost 2 of 4 fronts to a provider
  `ETIMEDOUT` (retryable); relaunch succeeded on the first retry. Recorded as an operational
  data point, not hidden.
- Totals across the 4 completed fronts: **~4.5M subagent tokens**, **214 tool uses**,
  ~24 min of front wall time (422 s / 319 s / 443 s / 249 s).

## What the tools contributed

- **Markdown corpora (fronts A/B): grep/ripgrep did 100% of the work.** Consistent with Round
  2's finding — code-graph tools index nothing in scraped portal markdown. The real corpora
  bottleneck was coverage, not tooling: `.cache-deep2/sumup_llms.txt` is **0 bytes** (the SumUp
  scrape silently failed back when it was made) — SumUp answers came from the official plugin's
  source code instead. Corpus defect recorded in the workspace docs.
- **Code corpus (front C): the graft index built in Round 2 paid off** — the agent used
  `graft grep` for symbol location (tool-reported ~93 tokens saved there) and direct file reads
  elsewhere, because the sparse clone lacks several module sources (`@medusajs/payment`,
  `core-flows`) — no tool can index files that aren't there.
- **App/plugin code (front D): plain grep/read.** No graph tooling claimed or needed.

## Outcome — docs survived the fresh-eyes audit, and what didn't

Roughly **30 audited claims were already documented** and held up (webhook pipeline 5s/3
retries/session_id/only-authorized-captured in event-bus.md; MP idempotency, TTL, x-signature
incl. the QR-code exception, 22s ACK/15min retries; Stone 200/min + sandbox 10 req/s + mandatory
close-after-webhook + split-on-authorization; Cielo confirmation + partial voids + no-webhook
model + Pix 300s; SumUp HMAC + retry 1/5/20min/2h + valid_until). The genuinely new findings,
all applied to the workspace docs the same day:

1. **Provenance defect (round-wide)**: the Medusa source clone is on **branch `develop`,
   version 2.21.1** — not the `v2.19.0` tag our docs cited as source. All "verificado no fonte
   v2.19.0" citations across 9 docs relabeled; version-sensitive contract claims flagged for
   re-verification against the exact backend version in Fase 1.
2. **Webhook actions are half-blind by design**: only `authorized`/`captured` move state in the
   core; `failed`/`canceled`/`pending` are dropped without touching the session → terminal
   declines must reach the app via **polling** (`getPaymentStatus`), never via webhook.
3. **`PaymentSession` has no TTL in the core** — expiry is the acquirer charge's job; adapter
   must handle expired charges (documented per-acquirer: MP `expiration_time`, SumUp
   `valid_until`, Cielo Pix ~300 s, Stone: orders don't expire).
4. **Partial capture/refund exist in the core HTTP contract** (`amount` optional positive) —
   adapter must validate against each acquirer's policy (Cielo windows: 330/690/150 days by
   product — newly documented; Stone classic 5-day capture window + discontinued deferred-
   capture route — newly documented; Stone deferred capture is out of our design).
5. **`POST /admin/orders/:id/payment-sessions/authorize`** (2.17+, `{is_authorized}`) surfaced
   as a synchronous alternative to markAsPaid for the polling dialog flow.
6. **The app receipt is closed and card-blind**: `ReceiptData` has no NSU/authorization
   code/brand/installments fields and the generator accepts no extra rows — the plugin must
   expose them (Stone webhook `metadata`, Cielo `Receipt` block + PPCONECTA Base64 receipts;
   MP Orders API fields = new 🟡 pendência; SumUp 🟡), and the app needs a `PosPlugin`-seam
   extension to print them.
7. **Corpus defect**: SumUp scrape empty (above) — noted in sumup.md provenance.

## Honest limits

- This is **field data from real mission work**, not a controlled comparison: n=1 operator,
  one ordering of fronts, no no-tool baseline. Round 3's remaining planned piece (same task
  with/without tool context wired into an agent, tokens + correctness) is still open and now
  has this mission as its task template.
- Front C could not verify module internals absent from the sparse clone (`@medusajs/payment`,
  `core-flows`) — marked "NOT VERIFIABLE IN THIS CLONE" rather than guessed.
