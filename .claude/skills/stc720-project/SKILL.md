---
name: stc720-project
description: Resume and continue the STC 720 (University of Pretoria) Random Forest–EWMA financial-volatility monitoring research assignment in this repository. Use at the start of any session in stc720-rf-ewma, or whenever the user asks to resume, continue, check status, prepare or run production or sensitivity simulations, work on the SPY application, methodology, literature/Zotero, results or the report. Gives the verified project status, approval gates, scientific invariants and the safe continuation workflow.
---

# STC 720 RF–EWMA — project continuation

**Project:** individual STC 720 research article (University of Pretoria), *Random Forest–EWMA Monitoring of Financial Market Volatility: A Simulation Study with an S&P 500 Application*.
**Due:** Thu **5 Nov 2026, 23:59 SAST**, via ClickUP. Internal target is to submit on 4 Nov. Turnitin similarity must be ≤ 20%, and a generative-AI declaration goes below the keywords.
**Repository:** `/home/stephen/projects/stc720-rf-ewma` (Python 3.14.4, `.venv/`, WSL2).

## Current stage (27 Oct 2026): P1–P5 DONE; SPY STOPPED AT THE GATE; MODEL B APPROVED; FINITE-VARIANCE CALIBRATION IMPLEMENTED; RELAUNCH NOT AUTHORIZED

- **SPY finite-variance calibration IMPLEMENTED (27 Oct 2026; code and synthetic tests only; post-stop refinement). Model B (variance-targeted GARCH-t) was approved by the user as the fixed SPY specification. `sim.simulate(..., need_m4=False)` is an explicit opt-in used only by `run.SPY['finite_variance_simulation']`; the strict default is bit-identical to committed code. Diagnostics a–i are fixed in `run.SPY['diagnostics']`. Target: the restricted mean run length E[min(T, 5000)] = 500, not E[T]. Tests: 133 passed. Criterion e refined (user decision, 27 Oct 2026, **before any SPY calibration**). These remain **hard stops**: a non-finite or non-positive h*, a failed minimality condition (restricted ARL(h*) ≥ 500 > restricted ARL(h*(1 − 10⁻⁶))), an inconsistent restricted-mean computation, and failed bracketing or bisection (`CalibrationError`). Only the overshoot |restricted ARL(h*)/500 − 1| > 10⁻³ became a **recorded warning** (`e_overshoot`), keeping the exact overshoot, achieved restricted ARL, target deviation and status in `results.json`. Justification: in the frozen production run, 24 of 160 calibrations exceeded 10⁻³ (maximum 0.16%) through the discreteness of the empirical ARL. There is no recalibration, no seed change and no selective rerun, and validation is unchanged. **SPY calibration and relaunch NOT authorized; the SPY application is NOT complete**.**

- **SPY variance-targeting remediation (training only; post-stop refinement, 27 Oct 2026; `docs/spy_vt_remediation.md`): the variance-targeted GARCH-t (`forecast.fit_garch_vt`, selected only by `run.SPY['garch_estimator']`) gives ω 0.00513, α 0.0593, β 0.9363, ν 7.63. Its implied variance equals s² (1.144), against 1.920 unrestricted, at a likelihood cost of 0.24, with practically identical training ĥ. It **still fails the fourth-moment gate** (m4 1.0039; E r⁴ = ∞). A finite-variance calibration option, diagnostics a–i and a relaunch are **NOT authorized**. **The SPY application is NOT complete**.**

- The scientific architecture and configuration are **frozen**. Phase 1 (pilot) and Phase 2 (production preparation, audits, final R = 20 design) are complete and committed (production source `3529ddd`). The post-production docs are committed as `fb73ecd`, P1 as `53552a9`, P2 as `9e9c30a`, and P3 as `8ef46aa`, the current HEAD (verified 27 Oct 2026).
- The R = 20, ARL₀ = 500 production run is complete and **frozen**: `results/runs/production_20261014T060921_145897/`, results hash `44410144…`. Its numbers, hashes and caveats are in [references/production-results.md](references/production-results.md). **P1 independent audit: PASS (27 Oct 2026; `docs/p1_audit_report.md`).**
  - 1,768/1,768 primary comparisons were bit-identical, 518/518 integrity and design checks passed, and the frozen artifacts are unchanged.
  - P1 verified the downstream calculations from the stored alarm times, **not** the upstream simulation.
- **P2 supplementary post hoc Holm analysis: PASS (27 Oct 2026; `docs/p2_multiplicity_report.md`). Holm (FWER 0.05, two-sided t₁₉, family of 12) rejects 6/12: all six RF − conventional contrasts. No RF − GARCH contrast is rejected; RF − GARCH RMD₅₀₀ has Holm p = 0.0533 at each δ (unadjusted p 0.009–0.011). The unadjusted primary estimates and CIs are unchanged.**
- **P3 figure repair: PASS (27 Oct 2026; `docs/p3_figure_report.md`). The fixed 0.03 jitter hid 4 replicate points per RMD panel and 2 per X(20) panel outside the axes at R = 20, and mixed the δ = 1.5 and δ = 2 clouds. Plotting-only fix `report.jitter`. The repaired figure is `results/derived/p3_figures/fig_replicates.png` (`6e4fbcde…`); the original `1af6a110…` is untouched. 41/41 checks: all 280 plotted replicate values equal the stored values, and the means and CIs equal the stored values.**
- **P4/P5 exploratory diagnostics: DONE (27 Oct 2026; `docs/p45_diagnostics_report.md`; descriptive, post hoc). P4: RF − GARCH between-system spread is 3.4–8.2× the MC SE under a change (1.2× at δ = 1) and stable within systems (ρ 0.85–0.97); the strongest association is with the masking gap (ρ −0.80 to −0.89); no pattern by RF cell. P5: equal ARL₀, different shapes: the conventional chart is over-dispersed (CV 1.04) with P(T < τ) 0.125, against a geometric 0.093; GARCH and the oracle are near-geometric; survivor conditioning is non-neutral, which is consistent with the −3.8-day RF − conventional δ = 1 baseline.**
- **Priorities now: (1) the SPY application** (rubric §5, Illustrative example, within the 35-mark results block). It needs the user's explicit authorization and preparation items S1–S3. **(2) The final research paper.** **The ARL₀ = 100 sensitivity is DEFERRED** (user, 27 Oct 2026): not authorized, and not permanently dropped.
- The task list is in `docs/project-status.md`.
- **No further simulation is authorized**: no production rerun, sensitivity, benchmark or SPY.

## Authority order

1. The user's instructions in the **current** session.
2. [`CLAUDE.md`](../../../CLAUDE.md) for policy, scope and the Git rules. §18 summarises the status and §19 gives the session-continuity workflow. The detailed record is `docs/project-status.md`.
3. [`docs/project-status.md`](../../../docs/project-status.md) (the status record) for progress, approvals and next task. **Always verify it against the repository.**
4. Scientific definitions: [`docs/methodology.md`](../../../docs/methodology.md), [`docs/research_plan.md`](../../../docs/research_plan.md), [`docs/references.md`](../../../docs/references.md).
5. The other reference files of this skill.

## Resume workflow (do this in order)

1. Read `CLAUDE.md`.
2. Read this skill, the status record [`docs/project-status.md`](../../../docs/project-status.md) and the frozen-results reference [references/production-results.md](references/production-results.md).
3. Inspect the repository using **read-only** commands only: `git status --short`, `git log --oneline -10`, `git diff --stat`, `ls results/runs/`, and the files named in the status record.
4. Identify the latest **verified** stage. Compare what the status record says with what the code actually contains; grep for the functions or configs a task should have added.
5. Separate completed work (tested, verified, recorded) from planned or partial work. Mark anything unclear as **unverified**.
6. Identify the next **authorized** task from the approval table in the status record.
7. Give the user a brief summary: verified stage, open items, next authorized task, and pending decisions.
8. **Ask for approval** before anything outside the authorized scope (see the gates below).
9. Continue from the verified checkpoint. Afterwards, update the status record (see "Keeping the status current").

## Hard invariants

- **No expensive or external runs without explicit approval in the current session.** This covers `python run.py production`, `scripts/run_simulation.sh production`, the ARL₀ = 100 sensitivity run, any further benchmark (the single authorized one ran on 14 Oct 2026), and any SPY download (`src/spy.download_snapshot`). Approval from an earlier session does not carry over unless the status record says so explicitly.
- **Git: read-only only.** You may use `status`, `diff`, `log`, `show`, `ls-files`, `rev-parse`, `branch --show-current`. Never `add`, `commit`, `push`, `pull`, `fetch`, `merge`, `rebase`, `reset`, `restore`, `checkout`, `switch`, `stash`, `clean` or `tag`, and never change Git config or hooks. **Never add AI co-author or attribution trailers.** At a milestone, suggest a commit message; the user commits.
- **Never overwrite or delete simulation evidence** in `results/runs/`. Each run goes to a new directory via `scripts/run_simulation.sh`. Frozen evidence:
  - canonical pilot `results/runs/pilot_20261013T075339_142070` (`f92f0715…`)
  - benchmark `benchmark_20261014T041247_106190` (`77e20ffa…`)
  - **production `production_20261014T060921_145897` (`44410144…`)**

  Derived outputs (audits, repaired figures) go to a separate directory and are computed from the frozen files, never by re-simulating.
- **Do not silently change the approved scientific design.** Proposals go to the user. Never tune parameters to rescue weak results. Report negative or mixed results as they are.
- **A task is "complete" only when** the code exists, the relevant tests pass, the outputs have been checked, and the status record is updated. Code written but not yet verified is "in progress".
- **Literature:** never attribute equations, results or conclusions to the metadata-only papers (MacGregor & Harris 1993; Lu & Reynolds 1999). Never invent references, DOIs or quotes.
- **Keep production guarded.** `production`, `sensitivity_arl100` and `benchmark` refuse without `--approved` (in `run.py` and in the wrapper). The flag never replaces the user's explicit authorization in the current session.
- New dependencies, trading or backtesting code, and extra ML models are out of scope without approval.

## Approval gates (summary; details in the status record)

| Work | Status (14 Oct 2026) |
|---|---|
| Phase 1 (docs, code, tests, smoke, pilot) | **Done and verified** |
| Preparing production corrections C1–C7 | **Done, verified and committed** by the user (`9b286e1`, 14 Oct 2026) |
| Final production design (R = 20, amended IC validation rule eq. 29, failure policy, provenance classification) | **Done, verified and committed** by the user (`3529ddd`, 14 Oct 2026; 80 tests) |
| Full production simulation (R = 20, ARL₀ = 500) | **Complete and frozen** (run once, authorized 14 Oct 2026; `production_20261014T060921_145897`, hash `44410144…`). **No rerun authorized** |
| Post-production analysis P1–P5 (independent audit, Holm, figure repair, heterogeneity, run-length comparison; no new simulation) | **P1–P5 DONE (27 Oct 2026).** Code changes (e.g. P3 in `src/report.py`) follow the normal test-and-verify rules |
| ARL₀ = 100 sensitivity run (R = 20, matched) | **Deferred** (user, 27 Oct 2026); not authorized, not permanently dropped (design recorded; P6) |
| Production-scale benchmark (`benchmark` mode, R = 1) | **Run once** (authorized, 14 Oct 2026; `benchmark_20261014T041247_106190`); performance evidence only; **do not repeat** |
| SPY download and application | **Stage A implemented and tested (27 Oct 2026; S1–S3 done; methodology v1.6 §11). Execution needs the user's explicit `START SPY APPLICATION`** (P6) |
| Git writes | **Never** (user only) |

## Reference files

| File | Contents |
|---|---|
| [references/scientific-design.md](references/scientific-design.md) | Charts, equations, DGP, roles, estimands, adaptation masking, pilot evidence, corrected interpretations |
| [references/production-plan.md](references/production-plan.md) | Readiness-review findings, corrections C1–C7, production and sensitivity configurations, replicate-aware estimators, compute estimates, execution procedure, SPY phase |
| [references/research-literature.md](references/research-literature.md) | Zotero setup, the 10 references with evidence status, literature discussed but not added, citation caveats |
| [references/reproducibility.md](references/reproducibility.md) | Environment, commands, seeds, determinism, artifacts, provenance |
| [references/production-results.md](references/production-results.md) | Frozen R = 20 production run: identity and hashes, configuration, measured execution, observed findings, caveats, data for P1–P5 |

## Keeping the status current

After every meaningful milestone, update the status record [`docs/project-status.md`](../../../docs/project-status.md); there is no copy inside the skill. Edit the "Verified checkpoint" section and append a row to the "Update log". Record:
- date
- milestone
- files and artifacts (run directory and results hash)
- test outcome (command and pass count)
- open issues
- next recommended task
- approval status

Only record what you verified this session. If an approval or decision came from the user, quote or paraphrase it with its date. Keep this skill's other files consistent when the design or plan changes, and flag conflicts with `CLAUDE.md` to the user rather than editing `CLAUDE.md` unasked.

## Restart instruction for the user

> Use the stc720-project skill, inspect the current repository state and resume from the last verified checkpoint (highest-priority OPEN task; currently the SPY application, which needs my explicit authorization, then the final paper). Do not rerun production or start the sensitivity, benchmark or SPY work without my explicit authorization.
