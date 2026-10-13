# Project status — verified record

*Authoritative progress record for the STC 720 project. It is read at the start of every session through the `stc720-project` skill ([`.claude/skills/stc720-project/SKILL.md`](../.claude/skills/stc720-project/SKILL.md)) and `CLAUDE.md` §19.*

*Last updated: **2026-10-14** (session 2: independent-audit remediation, then the user's Phase 1 commit `f77297b` and `CLAUDE.md` §18 synchronization). The remediation was verified by:*
- *`pytest -q`: 34 passed*
- *`scripts/run_simulation.sh smoke` and `verify`: both exit 0, identical hashes*
- *SHA-256 re-check of all 104 pre-existing `results/runs/` files*
- *read-only `git status`*

## Verified checkpoint

**Stage:**
- Phase 1 is **complete and verified**.
- The production-readiness review has been **delivered**.
- The **independent (Codex CLI) audit remediation is complete** (14 Oct 2026). Its verdict was "corrections required before commit".
- Production corrections C1–C7 have **not been started**.
- **The user committed the verified Phase 1 baseline:** `f77297b9a257bbe8ca80c858f6119219471925b8` ("feat: add RF-EWMA simulation pipeline and verified Phase 1 pilot"). This tree is the one verified with 34 passing tests. Phase 2 preparation has not begun.

| Item | Verified state | Evidence |
|---|---|---|
| Planning docs | Done | `docs/research_plan.md`, `docs/methodology.md` (eqs. 1–22), `docs/references.md` |
| Core code | Done (Phase 1 scope) | `src/sim.py`, `src/forecast.py`, `src/chart.py`, `src/report.py`, `src/spy.py` (data utilities only), `run.py` (modes `smoke`, `pilot`, `production` [refuses: `CONFIGS["production"] is None`], `verify`) |
| Wrapper | Done | `scripts/run_simulation.sh` (GNU time, logs, exit status, provenance, thread limits, read-only Git) |
| Tests | **34 passed**: 29 original + 5 new (slope normalisation; overwrite refusal ×3 modes; fresh wrapper directory) (`.venv/bin/python -m pytest -q`, 14 Oct 2026) | `tests/test_core.py`, `pytest.ini` |
| Smoke + verify | Passed after remediation; smoke hash `5e84db38…`, verify identical | `results/runs/smoke_20261014T002849_20414`, `results/runs/verify_20261014T002855_20527/verify.txt` (13 Oct runs kept) |
| Audit remediation (14 Oct) | **Done.** M1 statistical reporting; M2 RF-slope interpretation; M3 overwrite guard; small fixes 1–9. The pilot was **not rerun**; the canonical artifacts are unchanged (104/104 files hash-identical) | `docs/phase1_pilot_report.md` §14 (revision log); `run.py` `refuse_overwrite`; `src/forecast.py` `slope`; `src/report.py`; `setup.sh`; `docs/methodology.md` v1.1; skill references |
| Code ↔ canonical hash | The canonical `f92f0715…` came from **uncommitted pre-remediation source** (HEAD `2a06da8`, dirty). The remediation changed one numerical output: `slope_h` is now ×(n−1)/n. At smoke scale exactly 3 `slope_h` leaves differed (ratio (n−1)/n) and all other leaves were bit-identical. A pilot rerun with the committed source (`f77297b`) is expected to give a different hash; it was not rerun | scratch comparison, 14 Oct |
| Reduced pilot | Done; all criteria Q1–Q6 met | **Canonical run:** `results/runs/pilot_20261013T075339_142070` (hash `f92f07159b682406ef0ca8bd52c0e64e8eed38a795784b7ec8e9549c17b01bb7`; three identical runs). Summary: `docs/phase1_pilot_report.md` |
| Production-readiness review | Delivered **in chat only** (not saved in `docs/`); verdict **CORRECTIONS REQUIRED** | Content preserved in [production-plan.md](../.claude/skills/stc720-project/references/production-plan.md) |
| Corrections C1–C7 | **Not started** | Re-checked 14 Oct (`grep`: no `excess_detection`, `masking_se` or `--approved`). Verified 13 Oct: `run.py` has `"production": None`; `chart.paired_diff` still uses the bootstrap; there is no `excess_detection` or `masking_se`; `report.py` summarises replicate 0 only |
| Pilot-report errata (A1–A8) | **Partly applied (14 Oct).** Done: A2, A6, A7 and A8; A1 has a pointer to the diagnostic rows. **Pending (C7):** A1 full table, A3 ("M = 1 by construction" label), A4 (M SE) and A5 (X(k)) | `docs/phase1_pilot_report.md` §7, §9, §14 |
| SPY application | Not started; no data downloaded | `data/raw/` holds only `.gitkeep` |

**Git (read-only, 14 Oct 2026):**
- Branch `main`. **Phase 1 baseline commit:** `f77297b9a257bbe8ca80c858f6119219471925b8`, made by the user (author Stephen Pienaar; no trailers). Its parent is `2a06da8`.
- Before this synchronization the working tree was clean, apart from untracked `.serena/` (tool state, not project work).
- The `CLAUDE.md` §18–19 and status-record synchronization is uncommitted until the user commits it.
- `results/runs/` is git-ignored, so the pilot artifacts exist only locally. **Keep `pilot_20261013T075339_142070` safe.** The current code would regenerate it except for the `slope_h` normalisation, so the hash would differ (see "Code ↔ canonical hash").
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
| Full production run, ARL₀ = 100 run, SPY download | **Not authorized** | – |
| SPY design (Yahoo adjusted close, 1993–2006 training, 2007 to Sep 2026 monitoring, frozen models, descriptive alarms) | **Approved plan**; execution not authorized | User, 13 Oct 2026 |

**Recommendations still awaiting explicit user confirmation:**
1. Within-replicate paired contrasts use a normal paired SE instead of the bootstrap.
2. Baseline-adjusted excess detection X(k) is added as a primary metric.
3. Primary endpoints are pre-specified: paired RMD₅₀₀ contrasts RF − GARCH and RF − conventional, and X(20), at λ = 0.1.
4. A code-level `--approved` guard is required for production and sensitivity modes.
5. How the SPY simulation-based UCL handles the 4th-moment check (see production-plan.md §SPY).
6. The SPY reference-date list must be pre-registered.

Items 1–3 are implied by the user's C1–C7 list; confirm them when preparation starts.

## Open issues

1. **C1–C7** not implemented (production-plan.md).
2. **Pilot-report errata:** A2 and A6–A8 were applied on 14 Oct. **A1, A3, A4 and A5 are pending (C7).**
3. **The production-preparation prompt** the user referred to is not recorded here; ask for it.
4. *(Resolved 13 Oct 2026: `CLAUDE.md` §18 updated and §19 session-continuity workflow added, at the user's request.)*
5. **SPY readiness (S1–S3):**
   - no data-integrity checks
   - `download_snapshot` relies on yfinance's `multi_level_index=True` default
   - no SPY pipeline: chronological tuning, refit and freeze, continuous filtering, simulation-based UCL
   - `sim.simulate` enforces the 4th-moment margin, which a SPY-fitted GARCH-t may fail
   - the reference dates are not yet written down
6. *(Resolved 14 Oct 2026: `CLAUDE.md` §18 synchronized at the user's request, covering 34 tests, the C2 wording, the baseline commit and the reproducibility caveat. §19 step 4 now names the production and Git gates.)*
7. **Source provenance.** The pilot came from uncommitted source. Recommended for future runs: run from a clean committed worktree, plus one wrapper line `sha256sum … > source_sha256.txt` (production-plan.md §Source provenance). Not implemented.
8. **Pre-change false-alarm check (A9).** In the pilot, the OOC P(T<τ) was 1.4–1.9 SE below the validation P(T<50). Recheck at production scale.
9. **Literature:**
   - MacGregor & Harris (1993) and Lu & Reynolds (1999) are metadata-only.
   - Lee, Park & Baek (2020) was mentioned in the user's session-closing prompt but **not discussed in this session and not in Zotero**; no details are verified.

## Next recommended task

**Phase 2 preparation:** confirm with the user the instructions of the "production-preparation prompt". Then implement C1–C7 (production-plan.md), including the `--approved` guard, and update the docs and pilot-report errata. Next, run `pytest`, `scripts/run_simulation.sh smoke` and `verify` only. Then:
- report back
- request authorization for the R = 10 runtime benchmark (if not already granted)
- request authorization for production and for the ARL₀ = 100 sensitivity

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
