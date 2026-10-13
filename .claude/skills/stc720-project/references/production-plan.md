# Production plan, required corrections and approval gates

This file is the persistent record of the **production-readiness review** (13 Oct 2026; verdict **CORRECTIONS REQUIRED**). The review was delivered in chat and is **not saved in `docs/`**. Production execution is **not authorized**. Preparing corrections C1–C7 is authorized, subject to the user's "production-preparation prompt", whose contents are **not recorded here**; confirm them first.

*Revised 14 Oct 2026 (independent-audit remediation, Phase 1 baseline):*
- *The masking-SE and variance-decomposition formulas are corrected.*
- *C2 is clarified: the counterfactuals already exist; only per-path storage is pending.*
- *A-item status is recorded below.*
- *A source-provenance recommendation is added.*

*None of C1–C7 is implemented.*

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
| Training replicates R | **10 preferred, subject to a small runtime benchmark** (otherwise 5) | User preference; benchmark needs confirmation |
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
| C4 | Aggregation across replicates: replicate mean, t_{R−1} CI, range, between-replicate SD s_b, within-replicate Monte Carlo SEs w_r, σ̂²_train = max(0, s_b² − (1/R)Σ_r w_r²) with σ̂_train = √σ̂²_train, and sign count. |
| C5 | `src/report.py`: per-replicate tables (fitted diagnostics, h*, validation); aggregate tables including δ = 1 rows; labels distinguishing conditional and restricted summaries; conventional M marked "= 1 by construction"; a figure showing each replicate as a point. |
| C6 | Tests: conventional M ≡ 1; X(k) ≡ 0 at δ = 1; aggregation formulas on synthetic inputs; reproducibility with 2 replicates; the production guard refuses without `--approved`. |
| C7 | Docs: methodology §6–8 (estimands, H rationale, X(k), replicate aggregation, primary endpoints, sensitivity design); errata for pilot-report items A1–A8. |

**Done means:** code written, `pytest` passing, `smoke` and `verify` passing, docs updated, and the status record (`docs/project-status.md`) updated. Then ask for authorization to run the benchmark, production and the sensitivity.

## Replication-aware estimators (avoid pseudoreplication)

**Within replicate r** (Monte Carlo inference conditional on the trained models). E = {i : T_i ≥ τ}, identical across δ by CRN.

| Quantity | Estimator | Monte Carlo SE |
|---|---|---|
| Pre-change false alarm | p̂_FA = 1 − \|E\|/N | binomial |
| Detection | P̂(D ≤ k), k ∈ {5, 20, 60} | binomial |
| **Excess detection** | **X̂(k)** = mean over E of [1{D(δ) ≤ k} − 1{D(1) ≤ k}] (paired) | sd/√\|E\| |
| Censoring | fraction with T > τ+H−1 | binomial |
| Restricted mean delay | **RMD_H** = mean of min(D, H), labelled "restricted to H = 500" | sd/√\|E\| |
| Conditional delay distribution | median and quartiles, reported only if censoring < 0.5 | – |
| Paired contrasts | Δ̂(a, b) = mean over E_a ∩ E_b of (D_H^a − D_H^b), always with its δ = 1 counterpart | normal paired SE |
| Masking | M̂ = (R̂ − 1)/(δ−1), R̂ = Ā/B̄, where A_i and B_i are path i's sustained-window mean score at δ and at δ = 1 (all N paths) | **SE(M̂) ≈ SE(R̂)/(δ−1)**, with delta-method SE(R̂) ≈ √(Σ_i(A_i − R̂B_i)²/(N(N−1)))/B̄. Conventional chart: A_i = δB_i, so SE = 0 by construction |
| Occupancy and validation | per-path averages | sd/√N |

Also report, per replicate: GARCH θ̂, s², the selected RF settings, QLIKE, the gap closed G, the RF slope, mean u, ACF(u), h* and the validation results.

**Across replicates** (method level; estimand θ = E_r[θ_r]):
- θ̄ = mean of θ̂_r, with equal weights.
- 95% CI θ̄ ± t_{R−1, 0.975}·s_b/√R. Here t₄ = 2.776 and t₉ = 2.262.
- Show every replicate value.
- **Never** pool N × R paths with path-level SEs.
- **Variance decomposition.** Var(θ̂_r) = σ²_train + E[w_r²], where w_r is the Monte Carlo SE of θ̂_r. Hence σ̂²_train = max(0, s_b² − (1/R)Σ_r w_r²) and σ̂_train = √σ̂²_train. Use the mean of the squared SEs, not the square of the mean SE: by Jensen's inequality, w̄² ≤ mean(w_r²), so w̄² would overstate σ̂_train.
- The conventional chart's performance is invariant to s² apart from the decaying Z₀ term, so expect σ̂_train ≈ 0. This is a built-in check.

**Limitations (worst at R = 5):**
- wide t intervals, and an imprecise s_b (df = 4 gives a 95% CI for σ of [0.60, 2.87]·s_b)
- normality cannot be checked
- a sign test cannot reach 5% at 5/5
- conclusions are conditional on the DGP and n_train

**Pre-specified primary endpoints (recommended):** paired RMD₅₀₀ contrasts RF − GARCH and RF − conventional, and X(20), at λ = 0.1 for every δ. Everything else is secondary.

## ARL₀ = 100 sensitivity (secondary)

**Design:**
- Same seed, models and paths as the primary run.
- Limits calibrated to 100 on the calibration paths and validated on the validation paths.
- τ = 50 and H = 500 kept.

**What to expect:** P(T<τ) ≈ 0.4–0.45, i.e. about 1,100–1,200 evaluable paths per chart.

**Endpoints:** primary X(5), X(20), X(60) and the paired contrasts with their δ = 1 counterparts. RMD is mostly false-alarm timing at this ARL₀.

**Declaring a reversal:** only if the aggregate CIs exclude 0 with opposite signs at ARL₀ = 500 and ARL₀ = 100. Otherwise call it "inconclusive". Never treat it as causal proof.

## Compute estimate (from the readiness review; scaled from pilot stage timings, not measured)

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

The R = 10 decision depends on a **small runtime benchmark**, for example one production-size replicate through the wrapper. Confirm authorization before running it.

## Source provenance (recommended for future runs; not implemented)

**The limitation.** The Phase 1 pilot was run from **uncommitted** source: HEAD `2a06da8`, worktree dirty, and `src/` and `run.py` untracked. `provenance.txt` records only the commit, a dirty flag and `git diff --stat`, so the pilot-generating source cannot be recovered from the run directory. Historical provenance is left as it is.

**Minimal improvements, cheapest first:**
1. Launch production and sensitivity runs only from a **clean, committed** worktree (`git_worktree_dirty: no`), so `git_commit` identifies the source.
2. Add one read-only line to `scripts/run_simulation.sh` that hashes the executed source: `sha256sum run.py src/*.py scripts/run_simulation.sh requirements-lock.txt > "$RUN_DIR/source_sha256.txt"`. Optionally, also copy those files (about 40 KB) into the run directory.

## Execution procedure (only after explicit authorization)

1. Confirm corrections C1–C7 are complete; the status record shows tests passing and smoke/verify passing.
2. Run `scripts/run_simulation.sh production --approved` (the exact flag is decided in C1), then the sensitivity run. Each run gets its own `results/runs/<mode>_<timestamp>_<pid>/`.
3. Check: exit status 0; per-replicate validation passes (a failing replicate is **reported, never dropped or rescued**); frozen-model checks true; results hash recorded.
4. Record the run IDs, hashes, resources and findings in the status record. Report to the user.

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
