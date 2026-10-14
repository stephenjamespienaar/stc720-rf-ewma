# Production plan, required corrections and approval gates

This file is the persistent record of the **production-readiness review** (13 Oct 2026; verdict **CORRECTIONS REQUIRED**). The review was delivered in chat and is **not saved in `docs/`**. Production execution is **not authorized**.

*Updated 14 Oct 2026 (session 3): the user supplied the production-preparation prompt and approved the C1–C7 implementation plan with refinements. **C1–C7 are implemented and verified (uncommitted until the user commits)**; see the status table below and `docs/project-status.md`. Benchmark, production, sensitivity and SPY remain **not authorized**.*

*Revised 14 Oct 2026 (independent-audit remediation, Phase 1 baseline):*
- *The masking-SE and variance-decomposition formulas are corrected.*
- *C2 is clarified: the counterfactuals already exist; only per-path storage is pending.*
- *A-item status is recorded below.*
- *A source-provenance recommendation is added.*

*C1–C7 implemented 14 Oct 2026 (session 3); see "Implementation status". Committed by the user as `9b286e1`.*

*Updated 14 Oct 2026 (after the authorized benchmark): post-benchmark amendments A (R = 20) and B (equivalence-style IC validation, methodology eq. 29), the production failure-handling policy and the provenance classification are implemented and verified; see "Post-benchmark amendments". Production and sensitivity remain **not authorized**.*

## Review findings (errors and ambiguities)

| ID | Finding | Action |
|---|---|---|
| A1 | The pilot report says "8 configurations" but its table shows 6 (the 2 oracle diagnostics are omitted) | List all 8; mark the diagnostics |
| A2 | "Significantly faster" overstates conditional, single-replicate CIs | Reword; base method-level claims on replicates. **Pilot report reworded 14 Oct**; method-level claims still need replicates (C4) |
| A3 | Conventional M = 1 is presented as a finding | Label "= 1 by construction"; add as a unit test |
| A4 | M reported without uncertainty | Delta-method SE |
| A5 | Detection metrics not adjusted for the false-alarm baseline | Add the paired excess detection X(k) |
| A6 | Per-chart summaries use chart-specific evaluable sets; contrasts use pairwise intersections | Label both denominators. **Done 14 Oct** (pilot report §7, methodology §7, `report.py` Tables 4 and 6) |
| A7 | Restricted delays already differ between charts with no change | Report the δ = 1 contrast next to every contrast. **Done for the pilot report 14 Oct** |
| A8 | `report.py` Table 6 omits the δ = 1 contrasts, although they are computed | Include them. **Done 14 Oct** |
| A9 | Pilot OOC P(T<τ) (0.07–0.11) is below validation P(T<50) (0.12–0.15) | Recheck at N = 2,000 |
| A10 | `report.py` handles replicate 0 only | Corrections C2–C5 |
| A11 | SPY reference dates are cited as "pre-registered" but not listed anywhere | Write the list before any SPY output is viewed |
| A12 | SPY download: relies on the `multi_level_index` default; no integrity checks | Correction S1 |

## Production configuration

As stated by the user, 13 Oct 2026. **Execution is not authorized.**

| Parameter | Value | Status |
|---|---|---|
| Charts, DGP, fault, frozen models | as in scientific-design.md | Approved |
| ARL₀, λ, τ, δ | 500; 0.1 (primary) / 0.2; 50; {1.5, 2, 3}, plus δ = 1 counterfactual | Approved primary simulation |
| Training replicates R | **20** (production and the matched sensitivity; benchmark R = 1) | Approved 14 Oct 2026 after the benchmark (amendment A); was 10 |
| Calibration / validation paths | 2,000 + 2,000 per replicate, shared across chart × λ | Recommended |
| OOC paths | 2,000 per replicate, reused across δ (CRN) | Recommended |
| In-control horizon T_max | 5,000 (3,000 would suffice) | Recommended |
| OOC horizon H | **500** (not 1,000: later alarms are dominated by false alarms, and the cost halves) | Recommended |
| RF trees | 500 (pilot used 100; not pilot-tested) | Recommended |
| n_train / n_dev / burn / W | 3,500 / 3,500 / 500 / 250 | Pilot-tested |
| Sensitivity | **ARL₀ = 100**, a separate configuration with the **same master seed** (identical models and paths), independently calibrated limits, labelled secondary | Recommended; execution not authorized |

## Corrections required before production (C1–C7)

| ID | Change |
|---|---|
| C1 | `run.py`: add a `production` config and a `sensitivity_arl100` config (same seed, target 100). **Keep an explicit `--approved` (or equivalent) opt-in** for both modes, so they cannot start by accident once `CONFIGS["production"]` is no longer `None`. |
| C2 | **The paired no-change counterfactuals already exist**: `run.py` evaluates δ = 1 on the same CRN paths, and stores its summaries and paired contrasts in `results.json`. **Still pending: storage of their per-path derived outputs**, namely the δ = 1 per-path delays (for X(k)), the per-path window means for M at δ and at 1 (for its SE), and per-path occupancy. Output per-replicate Monte Carlo SEs. |
| C3 | `src/chart.py`: replace the percentile bootstrap in `paired_diff` with a **normal paired SE**; add `excess_detection` and a delta-method `masking_se`. |
| C4 | Aggregation across replicates: replicate mean, t_{R−1} CI, range, between-replicate SD s_b, within-replicate Monte Carlo SEs w_r, residual between-system variance σ̂²_sys = max(0, s_b² − (1/R)Σ_r w_r²) with σ̂_sys = √σ̂²_sys (originally named σ̂²_train; relabelled after the Phase 2 audit, M3), and sign count. |
| C5 | `src/report.py`: per-replicate tables (fitted diagnostics, h*, validation); aggregate tables including δ = 1 rows; labels distinguishing conditional and restricted summaries; conventional M marked "= 1 by construction"; a figure showing each replicate as a point. |
| C6 | Tests: conventional M ≡ 1; X(k) ≡ 0 at δ = 1; aggregation formulas on synthetic inputs; reproducibility with 2 replicates; the production guard refuses without `--approved`. |
| C7 | Docs: methodology §6–8 (estimands, H rationale, X(k), replicate aggregation, primary endpoints, sensitivity design); errata for pilot-report items A1–A8. |

**Done means:** code written, `pytest` passing, `smoke` and `verify` passing, docs updated, and the status record (`docs/project-status.md`) updated. Then ask for authorization to run the benchmark, production and the sensitivity.

### Implementation status (14 Oct 2026, session 3)

User decisions and refinements this session (binding):
- **Seeds:** production and sensitivity use the new master seed **20261014** (production evidence disjoint from the pilot); smoke and pilot keep 20261013.
- **Primary endpoints (12):** paired RMD₅₀₀ and paired X(20) contrasts, RF − GARCH and RF − conventional, λ = 0.1, δ ∈ {1.5, 2, 3}, each with its δ = 1 counterpart; "pre-specified after the exploratory pilot, before production"; recorded in `config["primary"]`.
- Conditional quantiles use the observed detection distribution with administrative censoring (censored paths never detections; non-identifiable quantiles suppressed).
- Aggregation uses an explicit schema, separating estimands, Monte Carlo SEs, flags, counts and metadata.
- Pathwise T(δ) ≤ T(1) is tested for the conventional chart only.
- Alarm-day coding: day M = τ − 1 + H (549) is a detection with D = H; M + 1 (550) is the censoring sentinel; boundary regression test including the `paths.npz` round trip.
- The benchmark (R = 1, seed 20261013) is a production-scale performance benchmark, not a pilot reproduction, and is excluded from production and sensitivity inference.
- `--approved` is a technical safeguard and never replaces the user's explicit authorization.

| ID | Implemented as |
|---|---|
| C1 | `run.py`: `PRODUCTION` sizes; modes `production`, `sensitivity_arl100` (target 100, same seed), `benchmark` (R = 1, seed 20261013); `GUARDED`; `--approved` checked before any directory or overwrite check; the wrapper refuses guarded modes without `--approved` (exit 2) before creating a directory, forwards the flag, and writes `source_sha256.txt` |
| C2 | `replicate(..., paths)` fills per-path arrays `T`, `occ`, `uS`, `uE` (δ = 1 included); `run()` writes `paths.npz` and `perpath_axes`; `perpath_sha256` per replicate enters the results hash. ≈ 0.8 MB per production replicate. Detection, occupancy and empirical masking statistics are reconstructible from it; bootstrap CIs also need the config and the replicate's bootstrap stream; daily score profiles are not reconstructible (path averages only, in `results.json`) |
| C3 | `src/chart.py`: `mean_se`, `alarm_days`, `delays_from_days`, `detected`, `cond_quantile`, `delay_summary(base=…)` with X(k), normal-SE `paired_diff` with optional bootstrap check, per-path `window_mean`, `ratio_se`; `run.evaluate()` computes the detection, occupancy and empirical masking estimates from the per-path arrays only. After the Phase 2 audit (M1): the summary keeps its full key set when no path survives (unidentified values None) and checks CRN pairing first |
| C4 | `src/aggregate.py`: `across` (eqs. 27–28, sign test; keys `var_between_resid`, `sd_between_resid`), `schema` (explicit allowlist), `collect` (unidentified replicate values listed without statistics); stored as `results.json` → `aggregate` |
| C5 | `src/report.py`: Tables 1–9 (per-replicate forecasters, h* and validation; aggregate diagnostics, detection incl. δ = 1, A9 check, masking with "1 by construction", primary endpoints, secondary contrasts, per-replicate primary contrasts with normal and bootstrap CIs, separate diagnostic section, runtime); figures `fig_delay`, `fig_profile`, `fig_replicates` |
| C6 | `tests/test_core.py`: 24 new tests (58 total); after the Phase 2 audit, 7 regression tests (65 total); after the second audit, 7 report-cell tests (72 total) |
| C7 | `docs/methodology.md` v1.2 (eqs. 23–28, §7.1–7.4, §10.1–10.3); pilot-report errata A1, A3, A4, A5 (no rerun); this file; `docs/project-status.md` |

## Post-benchmark amendments (user decision, 14 Oct 2026, before any production evaluation)

| ID | Change | Implemented as |
|---|---|---|
| A | Production R = 10 → **20**: more robust between-system variability and more precise primary comparisons, feasible per the benchmark. Unchanged: seed 20261014, 500 trees, 2,000 calibration, validation and OOC paths, shifts, λ, horizons, the 12 primary contrasts, architectures and tuning | `run.py` `PRODUCTION["replicates"] = 20`. The sensitivity inherits it (matched; only `target_arl` and `label` differ). The benchmark stays R = 1 with seed 20261013 |
| B | IC validation: pass iff the whole independent-validation 95% CI lies in [A₀(1−ε), A₀(1+ε)], ε = 0.15: [425, 575] at ARL₀ = 500 and [85, 115] at 100. A post-pilot, post-benchmark amendment made before production | `chart.ic_equivalence` (exact rational comparison, inclusive bounds); `validate` stores target, tol, bounds, rel. dev., N and outcome; `config["ic_validation"]` (rule and label) is written to `config.json` before computation; report Table 3, with failure listing |

**Original rule and benchmark outcome (unchanged):**
- The original rule was "A₀ in the 95% CI and |Â/A₀ − 1| ≤ 0.15". The benchmark recorded 2/6 primary passes (GARCH at both λ) and 2/2 diagnostic passes under it.
- Hypothetically, all 8 benchmark CIs lie in [425, 575]. The amendment was adopted after seeing this, and methodology §6 discloses it.
- Never relabel the benchmark's outcomes.

**Caveats:**
- each CI is conditional on h* (calibration uncertainty excluded), so the rule is not a complete equivalence test
- individual 95% CIs give no family-wise coverage
- at N = 2,000 passing needs Â ≈ 445–550

**Production failure-handling policy (methodology §6):**
- Run all 20 replicates. Never discard or replace failures, and never recalibrate on validation data.
- Report every per-replicate estimate, CI, relative deviation, N and outcome, and the pass counts per chart and λ.
- Flag failures next to the primary results (`report.validation_failures`). Never claim nominal calibration for all schemes if any failed.
- Severe-failure interpretation goes to a separate scientific decision: no post hoc exclusions or reruns.

**Provenance:** `scripts/git_provenance.sh` (see §Source provenance and reproducibility.md).

## Replication-aware estimators (avoid pseudoreplication)

**Within replicate r** (Monte Carlo inference conditional on the trained models). E = {i : T_i ≥ τ}, identical across δ by CRN.

| Quantity | Estimator | Monte Carlo SE |
|---|---|---|
| Pre-change false alarm | p̂_FA = 1 − \|E\|/N | binomial |
| Detection | P̂(D ≤ k), k ∈ {5, 20, 60} | binomial |
| **Excess detection** | **X̂(k)** = mean over E of [1{D(δ) ≤ k} − 1{D(1) ≤ k}] (paired) | sd/√\|E\| |
| Censoring | fraction with T > τ+H−1 | binomial |
| Restricted mean delay | **RMD_H** = mean of min(D, H), labelled "restricted to H = 500" | sd/√\|E\| |
| Conditional delay distribution | quartiles by the inverted empirical CDF over E; censored paths count in \|E\| but are never detections; q_p reported only if ⌈p\|E\|⌉ ≤ number detected within H | – |
| Paired contrasts | Δ̂(a, b) = mean over E_a ∩ E_b of (D_H^a − D_H^b) or of the per-path excess indicators (X contrasts), always with its δ = 1 counterpart | normal paired SE; bootstrap CI as a check |
| Masking | M̂ = (R̂ − 1)/(δ−1), R̂ = Ā/B̄, where A_i and B_i are path i's sustained-window mean score at δ and at δ = 1 (all N paths) | **SE(M̂) ≈ SE(R̂)/(δ−1)**, with delta-method SE(R̂) ≈ √(Σ_i(A_i − R̂B_i)²/(N(N−1)))/B̄. Conventional chart: A_i = δB_i, so SE = 0 by construction |
| Occupancy and validation | per-path averages | sd/√N |

Also report, per replicate: GARCH θ̂, s², the selected RF settings, QLIKE, the gap closed G, the RF slope, mean u, ACF(u), h* and the validation results.

**Across replicates** (method level; estimand θ = E_r[θ_r]):
- θ̄ = mean of θ̂_r, with equal weights.
- 95% CI θ̄ ± t_{R−1, 0.975}·s_b/√R. Here t₁₉ = 2.093 for production R = 20 (t₉ = 2.262, t₄ = 2.776).
- Show every replicate value.
- **Never** pool N × R paths with path-level SEs.
- **Variance decomposition (descriptive).** Var(θ̂_r) ≈ σ²_sys + E[w_r²], where w_r is the evaluation Monte Carlo SE of θ̂_r. Hence σ̂²_sys = max(0, s_b² − (1/R)Σ_r w_r²) and σ̂_sys = √σ̂²_sys (`var_between_resid`, `sd_between_resid`): the **residual between-system variability (training, model selection, forest randomness and calibration), after subtracting estimated evaluation Monte Carlo variance**. It does not isolate training-sample variability, because each replicate's h* is calibrated on its own paths. It is a method-of-moments approximation, not an identified decomposition of training uncertainty. Use the mean of the squared SEs, not the square of the mean SE: by Jensen's inequality, w̄² ≤ mean(w_r²), so w̄² would overstate σ̂_sys. The t interval uses s_b only and is unaffected.
- *(Withdrawn after the Phase 2 audit, M3: the earlier claim that the conventional chart should show σ̂ ≈ 0. Its s² and calibrated limit both vary across replicates, so its residual between-system variance need not be zero.)*

**Limitations (worst at R = 5):**
- wide t intervals, and an imprecise s_b (df = 4 gives a 95% CI for σ of [0.60, 2.87]·s_b)
- normality cannot be checked
- a sign test cannot reach 5% at 5/5
- conclusions are conditional on the DGP and n_train

**Pre-specified primary endpoints (confirmed by the user, 14 Oct 2026):** paired RMD₅₀₀ contrasts **and paired X(20) contrasts**, RF − GARCH and RF − conventional, at λ = 0.1 for every δ ∈ {1.5, 2, 3} (12 contrasts), each with its δ = 1 counterpart. Everything else is secondary.

## ARL₀ = 100 sensitivity (secondary)

**Design:**
- Same seed, models and paths as the primary run: a **matched** run, not an independent experiment (its Monte Carlo errors are correlated with production's).
- Limits calibrated separately to 100 on the same calibration paths and validated on the same validation paths.
- τ = 50 and H = 500 kept.

**What to expect:** P(T<τ) ≈ 0.4–0.45, i.e. about 1,100–1,200 evaluable paths per chart.

**Endpoints (all secondary):** the most informative here are X(5), X(20), X(60) and the paired contrasts with their δ = 1 counterparts; RMD is mostly false-alarm timing at this ARL₀. None of them is a primary endpoint of the study (primary: the 12 production contrasts of methodology §7.4).

**Declaring a reversal:** only if the aggregate CIs exclude 0 with opposite signs at ARL₀ = 500 and ARL₀ = 100. Otherwise call it "inconclusive". Never treat it as causal proof.

## Compute estimate

**Measured (benchmark, 14 Oct 2026, R = 1, production sizes, 500 trees):**
- one replicate: 50.7 s in process (RF prediction 37.3 s, RF grid fit 3.0 s, calibration bisection 2.5 s)
- whole command: 53.0 s (`time -v`), CPU 245 s user + 17 s system
- peak RSS 1,718,464 KiB (1.64 GiB)

**Forecast for R = 20 (extrapolated, not measured):**
- production ≈ 20 × 50.7 s + ≈ 3 s ≈ **17 min**; upper ≈ 30 min (allowing for replicates that select deeper forests, e.g. leaf 50 instead of the benchmark's 200, and for machine load)
- the ARL₀ = 100 sensitivity costs about the same again
- peak RSS ≈ 1.7 GiB, upper ≈ 2.2 GiB; per-path storage grows by ≈ 1 MB per replicate, so peak RSS is roughly independent of R
- `free -m` showed ≈ 3.4 GiB available on 14 Oct

### Original estimate (readiness review; scaled from pilot stage timings, not measured)

Per replicate (N = 2,000, T_max = 5,000, H = 500, 500 trees):

| Workload | Estimate |
|---|---|
| RF row-tree evaluations (24.4M rows × 500 trees) | 1.22e10, at 2.7–7.2 ns each plus a tree-depth allowance → **33–120 s** |
| Everything else | ≈ 10–15 s |
| **Per replicate** | **≈ 45–135 s** |

Totals:
- R = 5: ≈ 4–11 min
- R = 10: ≈ 8–22 min
- the ARL₀ = 100 run costs about the same again
- peak memory ≈ 1.6–2.0 GB, independent of R (estimate). Machine: 7,938,636 KiB ≈ 7.57 GiB RAM, 20 logical CPUs. The measured pilot peak RSS was 364,856 KiB ≈ 356 MiB
- uncertainty: a factor of about 2–3

*(Resolved: the benchmark ran on 14 Oct 2026 and the user chose R = 20; see the measured figures above.)* The R = 10 decision depended on a **small runtime benchmark**, for example one production-size replicate through the wrapper. Confirm authorization before running it.

## Source provenance (item 2 implemented 14 Oct 2026)

**The limitation.** The Phase 1 pilot was run from **uncommitted** source: HEAD `2a06da8`, worktree dirty, and `src/` and `run.py` untracked. `provenance.txt` records only the commit, a dirty flag and `git diff --stat`, so the pilot-generating source cannot be recovered from the run directory. Historical provenance is left as it is.

**Minimal improvements, cheapest first:**
1. Launch production and sensitivity runs only from a **clean, committed** worktree, so `git_commit` identifies the source. From 14 Oct 2026 the criterion is `git_tracked_modified: no`, `git_untracked_unclassified: none` and `git_ignored_python: none` in `provenance.txt` (`scripts/git_provenance.sh`). Untracked `.serena/` is reported separately as `git_untracked_tool_state` (development-tool state); it still sets the historical `git_worktree_dirty: yes`.
2. **Implemented:** one read-only line in `scripts/run_simulation.sh` hashes the executed source: `sha256sum run.py src/*.py scripts/run_simulation.sh requirements-lock.txt > "$RUN_DIR/source_sha256.txt"`. Optionally, also copy those files (about 40 KB) into the run directory.

## Execution procedure (only after explicit authorization)

1. Confirm corrections C1–C7 are complete; the status record shows tests passing and smoke/verify passing.
2. **Benchmark: done** (authorized, 14 Oct 2026; `results/runs/benchmark_20261014T041247_106190`; do not repeat). It was run as `scripts/run_simulation.sh benchmark --approved`. Workload: R = 1, N = 2,000 calibration + 2,000 validation + 2,000 OOC paths, T_max = 5,000, H = 500, 500 trees × 6 grid cells, seed 20261013. Its outputs are performance evidence only, never part of the production or sensitivity inference.
3. Then, after the production warning and explicit authorization: `scripts/run_simulation.sh production --approved`, and separately `scripts/run_simulation.sh sensitivity_arl100 --approved`. Each run gets its own `results/runs/<mode>_<timestamp>_<pid>/`. Launch from a clean committed worktree. Runs are not resumable: an interrupted run leaves a partial directory (logs kept, no `results.json`) and is rerun into a new directory.
4. Check: exit status 0; per-replicate validation under rule (29) (a failing replicate is **reported, never dropped, replaced or rescued**; see the failure policy below); frozen-model checks true; results hash recorded.
5. Record the run IDs, hashes, resources and findings in the status record. Report to the user.

## SPY application (later, separate phase; not authorized)

| Element | Plan |
|---|---|
| Data | Yahoo Finance via `yfinance` 1.7.0, `auto_adjust=True` (split- and dividend-adjusted close). One snapshot in `data/raw/` with timestamp and SHA-256; the analysis reads only the snapshot |
| Returns | r_t = 100·ln(P_t/P_{t−1}), demeaned by the training mean |
| Training | 1993-02-01 → 2006-12-29. RF tuned by chronological split (fit 1993–2003, select on 2004–2006 by QLIKE), then refit and frozen. GARCH(1,1)-t fitted and frozen. s² taken from training |
| Monitoring | 2007-01-03 → 2026-09-30. Filters and features update daily over the **concatenated** demeaned series; no refits |
| UCL | Calibrated to ARL₀ = 500 by simulation from the training GARCH-t fit, with the frozen SPY models applied. **This favours GARCH, and the article must say so** |
| Interpretation | Alarms are **descriptive only**: not validated event predictions, no causal claims, no trading strategy, Sharpe ratios or backtests |

**Outstanding SPY corrections:**
- **S1 – integrity checks:**
  - pass `multi_level_index` explicitly (`Series.squeeze("columns")` raises on single-level columns)
  - assert non-empty data; unique, increasing, tz-naive dates; finite positive prices; first date 1993-01-29; last date ≤ 2026-09-30; about 8,480–8,490 rows
  - list the extreme returns for an independent check
  - record that Yahoo back-adjusts history (file hashes differ between downloads; returns are robust) and that `repair=False`
- **S2 – the SPY pipeline:** tuning, refit and freeze, continuous filtering, simulation-based UCL. `sim.simulate` enforces ν > 4 and the 4th-moment margin, which a SPY-fitted GARCH-t may fail. The user must decide whether to allow finite-variance-only simulation (`need_m4=False`, documented). Near-IGARCH fits need longer burn-in.
- **S3 – reference dates:** pre-register the list in the docs **before** viewing any SPY output.

**Coverage notes:**
- Early years (1993–97) had thin volume and fractional ticks before 2001, so returns are more discrete.
- Multi-day closures (Sept 2001, Oct 2012) appear as single returns.
- The training window lacks 2008-level volatility, so RF saturation is expected in 2008 and 2020.
