# Project status — verified record

*Authoritative progress record for the STC 720 project. It is read at the start of every session through the `stc720-project` skill ([`.claude/skills/stc720-project/SKILL.md`](../.claude/skills/stc720-project/SKILL.md)) and `CLAUDE.md` §19.*

## FIRST FULL PRODUCTION COMPLETE — SCIENTIFIC RESULTS AUDIT PENDING

*Last updated: **2026-10-14**, end of the development session (post-production documentation synchronization, on HEAD `3529ddd`).*
- *The scientific architecture and configuration are **frozen**. Phase 1 and Phase 2 are complete.*
- *The R = 20 production run `results/runs/production_20261014T060921_145897` is complete and frozen.*
- *The **next task is P1 (independent production-results audit)**, below. No further simulation is authorized.*
- *Numbers, hashes and caveats are in [production-results.md](../.claude/skills/stc720-project/references/production-results.md).*

*Earlier update (final production-design preparation on HEAD `9b286e1`; since committed by the user as `3529ddd`). Verified by:*
- *`.venv/bin/python -m pytest -q`: **80 passed** (72 previous + 8 new parametrized cases)*
- *four deliberate mutations (strict bounds, float bounds, old rule, R = 10), each caught*
- *`scripts/run_simulation.sh smoke` and `verify`: exit 0; hash `0ff5992f6d155c91…` identical in smoke and both verify runs*
- *a leaf-by-leaf comparison with the previous smoke `smoke_20261014T034755_98486` (`afef9c4e…`): `aggregate.estimands`, `aggregate.counts`, `config.primary` and every per-replicate ooc/paired/masking/calibration/forecast value are identical, and `paths.npz` is byte-identical. Only the new `config.ic_validation` and validation keys, the `passed` flags and their counts differ*
- *a SHA-256 re-check of all 365 pre-existing `results/runs/` files: 0 changed*
- *read-only `git status` / `git diff --check`*

*Previous update (session 3: Phase 2 production preparation C1–C7, then remediation of the independent Codex CLI audit of Phase 2; HEAD `87c4dc7`; since committed by the user as `9b286e1`). That remediation was verified by:*
- *`.venv/bin/python -m pytest -q`: **72 passed** (34 Phase 1 + 24 Phase 2 + 7 audit-remediation + 7 report-cell regression tests), after the final reporting corrections from the second audit*
- *the audit's crashes (M1 truncated schema and KeyError, M1 pairing-check bypass, M2 figure KeyError) reproduced before the fix and absent after it*
- *`scripts/run_simulation.sh smoke` and `verify`: both exit 0; hash `afef9c4e…` identical in smoke and both verify runs. Against the pre-remediation smoke (`357f5c86…`): every per-replicate value is bit-identical; the aggregate is identical after the `var_train`/`sd_train` key rename (195 t-CIs bit-identical)*
- *earlier in session 3 (C1–C7): `smoke` and `verify` passed with hash `357f5c86…`*
- *guard checks: `run.py` and the wrapper refuse `production`, `sensitivity_arl100` and `benchmark` without `--approved`; overwrite refusal on existing run directories*
- *independent recomputation (plain NumPy/SciPy, no `src/` imports) of per-replicate estimators from `paths.npz` and of the replicate aggregates: max discrepancy 0*
- *SHA-256 re-check of all pre-existing `results/runs/` files (138 from the session start, 222 before the remediation): 0 changed; canonical pilot hash `f92f0715…`*
- *read-only `git status` / `git diff --check`*

## Verified checkpoint

**First full production run completed (14 Oct 2026; explicitly authorized by the user: "START PRODUCTION … this one full ARL₀ = 500 production simulation … at commit 3529ddd").** Details, full tables and hashes are in [production-results.md](../.claude/skills/stc720-project/references/production-results.md).
- **Run.**
  - directory `results/runs/production_20261014T060921_145897/`
  - `results_sha256` `44410144e3feb4a762dd2044fec07a2ddc64fdc742d43637332cc03f731431b8`; re-verified at the end-of-session synchronization (stored value = recomputed value; all 17 files unchanged)
  - command `/usr/bin/time -v scripts/run_simulation.sh production --approved`, run on clean committed HEAD `3529ddd`
- **Configuration (unchanged design).** Mode `production`; target ARL₀ = 500; R = 20 independent training-and-calibration replicates; master seed 20261014; 500 RF trees. Per replicate: 2,000 calibration paths, 2,000 IC-validation paths, and 2,000 OOC paths per shift scenario (CRN across δ). IC horizon 5,000; OOC horizon H = 500; τ = 50; δ ∈ {1.5, 2, 3}; λ ∈ {0.1, 0.2}. The 12 primary contrasts and the IC rule (eq. 29) are unchanged.
- **Execution.**
  - 20/20 replicates; exit status 0; wall 16 min 26.7 s; peak RSS 1,825,888 KiB (1.74 GiB)
  - **160/160 IC configurations passed** the amended criterion (eq. 29)
  - no replicate was discarded, replaced, selectively rerun or recalibrated
- **Checks.** All of the run session's internal reproducibility and verification checks passed: config, validation coverage, pass-flag recomputation, frozen models, recomputation from `paths.npz` with the project's estimators, aggregate and results hash, source hashes, and integrity of the historical artifacts. **The production results have not yet had an independent numerical audit (P1).**
- **Principal observed findings** (λ = 0.1; mean restricted delay RMD₅₀₀ in days):

  | δ | Conventional | RF | GARCH |
  |---|---|---|---|
  | 1.5 | 205 | 243 | 249 |
  | 2 | 132 | 192 | 202 |
  | 3 | 63 | 126 | 140 |

  1. Conventional EWMA detected the evaluated persistent increases fastest.
  2. RF–EWMA had shorter mean restricted delays than GARCH–EWMA: paired −6.1 / −9.9 / −13.1 days, unadjusted CIs exclude 0, with large between-system heterogeneity.
  3. RF–EWMA showed no clearly distinguishable advantage over GARCH–EWMA on X(20): all three CIs include 0.
  4. Conventional EWMA has the worst conditional-variance forecasting accuracy (QLIKE 1.019 against GARCH 0.812 and RF 0.841) but the best detection in these scenarios.
  5. Adaptation masking (M: conventional 1 by construction > RF ≈ 0.28–0.34 > GARCH ≈ 0.14–0.24) is **consistent with** the detection ranking. It is **not shown to be the cause**, or the sole cause.
- **Caveats** (see production-results.md):
  - matched paths and predefined survivor conditioning
  - replicate-level uncertainty from 20 independently fitted and calibrated systems
  - unadjusted 95% CIs
  - equal ARL₀ ≠ equal pre-change false-alarm probability (0.125 against 0.094)
  - administrative censoring at H = 500
  - GARCH-generated DGP
  - IC-validation CIs are conditional on h* and exclude control-limit estimation uncertainty

**Final production design prepared (14 Oct 2026; user-approved plan with two refinements; committed by the user as `3529ddd`):**
- **A. R = 20.** Production `replicates` 10 → 20. `sensitivity_arl100` inherits it (matched; only `target_arl` and `label` differ). The benchmark config is unchanged (R = 1, seed 20261013). Everything else is unchanged: seed 20261014, 500 trees, 2,000 calibration, validation and OOC paths, δ, λ, τ, H, the 12 primary contrasts, models and tuning.
- **B. Amended IC validation rule (methodology §6, eq. 29).** A configuration passes iff its whole independent-validation 95% CI lies in [A₀(1−ε), A₀(1+ε)], ε = 0.15. That is [425, 575] at ARL₀ = 500 and [85, 115] at 100.
  - Bounds are inclusive and exactly A₀(1 ± ε), compared in exact rational arithmetic (`chart.ic_equivalence`). This was the user's refinement: no rounding in the rule.
  - The rule is labelled a "post-pilot, post-benchmark methodological amendment made before production". It is recorded in `config["ic_validation"]`, so `config.json` captures it before computation.
  - `validate` also stores target, tol, bounds, relative deviation and N.
  - The report lists every failure under Table 3 and flags the λ = 0.1 failures before Table 7a.
  - Caveats are in methodology §6: conditional on h*, not a complete equivalence test, no family-wise coverage.
- **Benchmark outcome under the original rule: recorded unchanged** (2/6 primary, 2/2 diagnostic; see below). Evaluated hypothetically, all 8 benchmark CIs lie in [425, 575]; methodology §6 discloses this. It does not relabel the benchmark, which stays excluded from inference.
- **Production failure-handling policy** written before execution (methodology §6; production-plan.md).
- **Provenance.** `scripts/git_provenance.sh` (read-only Git) adds four lines to `provenance.txt`. This was the user's refinement: only `.serena/` is tool state, and no other untracked file is assumed harmless.
  - `git_tracked_modified`
  - `git_untracked_tool_state` (`.serena/` only)
  - `git_untracked_unclassified` (every other untracked file, listed individually as potentially execution-relevant)
  - `git_ignored_python`

  `git_worktree_dirty` keeps its old meaning, and `source_sha256.txt` now hashes `scripts/*.sh`.
- **Smoke under rule (29): 0 of 6 primary configurations pass** (was 3 of 6 under the original rule). At N = 60 and target 50 the CI half-width (~13) exceeds the ±7.5 margin. This is expected: smoke is not validation.
- New runs: `results/runs/smoke_20261014T053655_132590` and `results/runs/verify_20261014T053658_132710` (hash `0ff5992f6d155c91e10afc9b08e94078a7f8afea95fffe7c331a6ed32dc4aec3`).
- **Forecast for R = 20 (extrapolated from the measured benchmark):** ≈ 17 min (upper ≈ 30 min); peak RSS ≈ 1.7 GiB (upper ≈ 2.2 GiB); the sensitivity costs the same again.

**Benchmark executed (14 Oct 2026, explicitly authorized by the user):** `scripts/run_simulation.sh benchmark --approved` on committed HEAD `9b286e1` (tracked worktree clean; only untracked `.serena/`, hence `git_worktree_dirty: yes`). Output `results/runs/benchmark_20261014T041247_106190` (results hash `77e20ffa2e50457a…`, `results.json` SHA-256 `970ab9ea…`, `paths.npz` `5069c9da…`). Production-scale performance benchmark only (R = 1, seed 20261013, 500 trees), excluded from all inference.
- **Measured:** exit 0; wall 53.4 s (outer `time -v`), run.py 53.0 s, in-process replicate 50.7 s; CPU 245 s user + 17 s system (490%); **peak RSS 1,718,464 KiB (1.64 GiB)**; RF prediction 37.3 s (74% of the replicate), RF grid fit 3.1 s, calibration bisection 2.5 s.
- **Validation under the original pre-registered rule (target in the 95% CI and within ±15%), recorded unchanged: 2 of 6 primary configurations passed** (GARCH at λ = 0.1 and 0.2), 4 failed (conventional and RF at both λ; validated ARL₀ 460–475, −5.1% to −8.0%, CIs excluding 500); the diagnostic passed 2/2 (Brook–Evans 500.2 / 498.1 at the calibrated h*). All 8 validated ARL₀ were below 500; all were within ±15%. The cause is **not established** (see open issue 16). Calibration and validation censoring ≤ 0.05%.
- **Extrapolated (not measured):** production R = 10 ≈ 8.5–9 min (upper ≈ 15 min); R = 20 ≈ 17 min (upper ≈ 30 min); peak RSS ≈ 1.7 GiB, upper ≈ 2.2 GiB, roughly independent of R.

**Stage:**
- Phase 1 is **complete and verified**.
- The production-readiness review has been **delivered**.
- The **independent (Codex CLI) audit remediation is complete** (14 Oct 2026). Its verdict was "corrections required before commit".
- **The user committed the verified Phase 1 baseline:** `f77297b9a257bbe8ca80c858f6119219471925b8` ("feat: add RF-EWMA simulation pipeline and verified Phase 1 pilot"), then `87c4dc7` (docs synchronization).
- **Phase 2 production preparation (C1–C7) is implemented and verified (14 Oct 2026, session 3)**, from the user's production-preparation prompt and the approved implementation plan with the user's refinements (below). **Committed by the user as `9b286e1`.** The benchmark was then run once (authorized). Production, sensitivity and SPY were **not run**.
- **Phase 2 independent audit (Codex CLI): CORRECTIONS REQUIRED, 3 major findings, no critical scientific errors** (the auditor reproduced 9,009 numerical comparisons). **All findings remediated and verified (14 Oct 2026, session 3)**; awaiting an independent recheck:

  | Finding | Remediation | Evidence |
  |---|---|---|
  | M1 empty survivor sets | `chart.delay_summary` checks CRN pairing before anything else and always returns the full key set (unidentified values None, never 0); `paired_diff` gives a mean without SE/CI for n = 1; `aggregate.collect` tolerates missing SEs | tests `test_empty_survivor_set_keeps_full_schema_with_missing_values`, `test_mismatched_counterfactual_survivors_raise_even_when_empty`, `test_partially_identified_quantities`, `test_aggregation_handles_unidentified_replicate_endpoints` |
  | M2 unidentified points in figures | `report.series` omits unidentified points (count shown in the title) and draws no bar (NaN) when no interval exists; tables use n/i (not identifiable) and – (not applicable) | `test_reporting_with_unidentified_endpoints` (real `report.write` path, R = 2 and R = 1), `test_figure_series_omits_unidentified_points_and_never_zero_fills` |
  | M3 variance interpretation | `var_train`/`sd_train` → `var_between_resid`/`sd_between_resid`, σ̂_sys: residual between-system variability (training, model selection, forest randomness and calibration) after subtracting estimated evaluation Monte Carlo variance; descriptive method-of-moments approximation; conventional-chart "≈ 0" claim withdrawn | arithmetic and CIs bit-identical (smoke comparison); `docs/methodology.md` v1.3 eq. 28, production-plan.md |
  | Minor D1–D6 | population labels [all]/[E] in the report; `paths.npz` reconstruction scope qualified; only RMD₅₀₀ and X(20) contrasts primary; production and sensitivity matched, not independent; smoke ≠ validation, with a pass count in Table 3; hand-counted paired X(k) test over 2 shifts × 2 λ | `test_paired_excess_contrast_hand_counted_over_two_shifts_and_two_lambdas`; docs |

| Item | Verified state | Evidence |
|---|---|---|
| Planning docs | Done | `docs/research_plan.md`, `docs/methodology.md` (eqs. 1–22), `docs/references.md` |
| Core code | Done (Phase 1 + Phase 2 preparation) | `src/sim.py`, `src/forecast.py`, `src/chart.py`, `src/aggregate.py`, `src/report.py`, `src/spy.py` (data utilities only), `run.py` (modes `smoke` [R = 2], `pilot`, `verify`; guarded `production`, `sensitivity_arl100`, `benchmark` refuse without `--approved`) |
| Wrapper | Done | `scripts/run_simulation.sh` (GNU time, logs, exit status, provenance incl. args and `source_sha256.txt`, thread limits, read-only Git; guarded modes exit 2 without `--approved` before creating a directory) |
| Tests | **80 passed** after the final production-design preparation (14 Oct 2026). The 8 new cases are: exact equivalence bounds at ARL₀ 500 and 100 (bounds, one ulp inside and outside, clearly out of range); three hand-checked validation examples; R = 20 stream independence (140 distinct streams, disjoint from seed 20261013); provenance classification with probe files; failure reporting without dropping. The configuration test is updated (R = 20, inherited sensitivity, `ic_validation`) and t₁₉ is checked. Previously **72 passed** (`.venv/bin/python -m pytest -q`, 14 Oct 2026, session 3, after the final reporting corrections): 34 Phase 1 tests unchanged + 24 Phase 2 tests (one updated for the M3 key rename) + 7 audit-remediation regression tests + 7 report-cell regression tests (δ = 1 X(k) n/i vs valid zero; one-survivor SE n/i; inapplicable –; mode-sensitive headings for production, sensitivity, benchmark, smoke). Phase 2 tests (alarm-day boundary incl. `paths.npz` round trip; X(k); CRN-pairing check; censoring-aware quantiles; normal paired SE vs bootstrap; masking delta-method SE vs replication SD; aggregation formulas, equal weights, schema allowlist; conventional-only monotonicity and M ≡ 1; recomputation from `paths.npz`; 2-replicate reproducibility; config values; guards ×3 modes in run.py and wrapper; overwrite refusal with `--approved`). Six deliberate code mutations were each caught | `tests/test_core.py`, `pytest.ini` |
| Smoke + verify (Phase 1 code) | Passed after remediation; smoke hash `5e84db38…`, verify identical | `results/runs/smoke_20261014T002849_20414`, `results/runs/verify_20261014T002855_20527/verify.txt` (13 Oct runs kept) |
| Audit remediation (14 Oct) | **Done.** M1 statistical reporting; M2 RF-slope interpretation; M3 overwrite guard; small fixes 1–9. The pilot was **not rerun**; the canonical artifacts are unchanged (104/104 files hash-identical) | `docs/phase1_pilot_report.md` §14 (revision log); `run.py` `refuse_overwrite`; `src/forecast.py` `slope`; `src/report.py`; `setup.sh`; `docs/methodology.md` v1.1; skill references |
| Code ↔ canonical hash | The canonical `f92f0715…` came from **uncommitted pre-remediation source** (HEAD `2a06da8`, dirty). **Phase 1 remediation (committed in `f77297b`):** it changed one numerical output relative to the pilot source, `slope_h` ×(n−1)/n; at smoke scale exactly 3 `slope_h` leaves differed and all other leaves were bit-identical. **Phase 2 source (session 3, uncommitted) differs further:** new output schemas (per-path arrays, X(k), SE keys, renamed delay keys), replicate aggregation, normal paired intervals and the rewritten report, so it does not reproduce the pilot's `results.json` either, and the slope fix is **not** the only difference. The pilot was not rerun; its original artifacts are preserved | scratch comparison, 14 Oct |
| Reduced pilot | Done; all criteria Q1–Q6 met | **Canonical run:** `results/runs/pilot_20261013T075339_142070` (hash `f92f07159b682406ef0ca8bd52c0e64e8eed38a795784b7ec8e9549c17b01bb7`; three identical runs). Summary: `docs/phase1_pilot_report.md` |
| Production-readiness review | Delivered **in chat only** (not saved in `docs/`); verdict **CORRECTIONS REQUIRED** | Content preserved in [production-plan.md](../.claude/skills/stc720-project/references/production-plan.md) |
| Corrections C1–C7 | **Done and verified (14 Oct, session 3; uncommitted).** C1 guarded configs + `--approved` (run.py and wrapper); C2 per-path `paths.npz`; C3 estimators (eqs. 23–26); C4 `src/aggregate.py` (eqs. 27–28, explicit schema); C5 report rewrite; C6 24 new tests; C7 docs | `run.py`, `src/chart.py`, `src/aggregate.py` (new), `src/report.py`, `scripts/run_simulation.sh`, `tests/test_core.py`, `docs/methodology.md` v1.2, skill references; detail in production-plan.md "Implementation status" |
| Smoke + verify (Phase 2 code) | **After the audit remediation:** passed; hash `afef9c4e056797a8…` (R = 2) = verify run_a = run_b. Execution and reproducibility only: at smoke size, ARL₀ validation passed in **3 of 6** primary (and 0 of 2 diagnostic) chart × λ × replicate configurations, as expected for 60 paths; this is not production validation | `results/runs/smoke_20261014T025108_77623`, `results/runs/verify_20261014T025110_77720`. Pre-remediation pairs (hash `357f5c86…`): `smoke_20261014T014934_53384` / `verify_20261014T014936_53502` and `smoke_20261014T014802_51651` / `verify_20261014T014804_51730` |
| Pilot-report errata (A1–A8) | **All applied.** A2, A6–A8 on 14 Oct (session 2); **A1, A3, A4, A5 on 14 Oct (session 3)**, no rerun: A1 adds the 2 diagnostic rows; A3 labels M = 1 "by construction"; A4 states that M has no SE in the pilot; A5 adds X̂(k) point estimates derived exactly from stored P(D ≤ k) (SEs unavailable) | `docs/phase1_pilot_report.md` §6, §7, §8, §14 |
| SPY application | Not started; no data downloaded | `data/raw/` holds only `.gitkeep` |

**Git (read-only, 14 Oct 2026):**
- Branch `main`. **Phase 1 baseline commit:** `f77297b9a257bbe8ca80c858f6119219471925b8`, made by the user (author Stephen Pienaar; no trailers). Its parent is `2a06da8`.
- HEAD `3529ddd` ("feat: finalize production design (R=20, IC validation, provenance)", user commit; parent `9b286e1`, Phase 2). The production run used this commit. Post-production documentation edits (`CLAUDE.md`, this file, the skill) are **uncommitted** until the user commits. Untracked `.serena/` is development-tool state.
- `results/runs/` is git-ignored, so the pilot artifacts exist only locally. **Keep `pilot_20261013T075339_142070` safe.** Neither the Phase 1 committed source (slope normalisation) nor the current Phase 2 source (also new schemas, aggregation, paired intervals and reporting) reproduces its `results.json` bit-for-bit (see "Code ↔ canonical hash"). The original artifacts are the record.
- The user commits manually.

## Approvals and decisions

| Decision | Status | Source |
|---|---|---|
| Individual project (despite the rubric's "Group of 3") | **Approved** | User, 13 Oct 2026 |
| Full code in a GitHub repository; report appendix gives a concise description, reproduction steps and the link; no line limit | **Approved** | User, 13 Oct 2026 |
| MODIFY recommendation: three-chart comparison, frozen models, adaptation-masking investigation, pilot-first | **Approved** | User, 13 Oct 2026 |
| Primary simulation: GARCH(1,1)-t, α = 0.07, β = 0.91, ν = 6; ARL₀ = 500; λ = 0.1 (primary) / 0.2; τ = 50; δ ∈ {1.5, 2, 3} | **Approved** | User's session-closing statement, 13 Oct 2026 |
| Phase 1 (docs, implementation, tests, smoke, pilot) | **Authorized and completed** | User, 13 Oct 2026 |
| Five additional references in Zotero | **Done by the user** | User, 13 Oct 2026; verified via MCP |
| Production configuration (see production-plan.md): 2,000 calibration, 2,000 validation and 2,000 OOC paths per δ; in-control horizon 5,000; OOC horizon **H = 500**; 500 trees; **R = 10 preferred, subject to a small runtime benchmark** (superseded 14 Oct 2026: R = 20, amendment A); ARL₀ = 100 as a separately labelled sensitivity | **Stated by the user as the recommended configuration.** Execution **not authorized** | User's session-closing statement, 13 Oct 2026 |
| Preparation of corrections C1–C7 | **Authorized**, "subject to the instructions in the most recent production-preparation prompt" | User statement, 13 Oct 2026. **That prompt is not in this session's record**: confirm its contents with the user before starting |
| Production-preparation prompt (C1–C7 scope) | **Supplied by the user** in session 3; implementation plan **approved** with refinements | User, 14 Oct 2026 |
| Production and sensitivity master seed **20261014** (new; disjoint from the pilot's 20261013) | **Approved** | User, 14 Oct 2026 |
| Primary endpoints: 12 paired contrasts — RMD₅₀₀ and X(20), RF − GARCH and RF − conventional, λ = 0.1, δ ∈ {1.5, 2, 3}, each with its δ = 1 counterpart; "pre-specified after the exploratory pilot, before production" | **Approved** | User, 14 Oct 2026 |
| Normal paired SE with optional bootstrap check; X(k), k = 5, 20, 60; `--approved` guard | **Approved** (production-preparation prompt) | User, 14 Oct 2026 |
| Refinements: censoring-aware quantiles; explicit aggregation schema; pathwise T(δ) ≤ T(1) tested for the conventional chart only; alarm-day coding M vs M + 1 with boundary test; benchmark (R = 1, seed 20261013) labelled performance-only and excluded from inference; `--approved` never replaces authorization | **Required by the user**, implemented | User, 14 Oct 2026 |
| Phase 2 audit remediation (M1–M3, minor D1–D6), synchronization of `CLAUDE.md` §18 | **Authorized and done** | User's audit-remediation prompt, 14 Oct 2026 |
| Benchmark (R = 1, seed 20261013) | **Authorized and run once**, 14 Oct 2026 (`benchmark_20261014T041247_106190`); performance only; not to be repeated | User, 14 Oct 2026 |
| **Amendment A:** production R = 10 → 20; sensitivity matched (inherits) | **Approved** | User's final production-design prompt, 14 Oct 2026 |
| **Amendment B:** IC validation passes iff the whole independent-validation 95% CI lies in [A₀(1−ε), A₀(1+ε)], ε = 0.15; bounds exactly A₀(1 ± ε), robust inclusive comparison; labelled a post-pilot, post-benchmark amendment made before production; benchmark outcomes kept unchanged | **Approved** (with the refinement "no rounding in the scientific rule") | User, 14 Oct 2026 |
| Production failure-handling policy (run all 20; no discards, replacements or recalibration on validation; report all; flag failures; no nominal-calibration claim if any fail) | **Approved** | User, 14 Oct 2026 |
| Provenance: tracked changes, untracked source/configuration and `.serena/` tool state reported separately; no untracked file assumed harmless | **Approved and implemented** | User, 14 Oct 2026 |
| Full production run (R = 20, ARL₀ = 500), one run | **Authorized and run** (`production_20261014T060921_145897`); no reruns | User, 14 Oct 2026 ("START PRODUCTION … this one full ARL₀ = 500 production simulation") |
| ARL₀ = 100 sensitivity run, another production run, another benchmark, SPY download | **Not authorized** | User, 14 Oct 2026 ("Do not launch any additional production, sensitivity, benchmark or SPY experiment") |
| SPY design (Yahoo adjusted close, 1993–2006 training, 2007 to Sep 2026 monitoring, frozen models, descriptive alarms) | **Approved plan**; execution not authorized | User, 13 Oct 2026 |

**Recommendations still awaiting explicit user confirmation:**
1. *(Confirmed 14 Oct: normal paired SE.)*
2. *(Confirmed 14 Oct: X(k).)*
3. *(Confirmed 14 Oct: primary endpoints, with paired X(20) contrasts.)*
4. *(Confirmed 14 Oct: `--approved` guard.)*
5. How the SPY simulation-based UCL handles the 4th-moment check (see production-plan.md §SPY).
6. The SPY reference-date list must be pre-registered.

## Open issues

1. *(Resolved 14 Oct, session 3: C1–C7 implemented and verified; awaiting the user's commit.)*
2. *(Resolved 14 Oct, session 3: all pilot-report errata applied.)*
3. *(Resolved 14 Oct, session 3: the production-preparation prompt was supplied.)*
4. *(Resolved 13 Oct 2026: `CLAUDE.md` §18 updated and §19 session-continuity workflow added, at the user's request.)*
5. **SPY readiness (S1–S3):**
   - no data-integrity checks
   - `download_snapshot` relies on yfinance's `multi_level_index=True` default
   - no SPY pipeline: chronological tuning, refit and freeze, continuous filtering, simulation-based UCL
   - `sim.simulate` enforces the 4th-moment margin, which a SPY-fitted GARCH-t may fail
   - the reference dates are not yet written down
6. *(Resolved 14 Oct 2026: `CLAUDE.md` §18 synchronized at the user's request, covering 34 tests, the C2 wording, the baseline commit and the reproducibility caveat. §19 step 4 now names the production and Git gates.)*
7. *(Resolved for production, 14 Oct 2026: launched from clean committed `3529ddd`.)* **Source provenance.** The pilot came from uncommitted source. The wrapper now writes `source_sha256.txt` (implemented 14 Oct). Still required: launch benchmark, production and sensitivity from a **clean committed worktree**.
8. *(Resolved at production scale, 14 Oct 2026: OOC minus validation P(T<τ) is −0.0005 to −0.0033 across chart × λ, within Monte Carlo error.)* **Pre-change false-alarm check (A9).** In the pilot, the OOC P(T<τ) was 1.4–1.9 SE below the validation P(T<50). Recheck at production scale.
9. **Literature:**
   - MacGregor & Harris (1993) and Lu & Reynolds (1999) are metadata-only.
   - Lee, Park & Baek (2020) was mentioned in the user's session-closing prompt but **not discussed in this session and not in Zotero**; no details are verified.
10. *(Resolved 14 Oct, session 3: `CLAUDE.md` §18 synchronized at the user's request after the audit remediation.)*
11. *(Resolved, 14 Oct 2026: measured production peak RSS 1.74 GiB, no swap.)* **Memory headroom.** Estimated production peak RSS ≈ 1.4–1.8 GiB (upper ≈ 3 GiB, not measured); `free -m` showed ≈ 3.4 GiB available on 14 Oct. The benchmark measures it.
12. **Verification disclosure (session 3).** One guard check passed `--approved` on a real CLI call (`run.py production --approved --out <existing smoke dir>`); it was refused by the overwrite guard before any computation, as designed. Future guard checks with the flag use only the monkeypatched tests.

13. **Residual between-system SD σ̂_sys** is descriptive only (method of moments, truncated at 0, R = 20); it does not isolate training-sample variability.
14. **Multiplicity.** The 12 primary contrasts are not adjusted for multiple comparisons; the article must say so.
15. *(Resolved 14 Oct, session 3: the second independent audit confirmed M1 and M3 resolved and the M2 plotting fixes; its residual reporting and documentation findings were corrected and regression-tested.)*

16. *(Resolved 14 Oct 2026 by user decision before production: amendment B, the equivalence-style rule of methodology eq. 29, plus R = 20 and the failure policy. The benchmark's original-rule outcomes stay recorded unchanged. Original text follows.)* **Benchmark validation failures (decision needed before production).** At N = 2,000 the validation 95% CI is about ±4.3%, while the criterion ignores the Monte Carlo error of h* from the 2,000 calibration paths (similar size), so an unbiased calibration fails the CI part more often than 5% (about 17% per configuration if the two errors were independent), and charts share calibration and validation paths, so failures are correlated. The observed shortfalls (conventional and RF −5% to −8%, about −1.7 to −2.6 combined SE) may also reflect a systematic effect; not isolated. Options for the user, to be decided **before** production results are seen: keep the rule and report failures; pre-register a criterion that includes calibration error; or enlarge the calibration set (cost: ≈ +14 s per replicate per extra 2,000 paths). No change has been made.

### OPEN post-production tasks (14 Oct 2026; none started)

None of these needs new simulation. Do them in priority order.

| ID | Status | Task |
|---|---|---|
| **P1** | **OPEN — highest priority, next task** | **Independent production-results audit.** Recompute all 12 primary contrasts from `paths.npz` with an independent calculation that does **not** import `run`, `src.chart` or `src.aggregate` (plain NumPy/SciPy). Verify: matched survivor sets E_a ∩ E_b (T ≥ τ for both charts; T = 550 is censored, T = 549 a detection with D = H); restricted delays D_H = min(T − τ + 1, H); X(20) against the δ = 1 counterfactual; within-replicate normal paired SEs; the across-replicate t intervals (df 19); all 20 replicates represented; agreement with `results.json`. Report discrepancies; never edit the frozen run |
| **P2** | OPEN | **Multiplicity-aware interpretation.** Holm adjustment over the 12 primary contrasts, using replicate-level inference (one-sample t-tests of the 20 replicate contrasts, df 19). Keep the unadjusted estimates and CIs. Label it **post hoc and supplementary**: methodology §7.4 pre-registered no adjustment, and this was decided after the results were seen. No confirmatory overstatement |
| **P3** | OPEN | **Repair `fig_replicates.png`** (issue 17). The jitter `0.03·(r − (R−1)/2)` clips replicates 0 and 19 at δ = 1 and 3 when R = 20. Make it work for any R (needs a `src/report.py` change and a regression test). Regenerate **from the frozen `results.json` only** into a separate derived-output directory. Never overwrite the production artifacts; never rerun the simulation |
| **P4** | OPEN | **Descriptive heterogeneity investigation** (post hoc, descriptive). Why RF − GARCH contrasts vary across fitted systems (s_b 9.4–20.8 days): relate the per-replicate selected RF settings, forecast diagnostics (QLIKE, slope, corr, gap closure), masking M and paired delays, from `results.json`. **Never tune RF hyperparameters on production outcomes** |
| **P5** | OPEN | **Run-length distribution comparison.** Compare validation RL quantiles (q10/q50/q90), P(T ≤ 250) and P(T < τ) across schemes, and explain why equal mean ARL₀ need not imply identical RL distributions (e.g. dependence in u; conventional ACF₁ 0.13). Use stored data only: per-replicate validation summaries, and δ = 1 no-change alarm days in `paths.npz` (truncated at day 549). Per-path validation run lengths are **not stored**; report that limitation, and do not invent or re-simulate |
| **P6** | OPEN — **not authorized** | Later experiments: the ARL₀ = 100 sensitivity run and the SPY application (with SPY preparation items S1–S3, issue 5). Neither starts in a future session without the user's explicit authorization |

## Next recommended task

**P1 (independent production-results audit)**, then P2–P5 in order, with no new simulation. Production reruns, the ARL₀ = 100 sensitivity, further benchmarks and SPY are **not authorized**. The earlier task notes below are kept for history.

**Scientific results audit of `production_20261014T060921_145897`** (user review), then the user's decision on the figure defect (issue 17) and on the ARL₀ = 100 sensitivity run (not authorized). Earlier text:

**Await the user's commit of the final production-design changes, then the mandatory production warning and explicit authorization.** Production (R = 20), the ARL₀ = 100 sensitivity, another benchmark and SPY remain not authorized. Launch only from a clean worktree (`git_tracked_modified: no`, `git_untracked_unclassified: none`, `git_ignored_python: none`). Before the run, give the mandatory production warning (configuration, R, paths, horizons, trees, measured runtime with upper bound, RAM/CPU, output path, interruption and overwrite behaviour) and wait for explicit authorization of production and, separately, of the ARL₀ = 100 sensitivity.

## Timeline (from research_plan.md, adjusted)

| Date | Plan |
|---|---|
| 14–18 Oct | Corrections C1–C7, benchmark, production authorization |
| 19–22 Oct | Production and sensitivity runs; SPY snapshot and application (if authorized); results freeze |
| 15–23 Oct | Draft Introduction, Background, Method |
| 23–31 Oct | Results, Application, Conclusion, Abstract, Appendix |
| 1–3 Nov | Trace every number, proofread, AI declaration, Turnitin |
| **4 Nov** | Submit (deadline 5 Nov 23:59) |

## Update log

| Date | Milestone | Artifacts / files | Tests | Open issues | Next task | Approval status |
|---|---|---|---|---|---|---|
| 2026-10-13 | Research assessment; plan v2; Zotero refs added by user and verified | `docs/*.md` | – | – | Phase 1 | Phase 1 authorized |
| 2026-10-13 | Phase 1 complete: code, tests, smoke, verify, reduced pilot | `results/runs/pilot_20261013T075339_142070` (`f92f0715…`), `docs/phase1_pilot_report.md` | 29 passed | A1–A12, C1–C7 | Readiness review | Production not authorized |
| 2026-10-13 | Production-readiness review delivered (CORRECTIONS REQUIRED); continuation skill created | `.claude/skills/stc720-project/` | 29 passed (re-run 08:51) | C1–C7 not started; prep prompt unrecorded | Confirm prep scope, then C1–C7 | Preparation authorized (per user); production, sensitivity and SPY **not** authorized |
| 2026-10-13 | Continuity housekeeping: status record moved to `docs/project-status.md`; `CLAUDE.md` §18 updated, §19 added; skill links updated | `docs/project-status.md`, `CLAUDE.md`, `.claude/skills/stc720-project/` | not re-run (no code changes) | as above | Confirm prep scope, then C1–C7 | unchanged |
| 2026-10-14 | Independent-audit remediation (M1–M3 + 9 small fixes); no pilot rerun | `run.py`, `src/forecast.py`, `src/report.py`, `tests/test_core.py`, `setup.sh`, `docs/phase1_pilot_report.md`, `docs/methodology.md`, skill refs; new runs `smoke_20261014T002849_20414` (`5e84db38…`), `verify_20261014T002855_20527` (identical) | **34 passed** | C1–C7; A1/A3–A5 errata; CLAUDE.md §18 stale; provenance recommendation | User review and initial commit; then confirm C1–C7 scope | Production, sensitivity, R = 10 benchmark, SPY **not** authorized |
| 2026-10-14 | User committed the Phase 1 baseline `f77297b`; `CLAUDE.md` §18 synchronized (§19 step 4: gates named); documentation only | `CLAUDE.md`, `docs/project-status.md` | not re-run (no code changes; 34 collected; committed tree = verified tree) | C1–C7; A1/A3–A5 errata; provenance recommendation | Confirm the production-preparation scope, then C1–C7 | Production, sensitivity, R = 10 benchmark, SPY **not** authorized |
| 2026-10-14 | **Phase 2 preparation C1–C7 implemented and verified** (session 3, on `87c4dc7`, uncommitted): guarded `production` / `sensitivity_arl100` / `benchmark`; per-path `paths.npz`; X(k), normal paired SE, censoring-aware quantiles, masking SE; equal-weight replicate aggregation with explicit schema; report rewrite; methodology v1.2; errata A1, A3–A5; wrapper `source_sha256.txt` | `run.py`, `src/chart.py`, `src/aggregate.py` (new), `src/report.py`, `scripts/run_simulation.sh`, `tests/test_core.py`, `docs/methodology.md`, `docs/phase1_pilot_report.md`, skill refs; runs `smoke_20261014T014934_53384` (`357f5c86…`), `verify_20261014T014936_53502` (identical) | **58 passed** | CLAUDE.md §18 stale; memory headroom; clean-worktree launch | User review and commit; then benchmark authorization | Benchmark, production, sensitivity, SPY **not** authorized |
| 2026-10-14 | **Phase 2 independent audit remediated** (Codex CLI: 3 major findings, no critical errors): M1 empty survivor sets, M2 unidentified points in figures, M3 relabelled residual between-system variance; minor D1–D6; `CLAUDE.md` §18 synchronized | `src/chart.py`, `src/aggregate.py`, `src/report.py`, `run.py`, `tests/test_core.py`, `docs/methodology.md` v1.3, `CLAUDE.md`, skill refs; runs `smoke_20261014T025108_77623` (`afef9c4e…`), `verify_20261014T025110_77720` (identical) | **65 passed** | independent recheck pending; multiplicity; unmeasured runtime and memory | Independent recheck; user commit; then benchmark authorization | Benchmark, production, sensitivity, SPY **not** authorized |
| 2026-10-14 | **Second Phase 2 audit: final reporting corrections** (M1, M3 confirmed resolved; M2 plots confirmed): `n/i` vs `–` vs valid zero in report cells (`stat`, `zero_cell`); δ = 1 X(k) cells read stored estimands (n/i when no survivor); mode-sensitive headings (`STATUS`); historical reproducibility wording (Phase 1 slope fix vs Phase 2 schema changes); `P(late ∣ D>20)` header no longer breaks the Markdown table; two-line figure title | `src/report.py`, `tests/test_core.py`, `CLAUDE.md`, `docs/project-status.md`, `docs/phase1_pilot_report.md`, `reproducibility.md`, `SKILL.md`; runs `smoke_20261014T034755_98486`, `verify_20261014T034757_98595` (hash `afef9c4e…`, `results.json` unchanged) | **72 passed** | multiplicity; unmeasured runtime and memory | User commit review; then benchmark authorization | Benchmark, production, sensitivity, SPY **not** authorized |
| 2026-10-14 | **Production-scale performance benchmark executed** (authorized; R = 1, seed 20261013, 500 trees; HEAD `9b286e1`) | `results/runs/benchmark_20261014T041247_106190` (`77e20ffa…`) | not re-run (no code change) | validation 2/6 primary passed (conventional and RF −5% to −8%); decision on validation criterion | User decision on issue 16; production warning | Production, sensitivity, SPY **not** authorized |
| 2026-10-14 | **Final production design prepared** (user-approved plan + 2 refinements): R = 20 (sensitivity matched); amended IC validation rule eq. 29 (exact inclusive bounds A₀(1 ± ε)); failure policy; provenance classification (`scripts/git_provenance.sh`); benchmark original outcomes unchanged | `run.py`, `src/chart.py`, `src/report.py`, `scripts/run_simulation.sh`, `scripts/git_provenance.sh` (new), `tests/test_core.py`, `docs/methodology.md` v1.4, `docs/research_plan.md`, skill refs, `CLAUDE.md`; runs `smoke_20261014T053655_132590`, `verify_20261014T053658_132710` (`0ff5992f…`) | **80 passed** | multiplicity; validation rule conditional on h*; runtime extrapolated | User commit; production warning; explicit authorization | Production (R = 20), sensitivity, another benchmark, SPY **not** authorized |
| 2026-10-14 | **First full production run** (authorized; R = 20, seed 20261014, HEAD `3529ddd`, clean): exit 0, 16:26.7 wall, 1.74 GiB peak; IC validation 160/160 | `results/runs/production_20261014T060921_145897` (`44410144…`) | 80 passed (preflight) | issue 17 (figure jitter at R = 20); multiplicity; RF − GARCH heterogeneity across replicates | Scientific results audit | Sensitivity, further production, benchmark, SPY **not** authorized |
| 2026-10-14 | **End-of-session synchronization** (documentation only): production milestone and findings recorded; open tasks P1–P6; `CLAUDE.md` §18–19, skill and references updated; new `references/production-results.md` | `CLAUDE.md`, `docs/project-status.md`, `.claude/skills/stc720-project/SKILL.md`, `references/{production-results (new), scientific-design, production-plan, reproducibility}.md`; production `44410144…` re-verified, 424 run files unchanged | not run (no code change) | P1–P6 OPEN | P1 independent audit | Sensitivity, further production or benchmark, SPY **not** authorized |
