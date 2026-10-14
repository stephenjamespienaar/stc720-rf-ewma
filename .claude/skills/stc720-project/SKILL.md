---
name: stc720-project
description: Resume and continue the STC 720 (University of Pretoria) Random Forest–EWMA financial-volatility monitoring research assignment in this repository. Use at the start of any session in stc720-rf-ewma, or whenever the user asks to resume, continue, check status, prepare or run production or sensitivity simulations, work on the SPY application, methodology, literature/Zotero, results or the report. Gives the verified project status, approval gates, scientific invariants and the safe continuation workflow.
---

# STC 720 RF–EWMA — project continuation

**Project:** individual STC 720 research article (University of Pretoria), *Random Forest–EWMA Monitoring of Financial Market Volatility: A Simulation Study with an S&P 500 Application*.
**Due:** Thu **5 Nov 2026, 23:59 SAST**, via ClickUP. Internal target is to submit on 4 Nov. Turnitin similarity must be ≤ 20%, and a generative-AI declaration goes below the keywords.
**Repository:** `/home/stephen/projects/stc720-rf-ewma` (Python 3.14.4, `.venv/`, WSL2).

## Current stage (14 Oct 2026): FIRST FULL PRODUCTION COMPLETE — SCIENTIFIC RESULTS AUDIT PENDING

- The scientific architecture and configuration are **frozen**. Phase 1 (pilot) and Phase 2 (production preparation, audits, final R = 20 design) are complete and committed (HEAD `3529ddd`).
- The R = 20, ARL₀ = 500 production run is complete and **frozen**: `results/runs/production_20261014T060921_145897/`, results hash `44410144…`. Its numbers, hashes and caveats are in [references/production-results.md](references/production-results.md). It has **not** yet had an independent numerical audit.
- **Next task: P1, the independent production-results audit.** After it: P2 Holm (post hoc), P3 figure repair from the frozen results, P4 heterogeneity (descriptive), P5 run-length distributions. All are OPEN; the task list is in `docs/project-status.md`.
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
| Post-production analysis P1–P5 (independent audit, Holm, figure repair, heterogeneity, run-length comparison; no new simulation) | **OPEN.** P1 is next. Code changes (e.g. P3 in `src/report.py`) follow the normal test-and-verify rules |
| ARL₀ = 100 sensitivity run (R = 20, matched) | **Not authorized** (design recorded; P6) |
| Production-scale benchmark (`benchmark` mode, R = 1) | **Run once** (authorized, 14 Oct 2026; `benchmark_20261014T041247_106190`); performance evidence only; **do not repeat** |
| SPY download and application | **Not authorized** (later, separate phase; preparation items S1–S3 open; P6) |
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

> Use the stc720-project skill, inspect the current repository state and resume from the last verified checkpoint (highest-priority OPEN task; currently P1, the independent production-results audit). Do not rerun production or start the sensitivity, benchmark or SPY work without my explicit authorization.
