# Project status — verified record

*Authoritative progress record for the STC 720 project. It is read at the start of every session through the `stc720-project` skill ([`.claude/skills/stc720-project/SKILL.md`](../.claude/skills/stc720-project/SKILL.md)) and `CLAUDE.md` §19.*

*Last updated: **2026-10-14** (session 3: Phase 2 production preparation C1–C7, then remediation of the independent Codex CLI audit of Phase 2; HEAD `87c4dc7`; all uncommitted). The remediation was verified by:*
- *`.venv/bin/python -m pytest -q`: **72 passed** (34 Phase 1 + 24 Phase 2 + 7 audit-remediation + 7 report-cell regression tests), after the final reporting corrections from the second audit*
- *the audit's crashes (M1 truncated schema and KeyError, M1 pairing-check bypass, M2 figure KeyError) reproduced before the fix and absent after it*
- *`scripts/run_simulation.sh smoke` and `verify`: both exit 0; hash `afef9c4e…` identical in smoke and both verify runs. Against the pre-remediation smoke (`357f5c86…`): every per-replicate value is bit-identical; the aggregate is identical after the `var_train`/`sd_train` key rename (195 t-CIs bit-identical)*
- *earlier in session 3 (C1–C7): `smoke` and `verify` passed with hash `357f5c86…`*
- *guard checks: `run.py` and the wrapper refuse `production`, `sensitivity_arl100` and `benchmark` without `--approved`; overwrite refusal on existing run directories*
- *independent recomputation (plain NumPy/SciPy, no `src/` imports) of per-replicate estimators from `paths.npz` and of the replicate aggregates: max discrepancy 0*
- *SHA-256 re-check of all pre-existing `results/runs/` files (138 from the session start, 222 before the remediation): 0 changed; canonical pilot hash `f92f0715…`*
- *read-only `git status` / `git diff --check`*

## Verified checkpoint

**Stage:**
- Phase 1 is **complete and verified**.
- The production-readiness review has been **delivered**.
- The **independent (Codex CLI) audit remediation is complete** (14 Oct 2026). Its verdict was "corrections required before commit".
- **The user committed the verified Phase 1 baseline:** `f77297b9a257bbe8ca80c858f6119219471925b8` ("feat: add RF-EWMA simulation pipeline and verified Phase 1 pilot"), then `87c4dc7` (docs synchronization).
- **Phase 2 production preparation (C1–C7) is implemented and verified (14 Oct 2026, session 3)**, from the user's production-preparation prompt and the approved implementation plan with the user's refinements (below). **Uncommitted** until the user commits. Benchmark, production, sensitivity and SPY were **not run**.
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
| Tests | **72 passed** (`.venv/bin/python -m pytest -q`, 14 Oct 2026, session 3, after the final reporting corrections): 34 Phase 1 tests unchanged + 24 Phase 2 tests (one updated for the M3 key rename) + 7 audit-remediation regression tests + 7 report-cell regression tests (δ = 1 X(k) n/i vs valid zero; one-survivor SE n/i; inapplicable –; mode-sensitive headings for production, sensitivity, benchmark, smoke). Phase 2 tests (alarm-day boundary incl. `paths.npz` round trip; X(k); CRN-pairing check; censoring-aware quantiles; normal paired SE vs bootstrap; masking delta-method SE vs replication SD; aggregation formulas, equal weights, schema allowlist; conventional-only monotonicity and M ≡ 1; recomputation from `paths.npz`; 2-replicate reproducibility; config values; guards ×3 modes in run.py and wrapper; overwrite refusal with `--approved`). Six deliberate code mutations were each caught | `tests/test_core.py`, `pytest.ini` |
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
- HEAD `87c4dc7` (docs synchronization, user commit). Session 3 changes are **uncommitted**: 13 modified files (including `CLAUDE.md` §18, synchronized at the user's request in the audit-remediation prompt) plus new `src/aggregate.py`; untracked `.serena/` is tool state, not project work.
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
| Production configuration (see production-plan.md): 2,000 calibration, 2,000 validation and 2,000 OOC paths per δ; in-control horizon 5,000; OOC horizon **H = 500**; 500 trees; **R = 10 preferred, subject to a small runtime benchmark**; ARL₀ = 100 as a separately labelled sensitivity | **Stated by the user as the recommended configuration.** Execution **not authorized** | User's session-closing statement, 13 Oct 2026 |
| Preparation of corrections C1–C7 | **Authorized**, "subject to the instructions in the most recent production-preparation prompt" | User statement, 13 Oct 2026. **That prompt is not in this session's record**: confirm its contents with the user before starting |
| Production-preparation prompt (C1–C7 scope) | **Supplied by the user** in session 3; implementation plan **approved** with refinements | User, 14 Oct 2026 |
| Production and sensitivity master seed **20261014** (new; disjoint from the pilot's 20261013) | **Approved** | User, 14 Oct 2026 |
| Primary endpoints: 12 paired contrasts — RMD₅₀₀ and X(20), RF − GARCH and RF − conventional, λ = 0.1, δ ∈ {1.5, 2, 3}, each with its δ = 1 counterpart; "pre-specified after the exploratory pilot, before production" | **Approved** | User, 14 Oct 2026 |
| Normal paired SE with optional bootstrap check; X(k), k = 5, 20, 60; `--approved` guard | **Approved** (production-preparation prompt) | User, 14 Oct 2026 |
| Refinements: censoring-aware quantiles; explicit aggregation schema; pathwise T(δ) ≤ T(1) tested for the conventional chart only; alarm-day coding M vs M + 1 with boundary test; benchmark (R = 1, seed 20261013) labelled performance-only and excluded from inference; `--approved` never replaces authorization | **Required by the user**, implemented | User, 14 Oct 2026 |
| Phase 2 audit remediation (M1–M3, minor D1–D6), synchronization of `CLAUDE.md` §18 | **Authorized and done** | User's audit-remediation prompt, 14 Oct 2026 |
| Benchmark, full production run, ARL₀ = 100 run, SPY download | **Not authorized** | User, 14 Oct 2026 ("Do not run the benchmark, production, sensitivity experiment or SPY application"; repeated in the audit-remediation prompt) |
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
7. **Source provenance.** The pilot came from uncommitted source. The wrapper now writes `source_sha256.txt` (implemented 14 Oct). Still required: launch benchmark, production and sensitivity from a **clean committed worktree**.
8. **Pre-change false-alarm check (A9).** In the pilot, the OOC P(T<τ) was 1.4–1.9 SE below the validation P(T<50). Recheck at production scale.
9. **Literature:**
   - MacGregor & Harris (1993) and Lu & Reynolds (1999) are metadata-only.
   - Lee, Park & Baek (2020) was mentioned in the user's session-closing prompt but **not discussed in this session and not in Zotero**; no details are verified.
10. *(Resolved 14 Oct, session 3: `CLAUDE.md` §18 synchronized at the user's request after the audit remediation.)*
11. **Memory headroom.** Estimated production peak RSS ≈ 1.4–1.8 GiB (upper ≈ 3 GiB, not measured); `free -m` showed ≈ 3.4 GiB available on 14 Oct. The benchmark measures it.
12. **Verification disclosure (session 3).** One guard check passed `--approved` on a real CLI call (`run.py production --approved --out <existing smoke dir>`); it was refused by the overwrite guard before any computation, as designed. Future guard checks with the flag use only the monkeypatched tests.

13. **Residual between-system SD σ̂_sys** is descriptive only (method of moments, truncated at 0, R = 10); it does not isolate training-sample variability.
14. **Multiplicity.** The 12 primary contrasts are not adjusted for multiple comparisons; the article must say so.
15. *(Resolved 14 Oct, session 3: the second independent audit confirmed M1 and M3 resolved and the M2 plotting fixes; its residual reporting and documentation findings were corrected and regression-tested.)*

## Next recommended task

**Await the user's commit review, then benchmark authorization.** After the user commits session 3 (clean worktree), and only with explicit authorization: `scripts/run_simulation.sh benchmark --approved` (R = 1, production sizes, seed 20261013; performance evidence only; proposal in production-plan.md). Then give the mandatory production warning (configuration, R, paths, horizons, trees, measured runtime with upper bound, RAM/CPU, output path, interruption and overwrite behaviour) and wait for explicit authorization of production and, separately, of the ARL₀ = 100 sensitivity.

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
