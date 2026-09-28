# Round summary

All cold rounds are committed (`rounds.json` per pair) — nothing dropped. Per
METHODOLOGY.md §4: speed claims need ≥20% median delta and non-overlapping IQR; otherwise
report parity.

| repo | tool | ver | rounds ok | wall med (s) | min–max | σ | cpu med (s) | RSS peak (MB) | index (KB) | files | nodes | edges | warm (s) | mutation (s) | query med (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| medusa-plugins | codegraph | 1.6.0 | 5/5 | 5.82 | 4.798–5.893 | 0.55 | 4.46 | 171.8 | 280 | 14 | 55 | 77 | 1.654 | 3.792 | 1.759 |
| medusa-plugins | graft | 0.20.0 | 5/5 | 3.11 | 2.495–3.374 | 0.33 | 2.48 | 83.8 | 93 | 11 | 27 | 44 | 2.904 | 3.924 | 2.112 |
| medusa-pos | codegraph | 1.6.0 | 5/5 | 9.27 | 8.727–11.037 | 0.88 | 10.47 | 231.8 | 7992 | 231 | 2628 | 6758 | 2.01 | 3.149 | 1.816 |
| medusa-pos | graft | 0.20.0 | 5/5 | 15.48 | 14.277–18.78 | 1.77 | 14.31 | 190.4 | 4365 | 223 | 1018 | 2810 | 3.482 | 3.446 | 2.217 |
| store-b2c-boilerplate | codegraph | 1.6.0 | 5/5 | 9.22 | 8.248–9.96 | 0.7 | 10.09 | 225.3 | 7768 | 296 | 2558 | 5092 | 1.857 | 3.291 | 2.059 |
| store-b2c-boilerplate | graft | 0.20.0 | 5/5 | 15.9 | 13.441–16.986 | 1.34 | 12.75 | 170.7 | 4305 | 288 | 875 | 1950 | 2.946 | 3.333 | 2.066 |
