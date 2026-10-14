# Frozen production results (R = 20, ARL₀ = 500)

**Status: FIRST FULL PRODUCTION COMPLETE — SCIENTIFIC RESULTS AUDIT PENDING.** These results come from the run session's internal checks only. **No independent numerical audit has been done yet** (open task P1 in [`docs/project-status.md`](../../../../docs/project-status.md), which is the authoritative checkpoint and task list). Every number below was read from the run's `results.json` (aggregate over replicates). The full tables are in the run's `tables.md`.

## Identity: how to locate and authenticate the frozen run

| Item | Value |
|---|---|
| Directory | `results/runs/production_20261014T060921_145897/` (git-ignored; local only; **never modify, overwrite or regenerate**) |
| Source | commit `3529dddf5ea7dcc68d3f279e31e6150dd188d3d7` on `main`, clean worktree. Provenance: `git_tracked_modified: no`, `git_untracked_unclassified: none`, `git_ignored_python: none`, `.serena/` tool state only. The run's `source_sha256.txt` equals the committed files |
| `results_sha256` (in `results.json`; recompute with `run.results_hash`) | `44410144e3feb4a762dd2044fec07a2ddc64fdc742d43637332cc03f731431b8` |
| `results.json` file SHA-256 | `716862ab41d08c581d2bd65c63979c046a9d9cb5930c111381b3eeb6506b708b` |
| `paths.npz` | `0055f1e115e6cd676d88dcc0875dfee19c44018afc8154658b40be9a2ab8cdf3` |
| `config.json` | `897cf519889a117a7282592b9f7108e74eba4ef0bd047201e37261fba340c130` |
| `tables.md` | `7757c948017b6ee2ef6ed04411534404fe03ea77774ac2de517b8a93ead0dc39` |
| `source_sha256.txt` | `746e9cf88ecbbb127b2bfc4806e4212baa68e8783062cf3184bbb707520f6747` |
| `fig_replicates.png` (defective, P3) | `1af6a11058e6e014397befbbff7a0d6c060f96a277a64293aaeda8456225aecb` |
| `fig_delay.png` / `fig_profile.png` | `e3ff5f011f9d7a21…` / `a409411c285eab91…` |

Check: `sha256sum results/runs/production_20261014T060921_145897/*`, then compare with this table.

## Configuration (frozen; equals `run.CONFIGS["production"]` at `3529ddd`)

| Setting | Value |
|---|---|
| Mode, date | `production`, 14 Oct 2026 (06:09:21–06:25:48 SAST) |
| Target ARL₀ | 500 |
| Replicates and seed | R = 20 independent training-and-calibration replicates; master seed 20261014; streams `SeedSequence(20261014, spawn_key=(rep, role))` |
| Data | GARCH(1,1)-t DGP (ω = 0.02, α = 0.07, β = 0.91, ν = 6); n_train = n_dev = 3,500 |
| Paths per replicate | 2,000 calibration and 2,000 independent IC-validation paths (horizon 5,000); 2,000 OOC paths (H = 500), reused across δ by CRN, which gives 2,000 paths per shift scenario |
| Change and grid | τ = 50; δ ∈ {1.5, 2, 3} plus the δ = 1 counterfactual; λ ∈ {0.1 (primary), 0.2} |
| Forest | 500 trees; grid min leaf {50, 200, 800} × max features {1, 3} |
| Endpoints and rule | the 12 pre-registered primary contrasts (methodology §7.4) and the amended IC rule (eq. 29), both unchanged |

## Execution (measured)

- Exit 0. **20/20 replicates.** None discarded, replaced, selectively rerun or recalibrated.
- Wall 16 min 26.7 s (outer `time -v`); run.py 981.2 s; 49.1 s per replicate.
- CPU 6,602 s user + 306 s system (700%).
- **Peak RSS 1,825,888 KiB (1.74 GiB)**; no swap.
- RF prediction 721 s (73%).

**Internal checks by the run session (all passed):**
- config equals the committed config
- every h* has an independent validation (N = 2,000, bounds [425, 575])
- pass flags recompute from the stored CIs
- frozen-model checks true
- per-path hashes, and the OOC, paired and masking results, recompute exactly from `paths.npz` (with `run.evaluate`)
- the aggregate and the results hash recompute
- one t-CI was checked with plain SciPy
- censoring ≤ 0.05%

These checks used the project's own estimators; P1 must not.

## Observed numerical findings (λ = 0.1 unless stated)

**IC validation (eq. 29): 160/160 configurations passed** (120 primary + 40 diagnostic).
- Mean validated ARL₀ by chart and λ is 495.9–502.2.
- Per-replicate relative deviation is −8.2% to +7.9%; CI ends span 438.8–564.9.
- Brook–Evans oracle ARL: 501.7 (λ = 0.1), 500.1 (λ = 0.2).
- Descriptive only: the original rule would have passed 97/120 primary configurations.

**Detection.** Restricted mean delay RMD₅₀₀ (days), per chart over its own evaluable set, with the 95% t interval over replicates:

| δ | Conventional | RF | GARCH | Oracle (diagnostic) |
|---|---|---|---|---|
| 1 (no change) | 319.9 | 316.6 | 316.0 | 316.3 |
| 1.5 | 205.3 [202.9, 207.6] | 243.3 [237.9, 248.6] | 249.1 [245.6, 252.7] | 251.3 |
| 2 | 131.6 [129.9, 133.4] | 191.8 [183.5, 200.0] | 201.7 [196.2, 207.1] | 204.7 |
| 3 | 63.0 [62.1, 64.0] | 126.4 [115.3, 137.4] | 139.6 [132.8, 146.4] | 142.3 |

| Per-chart X(20) (excess detection within 20 days) | Conventional | RF | GARCH |
|---|---|---|---|
| δ = 1.5 | 0.054 | 0.045 | 0.044 |
| δ = 2 | 0.126 | 0.100 | 0.098 |
| δ = 3 | 0.282 | 0.220 | 0.220 |

Pre-change false-alarm probability P(T < τ) [all paths]: conventional 0.125, RF 0.102, GARCH 0.094, oracle 0.093.

**The 12 primary contrasts.** Paired over E_a ∩ E_b; replicate mean [95% t CI, df 19]; **not adjusted for multiplicity**. Signs give the number of replicates with a positive / negative contrast.

| Contrast | δ = 1 counterpart | δ = 1.5 | δ = 2 | δ = 3 |
|---|---|---|---|---|
| RF − GARCH, RMD₅₀₀ | +0.27 [−1.24, 1.79] | −6.05 [−10.47, −1.63] (6/14) | −9.94 [−17.08, −2.80] (5/15) | −13.13 [−22.88, −3.39] (6/14) |
| RF − GARCH, X(20) | 0 by construction | +0.0009 [−0.0021, 0.0039] | +0.0013 [−0.0027, 0.0054] | −0.0005 [−0.0092, 0.0081] |
| RF − conventional, RMD₅₀₀ | −3.80 [−6.53, −1.07] | +37.54 [32.96, 42.11] (20/0) | +60.40 [52.96, 67.84] (20/0) | +63.63 [53.01, 74.25] (20/0) |
| RF − conventional, X(20) | 0 by construction | −0.0081 [−0.0110, −0.0052] (1/18) | −0.0251 [−0.0290, −0.0212] (0/20) | −0.0608 [−0.0693, −0.0524] (0/20) |

- Paired path counts: 1,734–1,793 (RF − GARCH) and 1,645–1,717 (RF − conventional).
- RF − GARCH RMD varies strongly across trained systems: s_b = 9.4 / 15.3 / 20.8 days against a Monte Carlo SE of about 2.7. Replicate values at δ = 3 range from −46.8 to +18.3. The sign-test p is 0.12 / 0.041 / 0.12.
- The selected RF settings (min leaf, max features) varied: (200, 3) ×8, (50, 1) ×6, (50, 3) ×4, (200, 1) ×2.
- λ = 0.2 (secondary) shows the same pattern.

**Adaptation masking M** (sustained window, λ-free; mean [95% t CI]):

| δ | Conventional | RF | GARCH | Oracle | First-order theory (GARCH / oracle) |
|---|---|---|---|---|---|
| 1.5 | 1 (by construction) | 0.342 [0.305, 0.380] | 0.243 [0.226, 0.261] | 0.230 | 0.171 / 0.160 |
| 2 | 1 | 0.308 [0.269, 0.348] | 0.198 [0.182, 0.214] | 0.186 | 0.134 / 0.125 |
| 3 | 1 | 0.281 [0.237, 0.326] | 0.144 [0.132, 0.157] | 0.134 | 0.094 / 0.087 |

**Forecasting** (independent IC validation paths):

| | QLIKE vs true h | Gap closed G | Slope of d on h | corr(d, h) | Mean u | ACF₁ of u |
|---|---|---|---|---|---|---|
| Oracle | 0.810 | – | – | – | 1.000 | 0.000 |
| GARCH | 0.812 | 0.989 | 0.999 | 0.996 | 0.996 | −0.002 |
| RF | 0.841 | 0.850 | 0.348 | 0.642 | 1.022 | 0.011 |
| Conventional | 1.019 | – | – | – | 1.030 | 0.132 |

- The RF floor never bound (0 of 10⁷ forecasts).
- No GARCH fit was near the boundary; persistence ranged 0.960–0.992.

**A9 (pre-change false alarms, OOC against validation): resolved.** The differences are −0.0005 to −0.0033, within Monte Carlo error.

## What the findings show, and what they do not

**Observed (numerical, in this simulation):**
1. Conventional EWMA detected the evaluated persistent increases fastest, with the lowest RMD₅₀₀ and the highest X(20) at every δ > 1.
2. RF–EWMA had shorter mean restricted delays than GARCH–EWMA (unadjusted CIs exclude 0 at every δ > 1), with large between-system heterogeneity.
3. RF–EWMA showed no distinguishable advantage over GARCH–EWMA on X(20).
4. The forecast-accuracy ranking (oracle ≈ GARCH < RF < conventional, by QLIKE) is roughly opposite to the detection-speed ranking. The least accurate forecaster detected best.
5. The masking ranking (conventional M = 1 > RF > GARCH ≈ oracle) matches the RMD ranking.
6. The first-order masking theory (eq. 20) underpredicts the empirical M by about 0.05–0.07.

**Not established:**
- That adaptation masking is the cause, or the sole cause, of the detection differences. It is an association across four charts that also differ in the shape of their IC run-length distribution, in score dependence and in pre-change false alarms. RF's lower masking coincides with its attenuated responsiveness (slope 0.35), whose cause is not isolated (methodology §9).
- Any family-wise or confirmatory significance.
- Any generalization beyond this DGP and design.

## Caveats (state them with the results)

- All 12 primary contrasts use matched (CRN) simulated paths and predefined survivor conditioning: paths with no pre-change alarm for either chart (E_a ∩ E_b).
- Replicate-level uncertainty comes from 20 independently fitted and calibrated monitoring systems (t interval, df 19). The within-replicate Monte Carlo intervals are conditional on each trained system.
- The 95% CIs are **not adjusted for multiple comparisons**. Methodology §7.4 pre-registered no adjustment. Any Holm analysis (P2) was decided after seeing the results and must be labelled post hoc and supplementary.
- Equal target ARL₀ does not imply identical pre-change false-alarm probabilities: 0.125 against 0.094. The δ = 1 RF − conventional RMD counterpart is −3.80 days, not 0.
- Restricted delays are administratively censored at H = 500; GARCH censoring is 21% at δ = 1.5. RMD is a restricted mean, never ARL₁.
- The GARCH-generated DGP favours the GARCH forecaster and limits generalization.
- IC validation (eq. 29) uses CIs conditional on the calibrated h*, so the full uncertainty of the estimated control limits is excluded. It is a post-pilot, post-benchmark amendment.
- `fig_replicates.png` is defective at R = 20: jitter clips replicates 0 and 19 at δ = 1 and 3 (P3). The tables are unaffected.

## Data available for the open tasks (no new simulation needed)

- **P1, P2.** Per-path arrays in `paths.npz` (`r{rep}_T`, `_occ`, `_uS`, `_uE`; axes in `results.json` → `perpath_axes`; T = 550 means censored), plus the per-replicate estimates in `results.json`.
- **P4.** Per-replicate `rf_grid` (with the selected cell), `forecast_diag`, `masking`, `paired`, `garch_fit` and `calibration` in `results.json`.
- **P5.** Per-replicate validation summaries (`q10`, `q50`, `q90`, `p_le_250`, `p_lt_tau`, ARL, SE). The δ = 1 alarm days in `paths.npz` give per-path no-change run lengths truncated at day 549. **Per-path IC-validation run lengths are not stored.**
