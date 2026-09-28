# Round 2 — real-task field test + corpora viability (2026-09-28)

Round 2 inverts Round 1's direction: instead of synthetic workloads, we executed the
workspace's **actual pending work** (CI-drift fixes across 3 repos) with Graft 0.20.0 /
CodeGraph 1.6.0 in the loop, and answered the corpora question. Single operator, tasks run
once — **no cross-tool winner is claimed from this round**; the controlled agent-task
comparison is Round 3. Everything below is reproducible from the repos' working trees
(commits pending owner authorization, per workspace rule) and the quoted log lines.

## Tasks executed (real pending work)

### T1 — medusa-pos `release.yml`: dead tauri-action input + unpinned third-party actions

- Verified against the v1 tag's `action.yml` (raw.githubusercontent.com): the input is
  `uploadUpdaterJson` (default **`true`**); `includeUpdaterJson` no longer exists.
- **Severity correction vs the first audit**: the old input name was ignored with an
  "unexpected input" warning, and because `uploadUpdaterJson` defaults to true, the updater
  feed (`latest.json`) **was not being lost** — the workspace engineering doc claimed it was;
  corrected.
- Fixed: input renamed; 4 third-party actions pinned to 40-char SHAs with version comments
  (house rule): `pnpm/action-setup` v6.1.0 · `dtolnay/rust-toolchain` (head of `stable`
  branch — action maintained by branch, not tag) · `Swatinem/rust-cache` v2.9.2 (highest v2;
  checked no v2.10/v3) · `tauri-apps/tauri-action` v1.0.0 (highest v1; checked no v1.1/v2).
- Verification: YAML parses (PyYAML); no leftover old names/versions; diff = 1 file, 5 hunks.

### T2 — store-b2c-boilerplate `ci.yml`: actions v4 → v7 (+ new `dependabot.yml`)

- `checkout`/`setup-node` v4 → v7 (6 call sites); `pnpm/action-setup@v4` pinned to SHA
  (v4.4.0, highest v4 — major bump deliberately left to Dependabot).
- New `.github/dependabot.yml` (house molde = medusa-pos): two `npm` entries (`/backend`,
  `/storefront` — separate pnpm lockfiles) + `github-actions` monthly; cooldown
  default/minor 14d, major 30d, patch 7d; groups `@medusajs/*`, next/react.
- Verification: YAML parses ×2; grep shows no `@v4` left.

### T3 — medusa-plugins `ci.yml` + `publish.yml`: v5 → v7, Node 20 → 22 (+ new `dependabot.yml`)

- Node 20 was removed from GitHub runner images on 2026-09-16; both workflows still pinned
  `node-version: '20'`.
- `checkout`/`setup-node` v5 → v7; node 20 → 22 (inside Medusa 2.19's engine range).
- `publish.yml` gained the **tag ↔ package version guard** from the blueprint (without it, a
  mistagged push would publish whatever version `package.json` has — package currently
  0.1.3; path verified). The 2-job OIDC publish restructure stays a blueprint for our own
  future plugin — this is the narisolutions repo; minimal divergence only.
- New `.github/dependabot.yml`: npm weekly + cooldown + `@medusajs/*` group, target-branch
  `develop` (branch exists); `github-actions` monthly.
- Verification: YAML parses ×2; no `@v5` / `'20'` left.

## What the tools contributed — and didn't

- **Code-graph tools are blind to the file type of these tasks.** `graft grep
  includeUpdaterJson` over medusa-pos returned **0 hits** while the string sits in
  `.github/workflows/release.yml:184` — neither tool indexes Actions YAML. The tasks were
  unblocked by plain grep, `raw.githubusercontent.com` verification and `git ls-remote`.
  Honest conclusion: for CI-YAML work the graph adds nothing today.
- **Corpora viability (the round's second question):**
  - **Markdown corpora are not indexable.** `.cache-pagarme` (178 files, 174 scraped portal
    pages): Graft parsed **1/178** (a Python sweep script), CodeGraph **1/178** (12 nodes).
    Same family expected for stone/cielo/getnet/sicoob/deep2/rede2. Verdict: ripgrep stays
    the corpora research tool; markdown corpora are **not** benchmark targets for code-graph
    tools.
  - **The code corpus is viable — and the heaviest real target so far.** `.cache-medusa-src`
    (sparse clone of `medusajs/medusa`, 3,672 ts/tsx files, ~16× the largest Round 1 target):

    | tool | build (s) | files | index (KB) | max RSS (MB) | query quality on a real lookup* |
    |---|---|---|---|---|---|
    | graft 0.20.0 | 167.0 | 3,672 / 3,672 parsed | 77,020 | 761 | **found it** — 4 hits / 2 symbols / 2 files, exact lines, tool-reported "tokens saved ≈ 6,725 (98%)" |
    | codegraph 1.6.0 | 34.0 | 3,676 indexed; **10,003 "could not be parsed" (73% of scanned)** | 115,536 | 966 | found the class, **missed the abstract method** |

    \* lookup: `getWebhookActionAndData` — the payment-provider webhook contract this
    workspace actually consults; confirmed present in 2 files by plain grep, so the miss is
    query/index quality, not missing data.
  - CodeGraph builds ~5× faster here, but silently drops most of the scanned universe while
    calling the index "fully usable", missed the method-level lookup, and used +27% RSS.
    Build-time comparison is directional only: the tools scan different file universes
    (Graft 3,672 code files; CodeGraph 13,679 scanned including json/md it then failed on).
- Disposition: Graft's medusa-src index **kept** (75 MB, research accelerator for plugin
  work); CodeGraph's **deleted**; markdown-corpus indices **deleted** (useless).
- Tool-reported token estimate recorded verbatim per house rule (§3) — no conversion.

## Discoveries that changed workspace docs (independent of the tools)

1. `latest.json` severity corrected: `uploadUpdaterJson` defaults to `true`, so the dead
   input never lost the updater feed (engenharia.md §4.1 fixed).
2. medusa-plugins CI was still on **Node 20** after the 2026-09-16 runner-image removal —
   bumped to 22.
3. medusa-plugins publish had **no tag ↔ package version guard** — added.

## Limitations

- n=1 operator; each task executed once; no no-tool baseline. This round measures "what
  working with the tools is like on real backlog", not "do the tools make the agent
  better/cheaper" — that controlled question is Round 3.
- The medusa-src corpus was a single-pair field test, not the full 5-round protocol; it is
  queued as a full target.
- Round 1's disk-free logging applies; indices left in place after Round 2 (graft on
  medusa-src) are intentional working state, not benchmark artifacts.
