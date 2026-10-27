# P4/P5: exploratory simulation diagnostics

*27 Oct 2026. Inputs: the frozen `results.json` (`716862ab…`) and `paths.npz` (`0055f1e1…`) of `production_20261014T060921_145897`, read only. Script: `scripts/p45_diagnostics.py` (SHA-256 `f9808c11…`), run on HEAD `8ef46aa`. Outputs: `results/derived/p45_diagnostics/`, with full-precision `p45_summary.json`, `p45_tables.md` and `fig_rl_survival.png`.*

> **Status.** Everything here is **exploratory, post hoc and descriptive**:
> - It does not change the primary estimates, CIs or the P2 inference.
> - It gives no p-values and no significance flags.
> - Associations are not causal, and nothing is used to retune any model.
>
> All results are at λ = 0.1.

## P4: RF − GARCH between-system heterogeneity

The outcome y_r(δ) is the RF − GARCH paired RMD₅₀₀ of fitted system r, in days. A negative value means RF is faster. It was recomputed from `paths.npz` and equals the stored values exactly.

**Table P4a. Heterogeneity.** Cochran's Q and I² are descriptive indices only. The w_r are conditional Monte Carlo SEs, so no meta-analytic inference is implied.

| δ | Mean | s_b | RMS MC SE | s_b / MC SE | σ̂_sys | Q | I² | Signs +/− |
|---|---|---|---|---|---|---|---|---|
| 1 | +0.27 | 3.24 | 2.61 | 1.24 | 1.92 | 27.1 | 0.30 | 9/11 |
| 1.5 | −6.05 | 9.45 | 2.79 | 3.39 | 9.03 | 212.0 | 0.91 | 6/14 |
| 2 | −9.94 | 15.25 | 2.76 | 5.53 | 15.00 | 550.3 | 0.97 | 5/15 |
| 3 | −13.13 | 20.82 | 2.55 | 8.17 | 20.66 | 1163.6 | 0.98 | 6/14 |

**Stability of the system effects** (Spearman ρ over the same 20 systems):
- across shift sizes: δ 1.5 against 2, +0.86; δ 2 against 3, +0.95; δ 1.5 against 3, +0.85
- across smoothing constants at a given δ: λ 0.1 against 0.2, +0.89 / +0.94 / +0.97

**Table P4c. Exploratory associations.** Spearman ρ with y_r(δ). The predictors were fixed in advance; the values are descriptive, with no p-values.

| Predictor | Range over systems | δ = 1.5 | δ = 2 | δ = 3 |
|---|---|---|---|---|
| Masking gap M_RF − M_GARCH (same δ) | −0.028 to 0.325 | −0.80 | −0.89 | −0.89 |
| Validation P(T < τ), RF − GARCH | −0.0015 to 0.023 | −0.72 | −0.64 | −0.68 |
| RF responsiveness `slope_h` | 0.168 to 0.69 | +0.59 | +0.66 | +0.70 |
| QLIKE_true(RF) − QLIKE_true(GARCH) | 0.015 to 0.047 | −0.58 | −0.55 | −0.61 |
| Validated ARL₀ relative deviation, RF − GARCH | −0.057 to 0.030 | +0.42 | +0.22 | +0.15 |
| GARCH persistence α̂ + β̂ | 0.960 to 0.992 | −0.12 | −0.18 | −0.20 |

**Table P4d. Selected RF cell** (categorical): group size and mean y_r(δ), in days.

| Cell (min leaf, max features) | n | δ = 1.5 | δ = 2 | δ = 3 |
|---|---|---|---|---|
| 200, 3 | 8 | −4.1 | −9.4 | −13.7 |
| 50, 1 | 6 | −6.0 | −10.9 | −12.4 |
| 50, 3 | 4 | −8.4 | −8.6 | −14.3 |
| 200, 1 | 2 | −9.4 | −11.7 | −10.5 |

**Findings.**
1. **Heterogeneity dominates after a change.**
   - With no change, between-system spread is close to the Monte Carlo noise: s_b/MC SE = 1.24, I² = 0.30.
   - Under a change it is 3.4–8.2 times the Monte Carlo SE (I² 0.91–0.98), and it grows with δ.
2. **The variation belongs to the fitted system, not to the paths.** A system's RF − GARCH effect is very stable across δ and across λ (ρ 0.85–0.97). Systems that favour RF at one shift size favour it at the others.
3. **The strongest association is with the masking gap** (ρ −0.80 to −0.89). Systems in which the RF forecaster retains more of the shift than GARCH show a larger RF delay advantage.
   - RF responsiveness (slope; +0.59 to +0.70) and relative forecast accuracy (−0.55 to −0.61) point the same way. The RF advantage is larger when the fitted RF tracks the variance less closely and forecasts less accurately.
   - These three predictors measure related aspects of how strongly RF adapts, so they are not independent evidence.
4. **Early false alarms are also associated** (ρ −0.64 to −0.72). This is consistent with survivor conditioning (see P5), but it is not separated from the other predictors.
5. **Weak or no association** with validated ARL₀ deviation (+0.15 to +0.42) and with GARCH persistence (−0.12 to −0.20).
6. **No clear pattern by selected RF cell.** The groups are small (8/6/4/2) and their means overlap.

**Interpretation.**
- The RF − GARCH delay advantage varies between fitted systems by much more than the Monte Carlo noise.
- That variation is consistent with how much each fitted RF forecaster adapts to the new variance level: less adaptation, and poorer forecasting, go with faster detection.
- This is an association across 20 systems. It is consistent with the adaptation-masking account, but it does not show cause.
- It gives no basis for preferring RF hyperparameters, and none were changed.

## P5: why equal ARL₀ does not give equal pre-change false-alarm rates

**Two separate data sources:**
- **(a) Independent IC validation.** 2,000 paths per system, horizon 5,000, run length min(T, 5000). Only per-system summaries are stored. Per-path validation run lengths were **not** stored and are **not** reconstructed.
- **(b) The δ = 1 no-change paths of the separately generated out-of-control stream.** 2,000 per system, stored per path, truncated at day 549.

**Geometric benchmark.** For a geometric run length with mean A (p = 1/A), in the production indexing:
- T ∈ {1, 2, …}, and a pre-change alarm means T < τ, i.e. T ≤ 49: P = 1 − (1 − p)⁴⁹, which is 0.0934 at A = 500.
- Conditional on surviving to the change (T ≥ τ), memorylessness makes D = T − τ + 1 geometric. Then E[min(D, 500) | T ≥ τ] = A(1 − (1 − p)⁵⁰⁰), which is 316.2 at A = 500, and P(D > 500 | T ≥ τ) = (1 − p)⁵⁰⁰.
- These formulas were checked against brute-force sums over the exact probability function. In (b), the benchmark uses each system's own validated A.

**Table P5a. Independent validation summaries** (stored): replicate mean [95% t₁₉ CI].

| Chart | Validated ARL₀ | CV of run length | q10/A | q50/A | q90/A | P(T ≤ 250) | P(T < τ) |
|---|---|---|---|---|---|---|---|
| Conventional | 499.6 [491.6, 507.6] | 1.041 [1.031, 1.052] | 0.072 [0.070, 0.075] | 0.675 | 2.350 | 0.408 | 0.125 [0.123, 0.128] |
| GARCH | 501.3 [494.8, 507.7] | 1.005 [0.995, 1.014] | 0.104 [0.101, 0.106] | 0.687 | 2.326 | 0.396 | 0.096 [0.094, 0.099] |
| RF | 496.5 [487.9, 505.2] | 1.017 [1.010, 1.024] | 0.095 [0.093, 0.098] | 0.684 | 2.329 | 0.402 | 0.104 [0.101, 0.108] |
| Oracle (diagnostic) | 502.2 [497.2, 507.3] | 1.003 [0.996, 1.010] | 0.105 [0.102, 0.108] | 0.687 | 2.325 | 0.395 | 0.095 [0.092, 0.097] |
| Geometric, A = 500 | 500.0 | 0.999 | 0.106 | 0.694 | 2.302 | 0.394 | 0.093 |

The CV is SD/A, with SD = SE·√N recovered exactly from the stored SE (ddof = 1).

**Table P5b. δ = 1 out-of-control-stream paths.** Means with [95% t₁₉ CI].

| Chart | P(T < τ) | Geometric | RMD₅₀₀ given T ≥ τ | Geometric, given T ≥ τ | P(no alarm by day 549 ∣ T ≥ τ) | Geometric, given T ≥ τ |
|---|---|---|---|---|---|---|
| Conventional | 0.1250 [0.1212, 0.1288] | 0.0936 | 319.9 [317.0, 322.9] | 316.0 | 0.380 [0.373, 0.388] | 0.367 |
| GARCH | 0.0936 [0.0893, 0.0980] | 0.0933 | 316.0 [314.5, 317.6] | 316.5 | 0.371 [0.366, 0.376] | 0.368 |
| RF | 0.1015 [0.0973, 0.1058] | 0.0942 | 316.6 [315.0, 318.3] | 315.2 | 0.374 [0.368, 0.381] | 0.365 |
| Oracle | 0.0926 [0.0890, 0.0963] | 0.0931 | 316.3 [314.7, 317.8] | 316.8 | 0.372 [0.367, 0.376] | 0.369 |

**Paired on the same δ = 1 paths:**

| Pair | Difference in P(T < τ) [CI] | Mean \|E_a ∩ E_b\| | Paths excluded by exactly one chart |
|---|---|---|---|
| RF − GARCH | +0.0079 [0.0047, 0.0110] | 1,770 | 3.5% |
| RF − conventional | −0.0235 [−0.0278, −0.0192] | 1,682 | 9.1% |
| GARCH − conventional | −0.0314 [−0.0350, −0.0277] | 1,684 | 9.7% |

**Figure P5.** `fig_rl_survival.png` shows (a) the empirical survival P(no alarm by day t) for t ≤ 549, and (b) its departure from the geometric curve (A = 500), in percentage points. Both are equal-weight means over the 20 systems of the δ = 1 out-of-control-stream paths, at λ = 0.1. Suggested caption: *"In-control survival of the four EWMA schemes on the no-change paths, with the geometric benchmark for ARL₀ = 500. The conventional chart has the same mean run length but about 3 percentage points more alarms by the change point (day 49)."*

**Findings.**
1. **Same mean, different shape.**
   - All four charts have validated ARL₀ ≈ 500, but their run-length distributions differ.
   - GARCH and the oracle are close to geometric: CV ≈ 1.00, q10/A ≈ 0.104 against 0.106, P(T < τ) ≈ 0.095.
   - The conventional chart is over-dispersed (CV 1.041), with many more early alarms (q10/A 0.072; P(T < τ) 0.125, against 0.093 geometric). It offsets this with a slightly heavier upper tail (q90/A 2.35).
   - RF lies in between (CV 1.017; P(T < τ) 0.104).
2. **The two independent data sources agree.** The δ = 1 out-of-control paths reproduce the validation pattern. In Figure P5 the conventional survival curve falls 3.2 percentage points below geometric by day 49, then converges back by day 549. RF reaches about −0.8 points.
3. **Survivor conditioning is not neutral.**
   - Conventional-chart survivors, the paths with no alarm before τ, go on to alarm later than a memoryless chart would: RMD 319.9 against the geometric 316.0, and P(no alarm by 549) 0.380 against 0.367. RF shows a smaller version (316.6 against 315.2).
   - Conditioning on T ≥ τ selects different, calmer paths for different charts. About 9% of paths are excluded by exactly one chart in RF − conventional comparisons, against 3.5% for RF − GARCH.
4. **What this means for the paired endpoints.**
   - The non-zero δ = 1 RF − conventional RMD baseline (−3.80 days) is consistent with this mechanism. Conventional survivors start with a later no-change alarm time.
   - RF − conventional RMD contrasts at δ > 1 should therefore be read against that baseline. The conclusion is unaffected, because the contrasts are +37.5 to +63.6 days.
   - The RF − GARCH baseline is about 0 (+0.27), because both are near-geometric.
   - The X(k) endpoints are baseline-adjusted by construction.
5. **Plausible contributors** (consistent with the evidence, not shown to be causes):
   - Dependence in the conventional score: ACF₁ of u is 0.13, against about 0 for GARCH and 0.01 for RF.
   - Volatility clustering that a constant denominator cannot absorb. High-volatility stretches can produce runs of large u and clustered early alarms.

## Limitations

- Per-path validation run lengths are not stored. The full in-control distribution beyond day 549 is known only through the stored mean, SD, quantiles and P(T ≤ 250).
- The δ = 1 out-of-control-stream paths are a different in-control sample, truncated at 549.
- The analysis covers λ = 0.1 only. λ = 0.2 enters only the P4 stability check.
- With R = 20, the Spearman correlations are imprecise and the predictors are correlated with one another.
- Q and I² use conditional SEs and are descriptive only.
- Validation quantiles use linear interpolation, while the geometric quantiles are discrete, so the comparison is approximate to about 1 day.

## Verification

- **Checks: 25/25 passed.**
  - Hashes of both inputs and the P1 verdict.
  - y_r at all four δ recomputed from `paths.npz` equal the stored values exactly, and s_b equals the stored value.
  - Per-chart P(T < τ), RMD and survivor censoring at δ = 1 recomputed equal the stored `ooc` values.
  - |E_a ∩ E_b| equals the stored paired n.
  - Validation N = 2,000 and the stored relative deviation are consistent.
  - One selected RF cell per system, and no project imports.
- **Self-test (hand-computed or brute-force):**
  - the geometric P(T < τ), conditional restricted mean and conditional censoring against exact sums
  - the restricted validation moments against a 400,000-draw synthetic sample
  - Cochran's Q and I² on worked examples
  - Spearman with ties, √0.9
  - the survival coding (T = 550 meaning no alarm by day 549)
- **Integrity:** all 17 production files unchanged, `pytest -q` 85 passed, and the figure inspected at rendered resolution with no clipping or label collisions.

Reproduce:

```bash
.venv/bin/python -I scripts/p45_diagnostics.py --selftest
.venv/bin/python -I scripts/p45_diagnostics.py   # refuses to overwrite results/derived/p45_diagnostics
```

## Report-ready paragraphs

*Heterogeneity (Results §4.1).* "The RF − GARCH difference in restricted mean delay varied across the 20 independently fitted systems far more than within-system Monte Carlo error: the between-system SD was 3–8 times the Monte Carlo SE under a change, against 1.2 times with no change. Each system's effect was stable across shift sizes and smoothing constants (Spearman ρ 0.85–0.97). In an exploratory, post hoc analysis, larger RF advantages were associated with fitted RF forecasters that retained more of the shift (masking gap, ρ ≈ −0.8 to −0.9), responded less to the true variance, and forecast less accurately than GARCH. This is consistent with an accuracy–detection trade-off, but it is an association, not a demonstrated cause."

*Run-length shape (Results §4.2).* "Calibrating all charts to ARL₀ = 500 equalized the mean in-control run length but not its distribution. The GARCH-standardized charts had near-geometric run lengths (coefficient of variation ≈ 1.00), while the conventional chart was over-dispersed (1.04) and had more early false alarms (P(T < 50) = 0.125, against 0.093 for a geometric run length). Because the paired detection endpoints condition on no alarm before the change, the surviving paths differ between charts. This is consistent with the RF − conventional delay contrast being non-zero (−3.8 days) even without a change, and it is why X(k), which subtracts the no-change baseline, is the cleaner comparison of early detection."
