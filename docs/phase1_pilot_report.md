# Phase 1 Completion Report — Planning, Implementation, Tests, Pilot

*13 Oct 2026. Covers the Phase 1 scope authorised by the student. No production simulation and no SPY download has been run.*

**Reference run:** `results/runs/pilot_20261013T075339_142070`, launched with `scripts/run_simulation.sh pilot` (git-ignored; deterministic, so it can be regenerated).

**Results SHA-256 (excluding timing):** `f92f07159b682406ef0ca8bd52c0e64e8eed38a795784b7ec8e9549c17b01bb7`. The same hash was obtained in three separate pilot runs.

All numbers below come from that run's `results.json` / `tables.md`. They are based on **one training replicate** and 300 paths per role, so they are pilot evidence, not production results.

**Revised 14 Oct 2026 after an independent audit.** No numerical result was changed and the pilot was not rerun. Interpretations, labels and units were corrected (§14). **Further errata A1, A3, A4 and A5 (14 Oct 2026, Phase 2 preparation)** add the two diagnostic validation rows, label the conventional M as "1 by construction", state why M has no SE, and add excess-detection point estimates derived exactly from stored values (§14); again no rerun.

**Source provenance.** The pilot was generated from **uncommitted** working-tree source: `provenance.txt` records HEAD `2a06da8` with `git_worktree_dirty: yes`, and `src/` and `run.py` were untracked at the time. The source was then modified by the audit remediation (§14). Only one change affects numerical output: the `slope_h` diagnostic now uses one normalisation for covariance and variance, which multiplies it by (n−1)/n = 1 − 1.1×10⁻⁶. A rerun of `pilot` with the remediated code is therefore expected to give a different results hash than `f92f0715…`. This expectation comes from code inspection and was confirmed at smoke scale; the pilot itself was not rerun. *(Note, 14 Oct 2026, Phase 2: this paragraph describes the Phase 1 remediation only. The Phase 2 source also changes output schemas, aggregation, paired intervals and reporting, so the current code differs from the pilot source by more than the slope normalisation.)*

---

## 1. What was delivered

| Item | Files |
|---|---|
| Planning documents | `docs/research_plan.md`, `docs/methodology.md` (equations 1–22, labelled [E]/[L]/[P]/[D]), `docs/references.md` (10 references with evidence status) |
| Simulation | `src/sim.py`: GARCH(1,1)-t simulator, constraint checks, scale fault (eq. 6) |
| Forecasters | `src/forecast.py`: HAR features, frozen GARCH-t fit and filter, frozen RF with floor, QLIKE/MSE |
| Chart | `src/chart.py`: EWMA, censored run lengths, bisection calibration, validation, delays, masking metrics, Brook–Evans ARL |
| SPY | `src/spy.py`: snapshot download with SHA-256, log returns, chronological split. **Code only; not executed** |
| Reporting | `src/report.py`: 7 tables, 2 figures |
| Driver | `run.py`: `smoke`, `pilot`, `production` (refuses until approved), `verify` |
| Wrapper | `scripts/run_simulation.sh`: GNU time, logs, exit status, provenance, thread limits, read-only Git |
| Tests | `tests/test_core.py` (29 tests), `pytest.ini` |
| Other | `src/__init__.py`; `.gitignore` gains `results/runs/` |

Implementation size: about 870 lines of Python in `src/` and `run.py`, plus 243 lines of tests.

## 2. Literature verification (Zotero)

- **Collection.** `STC-720-lib` holds 10 records with no duplicates.
- **Schipper & Schmid (2001).** The PDF is a scan with no text layer, so Zotero's full-text index returns 404. All 12 pages were read from rendered images. It confirms that our fault model is their eq. 3, and that our GARCH–EWMA is their residual chart (§3.5).
- **Patton (2011).** Full text read.
- **Christensen et al. (2023).** Full text read, but the Zotero attachment is the arXiv preprint, not the typeset journal version.
- **MacGregor & Harris (1993) and Lu & Reynolds (1999).** Marked metadata-only. No equations, results or conclusions are attributed to them.

## 3. Scientific-correctness checks

| Check | Result |
|---|---|
| Unit tests | `pytest -q`: **29 passed** (≈3.5 s) |
| No look-ahead | Perturbing $r_{t_0},\dots$ leaves features and $\hat h$ up to $t_0$ bit-identical (3 cut points) |
| Frozen models | Forest leaf values hashed before and after monitoring are identical; GARCH θ̂ unchanged (asserted in every run) |
| EWMA recursion | Matches the closed-form weighted sum (rtol 1e-12) |
| Run-length conventions | Hand-built cases for alarm time, censoring, pre-change false alarm, and $D=T-\tau+1$ |
| Calibration machinery | iid χ²₁ input: calibrated h* gives Brook–Evans ARL within 3% of the target; independent validation passes |
| Constraints | Positivity, stationarity, ν > 4 and the 4th-moment margin are all detected when violated; the GARCH fit is checked after every estimate |
| Scale fault | Equals GARCH(δω, α, β) on observed returns after the change (eq. 6, tested) |
| RF prediction | Matches scikit-learn's `predict`. It is a convex combination of training targets, so always positive. It is deterministic across thread counts. The floor is counted |
| Reproducibility | `run.py verify`: identical smoke hashes. The pilot was run three times with the identical hash `f92f0715…` (same machine and environment; nothing is claimed beyond this) |

**Two design flaws found by the smoke test and fixed before the pilot:**
1. The diagnostic "oracle" first used the *true post-change* variance as its denominator. That makes its score blind to the change by construction. It now uses the GARCH filter with the true in-control parameters, known and frozen (methodology §5).
2. The masking ratio first used an unpaired in-control mean and was noisy: the conventional chart gave M = 0.55 where theory says exactly 1. It now uses the CRN no-change counterfactual of the same paths (eq. 19), and the conventional chart gives M = 1.000 exactly.

**Two wrapper bugs fixed:**
- A brace in the usage message corrupted the mode argument. This incidentally verified the failure path: logs were preserved and the status passed through.
- `nproc` reported 1 because of `OMP_NUM_THREADS=1`; it is now `nproc --all` = 20.

## 4. Pilot configuration

| Element | Setting |
|---|---|
| DGP | GARCH(1,1)-t: ω = 0.02, α = 0.07, β = 0.91, ν = 6 (σ² = 1; persistence 0.98; 4th-moment coefficient 0.985) |
| Training / development | n = 3,500 each |
| RF | 100 trees; grid `min_samples_leaf` {50, 200, 800} × `max_features` {1, 3} |
| Calibration / validation | 300 + 300 in-control paths, T_max = 3,000 |
| Out-of-control | 300 CRN paths, τ = 50, H = 500, δ ∈ {1 (no change), 1.5, 2, 3} |
| λ | {0.1, 0.2} |
| Target ARL₀ | 500 |
| Master seed | 20261013 |

## 5. Statistical diagnostics

**Fitted forecasters (training path):**
- GARCH-t: ω̂ = 0.017, α̂ = 0.071, β̂ = 0.910, ν̂ = 7.6; not near the boundary.
- RF selected `min_samples_leaf` = 200, `max_features` = 1. The development QLIKE spread across the grid was 0.781–0.802.
- The training s² = 0.886 underestimates σ² = 1. This is a realistic consequence of heavy-tailed, persistent data.

**Forecast accuracy and scores on independent validation paths (900,000 forecasts per forecaster = 300 paths × 3,000 days):**

| Forecaster | QLIKE vs h | Gap closed G | corr(d, h) | slope d on h | mean u | ACF₁ u | u q99 / max |
|---|---|---|---|---|---|---|---|
| Constant (s²) | 1.003 | – | – | – | 1.122 | 0.130 | 12.0 / 632 |
| GARCH-t (fitted) | 0.811 | 0.995 | 1.000 | 1.018 | 1.035 | −0.002 | 9.5 / 341 |
| RF | 0.835 | **0.868** | 0.684 | **0.345** | 1.024 | 0.012 | 9.6 / 352 |
| GARCH, true params (diag.) | 0.810 | – | 1.000 | 1.000 | 0.999 | 0.000 | 9.1 / 333 |

The RF floor never binds (0 of 900,000 forecasts).

Ranking: oracle < GARCH < RF < constant, as expected from **H1**. The RF forecasts are positive and calibrated on average (mean u = 1.024), but they vary much less than proportionally with the true variance (slope 0.345, correlation 0.684). **Reduced responsiveness is observed; its cause has not been isolated.** A slope below 1 is not by itself evidence of estimation error. Even the exact conditional expectation $E[h_t\mid x_t]$ given the three HAR features has slope $\operatorname{var}(E[h_t\mid x_t])/\operatorname{var}(h_t)<1$ unless $h_t$ is a function of $x_t$ (methodology §9). The value may therefore reflect limited predictor information as well as estimation, regularization (large leaves, bootstrap averaging) or saturation (no extrapolation beyond training leaf means).

*Slope normalisation erratum.* The pilot's `slope_h` divided a covariance with ddof = 1 by a variance with ddof = 0, which inflates every slope by n/(n−1) = 1 + 1.1×10⁻⁶ for n = 900,000. This is why the diagnostic shows 1.0000011 instead of exactly 1. The error is immaterial at the reported precision and has been fixed in code (`forecast.slope`).

The conventional score keeps clear dependence (ACF₁ = 0.13, from volatility clustering). The standardized scores are close to uncorrelated. All scores are very heavy-tailed.

## 6. Calibration and independent validation (H2)

| λ | Chart | h* | Validated ARL₀ (restricted) | 95% CI | Censored | P(T<50) | Pass |
|---|---|---|---|---|---|---|---|
| 0.1 | Conventional | 3.468 | 497.9 | [441.8, 554.0] | 0.0% | 0.147 | yes |
| 0.1 | GARCH | 2.936 | 508.9 | [451.1, 566.6] | 0.0% | 0.120 | yes |
| 0.1 | RF | 2.785 | 481.6 | [428.2, 535.0] | 0.0% | 0.140 | yes |
| 0.2 | Conventional | 5.134 | 467.2 | [416.3, 518.1] | 0.0% | 0.140 | yes |
| 0.2 | GARCH | 4.690 | 491.1 | [435.6, 546.7] | 0.0% | 0.117 | yes |
| 0.2 | RF | 4.427 | 469.0 | [415.9, 522.1] | 0.0% | 0.133 | yes |
| 0.1 | *GARCH, true params (diagnostic, not a competitor)* | 2.838 | 511.2 | [452.5, 569.9] | 0.0% | 0.120 | yes |
| 0.2 | *GARCH, true params (diagnostic, not a competitor)* | 4.476 | 472.7 | [418.1, 527.4] | 0.0% | 0.123 | yes |

- All **8** chart × λ configurations pass: **6 primary** (3 charts × 2 λ) and **2 diagnostic** (the known-parameter GARCH chart × 2 λ, italic rows; erratum A1, values read from the canonical `results.json`). Calibration censoring was 1 of 300 paths (0.33%) for the conventional chart at λ = 0.1 and 0 for every other configuration. Validation censoring was 0 throughout.
- **Independent theory check.** For the known-parameter chart (iid input), the Brook–Evans ARL at the calibrated h* is 508.0 (λ = 0.1) and 487.6 (λ = 0.2). The validation estimates are 511.2 and 472.7.
- **Run lengths are not geometric.** The median RL (311–348) is close to the geometric value of 347. However, early false alarms are more frequent: RL q10 is 34–44 against a geometric 53, and P(T < 50) is 0.12–0.15 against 0.093. Matching ARL₀ does not equalise early false alarms. The conventional chart has the most early alarms.

## 7. Out-of-control detection (λ = 0.1; delays restricted to H = 500)

**Two different path populations.** Each chart's summaries below are over its **own** evaluable paths $E_k=\{i:T_i\ge\tau\}$, with no pre-change false alarm: 267 conventional, 279 GARCH, 273 RF and 280 diagnostic (λ = 0.1). These sets are identical across δ (CRN) but differ between charts. The paired contrasts further below are over the **pairwise intersections** $E_a\cap E_b$: 271 paths for RF and GARCH, 262 for RF and conventional, 262 for GARCH and conventional. A paired contrast therefore need not equal the difference of the per-chart means.

| δ | Conventional mean D_H (median) | RF | GARCH | GARCH true params | No-change baseline P(D≤20) |
|---|---|---|---|---|---|
| 1 (no change) | 321 (385) | 303 (315) | 307 (324) | 304 (320) | 0.045–0.054 |
| 1.5 | 201 (171) | 228 (186) | 245 (214) | 237 (204) | |
| 2 | 134 (94) | 183 (137) | 211 (158) | 200 (143) | |
| 3 | 72 (37) | 113 (68) | 146 (93) | 137 (82) | |

**Paired contrasts in restricted mean delay** (mean over $E_a\cap E_b$ of $D_H^{a}-D_H^{b}$; CRN paths; percentile-bootstrap 95% CI over paths, B = 2,000; λ = 0.1):

| δ | RF − GARCH (n = 271) | RF − Conventional (n = 262) |
|---|---|---|
| 1 (no change) | −3.5 [−14.4, 8.3] | −14.3 [−34.9, 5.9] |
| 1.5 | −15.6 [−27.7, −3.5] | +29.0 [12.4, 47.3] |
| 2 | −28.4 [−42.8, −13.8] | +53.9 [38.3, 70.7] |
| 3 | −34.4 [−48.8, −20.8] | +43.0 [30.7, 55.4] |

- **These are paired restricted-mean contrasts, not differences in medians.** For example, the −28.4-day RF − GARCH contrast at δ = 2 is the mean paired difference in $D_{500}$ over 271 paths. The medians differ by 137 − 158 = −21 days, and the per-chart restricted means (183.5 and 211.3) are over 273 and 279 paths respectively.
- **The δ = 1 row is the no-change baseline of each contrast.** It was computed in the pilot (`results.json`) but omitted from the original `tables.md`. Without a change, restricted delays already differ between charts: −3.5 (RF − GARCH) and −14.3 (RF − conventional), both with CIs that include 0. Such differences can arise from the charts' different non-geometric in-control run-length distributions after conditioning on $T\ge\tau$, as well as from Monte Carlo noise. Each contrast should be read against its δ = 1 counterpart. At λ = 0.2 the δ = 1 contrasts are −5.9 [−19.2, 8.2] and +1.1 [−19.6, 23.7], and the δ > 1 ordering is the same as at λ = 0.1. Full tables are in the run's `tables.md`.
- **Inferential scope.** These intervals are Monte Carlo intervals **conditional on one trained system**: one fitted GARCH θ̂, one RF, one s², and the h* calibrated on 300 paths. They exclude three sources of uncertainty:
  1. **Training variability.** A different training path gives different forecasters, and possibly different contrasts. This pilot has one replicate, so this variation is unmeasured.
  2. **Calibration uncertainty.** h* is an estimate, and the charts are matched to ARL₀ = 500 only within calibration error: validated ARL₀ ranges from 482 to 509 at λ = 0.1, with 95% CIs of about ±11%. The delay comparison treats h* as fixed.
  3. **Multiple comparisons.** Twenty-four contrast intervals are reported (3 contrasts × 4 δ × 2 λ) without adjustment. They are correlated through shared paths, and their joint coverage is below 95%.

  A CI that excludes 0 shows only that the difference is not Monte Carlo noise **for this trained system**. It is not a method-level significance claim.

- **Baseline-adjusted excess detection X̂(k) (erratum A5).** $\hat X(k)=\hat P(D(\delta)\le k)-\hat P(D(1)\le k)$ on the same paths (methodology eq. 24). By CRN each chart's evaluable set is identical across δ, so the paired mean equals this difference exactly, and the values below are **derived from the stored P(D≤k)** of the canonical `results.json` (no rerun). **Their SEs are not available**: they need the per-path indicators, which the pilot did not store. λ = 0.1; X(5) / X(20) / X(60):

  | δ | Conventional | GARCH | RF | *GARCH true params (diagnostic)* |
  |---|---|---|---|---|
  | 1.5 | 0.019 / 0.049 / 0.124 | 0.022 / 0.050 / 0.082 | 0.018 / 0.066 / 0.099 | 0.018 / 0.043 / 0.089 |
  | 2 | 0.030 / 0.105 / 0.236 | 0.047 / 0.097 / 0.143 | 0.033 / 0.114 / 0.158 | 0.050 / 0.107 / 0.164 |
  | 3 | 0.075 / 0.266 / 0.498 | 0.093 / 0.197 / 0.283 | 0.084 / 0.220 / 0.337 | 0.100 / 0.221 / 0.311 |

  The no-change baselines P(D(1) ≤ 5 / 20 / 60) are 0.011 / 0.045 / 0.120 (conventional), 0.014 / 0.054 / 0.129 (GARCH) and 0.015 / 0.048 / 0.132 (RF). At δ = 3, X̂(20) is 0.197–0.266 across the three primary charts. These are single-replicate point estimates without uncertainty and support no ranking.
- **Initial sensitivity.** At δ = 3, λ = 0.1, P(D ≤ 5) is 0.086 (conventional), 0.108 (GARCH) and 0.099 (RF). The no-change baseline is about 0.011–0.015. These chart differences lie within sampling error (SE ≈ 0.018). P(D ≤ 20) favours the conventional chart: 0.311, against 0.251 (GARCH) and 0.267 (RF).
- **Detection is slow overall.** At ARL₀ = 500, doubling the variance takes a median of 94–158 trading days to detect.

## 8. Adaptation masking (RQ3, H3)

| δ | Conventional M | GARCH M (theory) | RF M | GARCH true-param M (theory) |
|---|---|---|---|---|
| 1.5 | 1 (by construction) | 0.200 (0.137) | 0.384 | 0.226 (0.160) |
| 2 | 1 (by construction) | 0.160 (0.106) | 0.353 | 0.182 (0.125) |
| 3 | 1 (by construction) | 0.114 (0.073) | 0.336 | 0.132 (0.087) |

*Errata A3 and A4.* The conventional chart's M = 1 is **algebraic, not a finding**: its denominator is fixed and the fault is multiplicative, so $u_t(\delta)=\delta u_t(1)$ path by path (stored value 1.000; it is an exactness check, now also a unit test). **The M values carry no standard errors**: the delta-method SE (methodology eq. 26) needs per-path window means at δ and at δ = 1, which the pilot stored only as pooled means. They cannot be obtained from the stored outputs without a rerun, which was not done; production computes them.

- **Transient confirmed.** At k = 0 the paired score ratio equals δ exactly for every chart, because every denominator is $\mathcal F_{\tau-1}$-measurable. The GARCH ratio then decays: at δ = 2 it is 1.92, 1.78, 1.58, 1.43 and 1.23 at k = 1, 2, 5, 10, 20, reaching about 1.16 by k ≈ 50 (`fig_profile.png`).
- **First-order theory (eq. 20)** reproduces the pattern (M ≪ 1 and decreasing in δ). It **underestimates the level by about 30–35%**, which fits Jensen's inequality for a ratio-of-means approximation. It should be presented as an approximation.
- **Sustained alarm occupancy** (fraction of days with Z > h* in days 100–499, δ = 3, λ = 0.1):

  | Chart | δ = 3 | No-change baseline |
  |---|---|---|
  | Conventional | 0.295 | 0.042 |
  | RF | 0.112 | 0.018 |
  | GARCH | 0.018 | 0.009 |

- **The RF retains about 34–38% of the shift** (M = 0.384, 0.353 and 0.336 for δ = 1.5, 2 and 3), against 11–20% for the fitted GARCH. Together with the in-control slope of 0.345, this shows that the RF forecasts respond less than proportionally to volatility changes. **The cause is not isolated.** Limited predictor information (three HAR features), estimation and regularization (large leaves, bootstrap averaging), and saturation (no extrapolation beyond training leaf means) could each contribute. This pilot contains no experiment that separates them.

## 9. Interpretation (pilot-level, one training replicate)

1. **H1 and H2 are supported.** The RF forecasts sensibly but is worse than the correctly specified GARCH. All charts can be calibrated and validated to a common ARL₀.
2. **H3 is supported qualitatively.** The adaptive charts lose most of a persistent shift within about 30–50 days. Masking is severe for GARCH (M ≈ 0.11–0.20) and partial for the RF (M ≈ 0.34–0.38).
3. **H4.** The design has a change at the fixed monitoring day τ = 50, after a start at Z₀ = 1, with delays conditional on no alarm before τ. It is not a steady-state design. Other settings: ARL₀ = 500, t₆ innovations, estimated parameters. In this design and this replicate, the **non-adaptive conventional EWMA had the shortest restricted mean delays** for persistent scale increases.
   - The RF chart's restricted mean delay was shorter than the GARCH chart's. The paired RF − GARCH contrasts were −15.6, −28.4 and −34.4 days at δ = 1.5, 2 and 3, and their 95% Monte Carlo CIs exclude 0. The no-change contrast was −3.5 [−14.4, 8.3].
   - This is **conditional on one fitted model per chart and its calibrated limit** (§7, inferential scope). It is not yet a method-level finding.
   - This ordering is the reverse of Schipper & Schmid (2001), who found the residual chart best. Their setting differs: ARL₀ = 60, change at t = 1, known parameters, normal innovations, and per-chart λ minimisation up to λ = 1.
   - A plausible but **untested** explanation: at a low ARL₀ the threshold can be crossed during the transient, whereas at ARL₀ = 500 the sustained (unmasked) signal dominates.
4. **Caution for the article.** The RF chart detected faster than the GARCH chart although its forecasts are less accurate (QLIKE 0.835 against 0.811), so the advantage is **not explained by better variance forecasting**.
   - The advantage coincides with the RF's reduced responsiveness (slope 0.345) and its higher retained shift (M ≈ 0.34–0.38 against 0.11–0.20), which make it behave partly like the non-adaptive conventional chart.
   - This association is observed in one replicate; the causal mechanism has not been isolated (§8).
   - Better monitoring ≠ better forecasting. This must be stated explicitly.

## 10. Measured runtime and resources (final pilot run)

| Measure | Value |
|---|---|
| Wall clock (GNU time) | **4.10 s** |
| In-process total | 2.42 s |
| CPU time | 7.02 s user + 0.48 s system |
| CPU utilisation | 182% |
| Peak RSS | **364,856 KiB** (≈ 356.3 MiB ≈ 373.6 MB). GNU time reports "Maximum resident set size (kbytes)" in KiB |
| Machine | 20 logical CPUs; 7,938,636 KiB RAM (≈ 7.57 GiB ≈ 8.13 GB) (WSL2) |

Main in-process stages (wall time):
- RF grid fit (6 × 100 trees): 0.66 s
- RF prediction (calibration and validation): 0.25 + 0.23 s
- RF prediction (out-of-control): 0.46 s
- Calibration bisection (8 combinations): 0.16 s
- Simulation: under 0.1 s per role

All pilot criteria are met:

| Q | Status |
|---|---|
| Q1 | G = 0.868 ≥ 0.5; mean u_RF = 1.024; floor binds 0% |
| Q2 | No NaN/inf; reproducible |
| Q3 | Censoring < 1%; all validations pass |
| Q4 | Delays decrease in δ; masking computed and compared with theory |
| Q5 | Paired CIs computed |
| Q6 | 4.1 s, 356.3 MiB peak RSS |

## 11. Unresolved issues and risks

1. **Single training replicate.** Every out-of-control conclusion is conditional on one fitted GARCH, one RF, one s² and the calibrated h*. The CIs exclude training variability and calibration uncertainty and are not adjusted for multiplicity (§7). Production needs replicates.
2. **Pre-change false alarms.** In the out-of-control set, P(T < τ) (0.07–0.11) is lower than the validation P(T < 50) (0.12–0.15) for every chart, by about 1.4–1.9 SE. The charts share paths, so the deviations are correlated; this is probably sampling noise. Recheck at production scale.
3. **Masking theory** (eq. 20) underestimates M by about one third. It will be reported as an approximation; a higher-order correction is not planned.
4. **The conventional chart's reference variance** comes from one training path (s² = 0.886σ²). Replicates will show how much this moves h* and the delays.
5. **Robustness of H4 to ARL₀ and change timing is untested.** This is needed to interpret the contrast with Schipper & Schmid (2001).
6. **SPY application not started.** No data downloaded; the SPY-training GARCH-t estimates (D1) are not yet available.
7. **`src/report.py` summarises replicate 0 only.** It must aggregate across replicates (per-replicate rows plus pooled values and between-replicate spread) before production.
8. **Two references are metadata-only** (MacGregor & Harris 1993; Lu & Reynolds 1999).
9. **Reproducibility** is demonstrated only on this machine and environment (Python 3.14.4, scikit-learn 1.9.1, NumPy 2.5.4).
10. **Source provenance.** The pilot was run from uncommitted source (see the note at the top), so no commit reproduces its hash exactly. A minimal fix for future runs is recorded in the production plan.

## 12. Proposed production configuration (requires approval)

> **Superseded (14 Oct 2026).** This proposal was replaced by the reviewed production-preparation plan, `.claude/skills/stc720-project/references/production-plan.md`. That plan sets:
> - R = 10 preferred, subject to a runtime benchmark
> - H = 500 rather than 1,000
> - the ARL₀ = 100 sensitivity as a separate secondary configuration
> - corrections C1–C7 before any production run
>
> §12 and §13 are kept below unchanged as a historical record. The current approval status is in `docs/project-status.md`.

| Element | Proposed | Rationale |
|---|---|---|
| Training replicates R | **5** | Captures variation across training samples; cost is negligible |
| Calibration / validation paths | **2,000 + 2,000**, T_max = 5,000 | SE of ARL₀ ≈ 2.2%; censoring ≈ 0 |
| Out-of-control paths | **2,000** per δ (CRN), τ = 50, **H = 1,000** | Paired CIs about 2.6× narrower; less censoring |
| δ | {1 (no change), 1.5, 2, 3} | as pilot |
| λ | 0.1 (primary), 0.2 | as pre-registered |
| RF trees | **500** | as Christensen et al. (2023); reduces forest Monte Carlo noise |
| RF grid | unchanged | pre-registered |

**Projected cost.** About 1–3 min per replicate, so roughly 10–15 min in total, with peak RSS around 1.5–2.5 GB. This is extrapolated from per-stage pilot timings (≈ 2.8 ns per row-tree for RF prediction with 16 threads) and is **not measured**. Arrays will be processed per chart if memory exceeds 4 GB.

**Code changes needed before production (routine):** replicate aggregation in the report, a `production` config entry, and per-chart memory release.

## 13. Decisions requested

- **P1.** Approve the production configuration above, or amend it.
- **P2.** *Optional* single sensitivity run to test the interpretation in §9.3: the same design at **ARL₀ = 100** (all else equal). Recommended because it is cheap and directly addresses the contrast with Schipper & Schmid. Approve or decline.
- **P3.** Approve the one-time SPY snapshot download (yfinance, 1993-01-29 → 2026-09-30) and the SPY application exactly as specified in methodology §11.
- Defaults D1–D3 (DGP values, ARL₀ = 500 / τ = 50 / λ, SPY partitions) were adopted as recommended in plan v2. Say if any should change.

## 14. Revision log

**14 Oct 2026: Phase 2 preparation errata (A1, A3, A4, A5).** No numerical result was changed and the pilot was not rerun; the canonical run directory is unchanged. The added numbers were read from, or derived arithmetically from, the unchanged `results.json`.

| Change | Section |
|---|---|
| A1: the two diagnostic (known-parameter GARCH) validation rows added and marked; "8 configurations = 6 primary + 2 diagnostic" | §6 |
| A3: conventional M labelled "1 (by construction)", an exactness check, not a finding | §8 |
| A4: M has no SE because per-path window means were not stored; production computes the delta-method SE | §8 |
| A5: X̂(k) point estimates, k = 5, 20, 60, derived exactly from stored P(D ≤ k) (identical evaluable sets across δ by CRN); SEs unavailable | §7 |

**14 Oct 2026: independent-audit remediation.** No numerical result was changed and the pilot was not rerun. Every number added here (the δ = 1 contrasts and the chart-specific n) was read from the unchanged `results.json`.

| Change | Section |
|---|---|
| Significance qualified as conditional on one trained system and its h*. Limitations stated: training variability, calibration uncertainty, multiplicity | §7, §9, §11 |
| Chart-specific evaluable sets distinguished from the pairwise intersections used for paired contrasts | §7 |
| −28.4 days labelled a paired restricted-mean contrast, not a difference in medians | §7, §9 |
| δ = 1 no-change paired contrasts added | §7 |
| RF slope: reduced responsiveness is observed but its cause is not isolated (limited information, estimation, regularization or saturation) | §5, §8, §9 |
| Forecast count corrected from 90,000 to 900,000; calibration censoring is 1/300 (0.33%), not "≤ 0.3%" | §5, §6 |
| Memory reported in KiB / MiB / MB | §10 |
| "Steady-state change" replaced by fixed change point τ = 50 | §9 |
| Slope normalisation erratum (ddof) and source-provenance note | header, §5, §11 |
| §12–§13 marked superseded | §12 |
| Code, not used by this pilot run: overwrite guard in `run.py`; `forecast.slope`; `report.py` Table 4, 6 and 7 labels, n eval and δ = 1 rows; `.gitignore` template in `setup.sh`. Tests went from 29 to 34, all passing | – |

