# STC 720 — RF–EWMA Financial Volatility Monitoring

## 1. Project Identity

This repository contains an individual STC 720 research assignment at the University of Pretoria, South Africa.

**Working title:**

*Random Forest–EWMA Monitoring of Financial Market Volatility: A Simulation Study with an S&P 500 Application.*

**Submission deadline:** 5 November 2026, before 23:59 SAST.

**Primary financial instrument:** SPDR S&P 500 ETF Trust (SPY).

**Development environment:**
- Ubuntu under WSL2.
- Python 3.14.4.
- Project-specific virtual environment: `.venv/`.
- Dependencies recorded in `requirements.txt` and `requirements-lock.txt`.
- CPU-based scientific computing.

The project must be mathematically defensible, computationally reproducible and appropriately scoped for a short honours-level research article.

The objective is to produce a correct, well-evaluated ML–SPC method, not an unnecessarily elaborate architecture.

## 2. Research Objective

Investigate whether Random Forest-based conditional-variance forecasting, combined with an exponentially weighted moving average (EWMA) control chart, provides useful sequential monitoring of unusual financial volatility.

The initial proposed architecture is:

**Financial returns → Random Forest variance forecast → Standardized squared-return score → One-sided EWMA → Volatility alarm**

Let \(r_t\) denote the return at time \(t\).

The Random Forest estimates:

\[
\widehat{\sigma}_{t|t-1}^{2}
=\widehat{E}(r_t^2\mid\mathcal F_{t-1}),
\]

where \(\mathcal F_{t-1}\) represents information available before the return at time \(t\) is observed.

The proposed monitoring score is:

\[
u_t=\frac{r_t^2}{\widehat{\sigma}_{t|t-1}^{2}}.
\]

The EWMA statistic is:

\[
Z_t=\lambda u_t+(1-\lambda)Z_{t-1},
\qquad 0<\lambda\leq1.
\]

A signal is generated when \(Z_t\) exceeds an empirically calibrated upper control limit.

These equations are the **initial research proposal**, not an immutable scientific specification.

Important: A forecast of \(E(r_t^2\mid\mathcal F_{t-1})\) is not automatically a conditional-variance forecast if the conditional mean is nonzero. The methodology must explicitly address this distinction and justify the selected prediction target.

Before implementation, verify whether the proposed architecture is appropriate and whether simpler alternatives should be preferred.

## 3. Scientific Priorities

Prioritize the following, in order:

1. Statistical and mathematical correctness.
2. Methodological defensibility.
3. Reproducibility.
4. Fair benchmark comparisons.
5. Computational reliability and efficiency.
6. Interpretation of results.
7. Code maintainability.
8. Optional performance improvements.

Do not introduce complexity merely to improve apparent sophistication.

Do not assume the proposed RF–EWMA method must outperform classical alternatives.

Negative or mixed experimental results are scientifically acceptable and must be reported accurately.

## 4. Mandatory Research Planning Phase

Before implementing the scientific pipeline:

1. Read the STC 720 assignment rubric in `docs/STC720_assignment_rubric.pdf`.
2. Identify the precise academic requirements and marking criteria.
3. Search and review relevant literature using the connected Zotero MCP server.
4. Verify the mathematical assumptions underlying the proposed architecture.
5. Define the research questions and hypotheses.
6. Identify appropriate classical monitoring benchmarks.
7. Specify financial data sources and preprocessing.
8. Specify a reproducible simulation design.
9. Identify possible methodological weaknesses.
10. Design a small feasibility pilot.

Prepare:

- `docs/research_plan.md`
- `docs/methodology.md`
- `docs/references.md`

These documents must distinguish between established methods, decisions supported by the literature, and proposed design choices.

**STOP after the planning phase and request explicit user approval before implementing the full pipeline.**

Do not run computationally expensive production simulations without authorization.

## 5. Zotero MCP Research Workflow

The Zotero MCP server is configured in Claude Code at user scope.

The user has verified that:

- The MCP server connects successfully.
- Zotero bibliographic records can be retrieved.
- Attached PDF full text can be retrieved.
- Mathematical equations may be distorted during PDF text extraction.

Use Zotero as the primary research-library source when reviewing available papers.

Prioritize literature covering:

- Random Forest regression.
- Classical EWMA control charts.
- RF–EWMA and other ML-assisted SPC methods.
- GARCH and conditional heteroskedasticity.
- Financial volatility forecasting.
- Statistical process monitoring of autocorrelated data.
- Control charts applied to financial markets.

Record verified bibliographic details in `docs/references.md`.

For every important methodological claim:

- Identify the supporting reference.
- Distinguish metadata and abstract information from full-text evidence.
- Verify equations against their original mathematical notation where possible.
- Do not reconstruct ambiguous PDF equations without identifying the reconstruction as uncertain.
- Do not invent references, DOIs, quotations or results.
- Do not claim that a paper directly validates the proposed architecture if it studies a materially different RF–EWMA formulation.

If the available Zotero library is insufficient, identify missing references and request permission before adding external research materials.

## 6. Financial Data and Forecasting

The primary real-world application uses historical SPY daily data.

Requirements:

- Specify the data source.
- Document the observation period.
- Define whether prices are adjusted for distributions and splits.
- Use an explicitly justified return convention.
- Use chronological training, validation and test partitions.
- Do not fit models or preprocessing transformations using future data.
- Avoid contemporaneous predictors unavailable at forecast time.
- Ensure all predictions for \(r_t\) use information available no later than \(t-1\).

For the Random Forest:

- Justify the prediction target.
- Use a modest and interpretable feature set.
- Enforce strictly positive, finite forecast denominators.
- Explain and test any prediction floor.
- Examine forecast bias and calibration.
- Assess whether normalized scores retain dependence or heavy tails.
- Avoid excessive hyperparameter searches.

When comparing forecasting methods, use consistent data partitions and information sets.

## 7. SPC Methodology

The proposed chart is a one-sided upper EWMA monitoring unexpected volatility.

The monitoring process must be specified mathematically, including:

- Monitoring statistic.
- Smoothing parameter.
- Initialization.
- Control-limit definition.
- Alarm rule.
- Treatment of serial dependence.
- Model fitting and calibration.
- Run-length definition.
- Change-point convention.
- Handling of false alarms.
- Handling of finite simulation horizons.

Do not assume \(u_t\) is independent, identically distributed or normally distributed.

Do not apply textbook Gaussian EWMA limits without validating their assumptions.

Prefer empirical control-limit calibration when dependence and non-normality make analytical limits inappropriate.

The proposed scheme must be calibrated and validated using independent data or simulation replications.

## 8. Classical Benchmarks

At minimum, investigate:

**Benchmark 1 — Conventional EWMA**

An EWMA monitoring raw squared returns or an explicitly standardized squared-return statistic.

**Benchmark 2 — GARCH-standardized EWMA**

An EWMA monitoring squared returns normalized by a fitted GARCH conditional-variance forecast.

**Proposed method — RF–EWMA**

An EWMA monitoring squared returns normalized by a Random Forest-based forecast.

The precise benchmark definitions must be approved during research planning.

Ensure comparisons are scientifically fair:

- Use identical underlying simulated trajectories wherever possible.
- Match validated in-control false-alarm performance.
- Use the same change-point and run-length conventions.
- Report assumptions for each competing model.
- Distinguish volatility-forecast accuracy from monitoring performance.

Do not select weak comparators merely to favour RF–EWMA.

## 9. Monte Carlo Simulation Design

Use a controlled financial time-series simulation framework, initially considering GARCH-type processes.

Investigate relevant scenarios such as:

- In-control stationary conditional heteroskedasticity.
- Persistent volatility increases.
- Changes in conditional-variance dynamics.
- Heavy-tailed innovations.
- Alternative changes justified by the literature.

The final selection of scenarios must be justified during planning.

Maintain separate experimental roles:

1. Model training.
2. Hyperparameter development.
3. In-control control-limit calibration.
4. Independent in-control validation.
5. Out-of-control evaluation.
6. Final untouched evaluation, where feasible.

Avoid leakage between experimental roles.

The forecasting model must remain frozen during an evaluation trajectory unless an explicitly approved alternative monitoring protocol is being studied.

Calibrate each chart against a common target in-control ARL.

Use independent random streams and explicit seed management.

Use matched simulated trajectories for paired chart comparisons when appropriate.

For each relevant scenario, report:

- Validated in-control ARL.
- Out-of-control detection performance.
- Mean or conditional detection delay.
- Simulation uncertainty.
- Relevant run-length distribution summaries.

Distinguish detection delay measured in monitoring opportunities from delay measured in raw observations.

Use appropriate handling for right-censored run lengths.

Do not report truncated run-length means as unrestricted ARL estimates.

Do not fabricate, interpolate or silently replace simulation results.

## 10. Feasibility Pilot

Before production experiments, implement an inexpensive pilot only after user approval.

The pilot should answer:

1. Can the RF produce sensible, positive, out-of-sample variance-related forecasts?
2. Are the monitoring scores numerically stable?
3. Can the EWMA achieve plausible in-control calibration?
4. Does it respond to controlled volatility changes?
5. How does it compare with a simple EWMA benchmark?
6. Is the computational runtime manageable?

Use small replication counts and limited parameter settings.

If the pilot identifies a fundamental methodological problem, stop and recommend a correction.

Do not rescue weak findings through extensive unplanned parameter searches.

Do not proceed to full production simply because the code executes successfully.

## 11. Reproducibility and Software Design

Use the existing Python environment:

`.venv/`

Core scientific packages include:

- NumPy
- pandas
- SciPy
- scikit-learn
- arch
- yfinance
- Matplotlib
- pytest

Additional packages require justification.

Keep the Python implementation modular but simple.

Separate:

- Data acquisition and preprocessing.
- Financial simulation.
- Forecasting models.
- Control-chart implementation.
- Control-limit calibration.
- Statistical evaluation.
- Reporting and visualization.

Use explicit configurations and deterministic random seeds where practical.

Provide unit tests for:

- Feature timing and absence of look-ahead.
- Conditional-variance forecast handling.
- EWMA recursion.
- Control-limit calibration.
- Run-length calculations.
- Independent simulation seeds.
- Experiment reproducibility.

Do not claim bit-for-bit reproducibility unless it has been demonstrated.

Use mathematical and numerical correctness tests rather than relying only on snapshots of expected output.

## 12. Simulation Macro Wrapper

The implementation must eventually support:

`python run.py smoke`

`python run.py production`

`python run.py verify`

Provide a Bash execution wrapper:

`scripts/run_simulation.sh`

The wrapper must:

- Execute the specified experiment.
- Create a unique run directory.
- Record elapsed wall-clock time.
- Record CPU time and utilization.
- Record peak memory usage.
- Preserve standard output and error logs.
- Record the process exit status.
- Preserve diagnostic information when a run fails.
- Record the Python version.
- Record relevant dependency versions.
- Record random seeds.
- Record the experiment configuration.
- Record available provenance information.

The Git commit identifier may be collected using a permitted read-only Git command.

Do not allow the wrapper to stage, commit, push or modify Git history.

Use GNU `/usr/bin/time` when available.

Prevent unrestricted nested parallelism.

Independent Monte Carlo replications may be parallelized using controlled CPU workers.

Report runtime and resource usage honestly.

Do not implement a complex experiment-orchestration framework.

## 13. Git Policy — User Controls All Changes to Repository History

**The user is the sole Git author, committer and publisher.**

Claude Code may execute read-only Git commands for inspection, verification and provenance purposes.

### Permitted read-only commands

Examples include:

- `git status`
- `git diff`
- `git diff --check`
- `git log`
- `git show`
- `git ls-files`
- `git rev-parse`
- `git branch --show-current`

Claude may inspect the repository state, identify modified files and recommend Git checkpoints.

### Prohibited operations

Claude Code must NEVER independently execute:

- `git add`
- `git commit`
- `git push`
- `git pull`
- `git fetch`
- `git merge`
- `git rebase`
- `git reset`
- `git restore`
- `git checkout`
- `git switch`
- `git branch` operations that create, delete or modify branches
- `git tag` operations that create, delete or modify tags
- `git stash`
- `git clean`
- `git cherry-pick`
- Git configuration changes
- Git hook installation or modification
- Repository history rewriting

The user must perform all staging, commits and pushes manually.

Claude must not execute these operations indirectly through scripts, subprocesses or other tools.

If a Git operation outside the permitted read-only set is required, explain why and give the exact command for the user to run manually.

### Commit authorship

Do not add Claude, Anthropic or any AI system as:

- Commit author.
- Commit committer.
- Co-author.
- `Co-authored-by` trailer.
- `Signed-off-by` trailer.
- Automated contributor attribution.

Do not modify `user.name`, `user.email` or other Git identity settings.

Do not create commits using an alternate identity.

The project remains subject to the university's academic-integrity and AI-disclosure requirements; Git authorship and academic AI disclosure are separate matters.

### Development checkpoints

At the end of each meaningful milestone:

1. Summarize the changes.
2. List files created or modified.
3. Report test results.
4. Identify outstanding issues.
5. Suggest a concise commit message.
6. Provide manual Git commands if requested.
7. Wait for the user to perform the commit.

Claude may continue ordinary research and development after approval, but must not perform Git writes.

Never modify the user's previous thesis repositories.

## 14. Research Report Requirements

Use the actual STC 720 assignment rubric as the primary authority.

The report should be a concise scientific article, not a full-length thesis.

The planned sections include:

- Abstract.
- Introduction and literature review.
- Mathematical background.
- Proposed monitoring scheme.
- Results and discussion.
- Financial application.
- Conclusion.
- References.
- Code appendix.

Follow the rubric's actual length limits, formatting rules, evaluation criteria and submission requirements.

Include numbered mathematical equations, appropriate figures and properly labelled numerical tables.

Every reported result must be traceable to a reproducible computational output.

Do not invent results or cite inaccessible literature as though it has been inspected.

Declare generative AI use according to the assignment requirements.

## 15. Post-Submission Trading Extension

The user may later extend the project into a quantitative trading and risk-management system.

Possible future work includes:

- SPY momentum strategies.
- Volatility-aware position sizing.
- Using EWMA alarms as a risk filter.
- Historical trading backtests.
- Transaction-cost and slippage modelling.
- Paper trading.
- Broker API integration.

**These extensions are explicitly outside the current STC 720 implementation scope.**

Do not add trading execution, live brokerage functionality or complex backtesting infrastructure unless separately authorized after the coursework objectives have been completed.

The research pipeline should remain sufficiently modular to support a future extension without making the present implementation more complicated.

## 16. Scope and Complexity Restrictions

Do not introduce the following without explicit user approval:

- Convolutional autoencoders.
- Neural networks.
- One-class SVMs.
- Deep reinforcement learning.
- Additional ML ensembles.
- Unnecessary dimensionality-reduction stages.
- Complex plugin architectures.
- Large agent hierarchies.
- Multiple scientific-contract systems.
- Unnecessary configuration frameworks.
- Extensive architecture searches.
- Automated Git commits or releases.

The current objective is a manageable, rigorous ML–SPC research project.

Prefer a correct and interpretable RF–EWMA experiment over a complicated hybrid that is difficult to validate.

## 17. Communication and Approval

Communicate findings clearly, including negative results, uncertainty and methodological limitations.

Distinguish:

- Established findings.
- Verified results.
- Assumptions.
- Proposed design choices.
- Speculation.

Ask for approval before:

- Changing the central research question.
- Replacing the main architecture.
- Adding substantial dependencies.
- Launching expensive simulations.
- Implementing the full pipeline after the planning phase.
- Expanding the project into trading infrastructure.
- Performing any Git operation that changes repository state.

Avoid unnecessary approval requests for routine, already-authorized coding, documentation and testing.

## 18. Current Project Status

**P1–P5 DONE; SPY APPLICATION EXECUTED AND VERIFIED (27 OCT 2026); FINAL PAPER STAGE 1 DONE (30 OCT 2026); NEXT: USER REVIEW, THEN STAGE 2 DRAFTING**

**Checkpoint 30 Oct 2026 (end of session): START THE NEXT SESSION WITH [`docs/next-session-handover.md`](docs/next-session-handover.md).**
- **First task (31 Oct 2026; approved, not started):** publication-size figure readability correction (plotting only, derived outputs, text 8–10 pt).
- **Then:** Stage 2 drafting.
- **Not authorized:** any simulation, SPY run, refit, recalibration, download or Git write.
- **Terminology:** new academic prose says "pre-specified"; the "pre-registered" wording below is historical.

**Final paper, Stage 1 DONE (30 Oct 2026).**
- **SPY figures.** Legends and panel labels no longer hide data (derived copies in `results/derived/spy_figures/`, 35/35 checks).
- **Report scaffold.** `report/main.tex` and `report/refs.bib`, with tables generated by `scripts/paper_assets.py` from frozen results (110/110 checks).
- **Outlines** for the student-written sections: `docs/paper_outlines.md`.
- **Tests:** 134 passed.
- **Public repository:** `https://github.com/stephenjamespienaar/stc720-rf-ewma`.
- **Open:** figure text is too small in print. The paper-size regeneration was **approved** by the user on 30 Oct 2026 and has **not been done**; it is the next task.
- Details: `docs/project-status.md`.

*Updated 27 October 2026, after P4/P5. The detailed, authoritative progress record and task list is `docs/project-status.md`. The frozen production numbers, hashes and caveats are in `.claude/skills/stc720-project/references/production-results.md`.*

Completed and verified:

- **Planning:** the rubric was reviewed and `docs/research_plan.md`, `docs/methodology.md` (now v1.4) and `docs/references.md` were written. The user approved the MODIFY recommendation: conventional EWMA, GARCH–EWMA and RF–EWMA on a common score, frozen models, an adaptation-masking investigation, and pilot-first development.
- **Phase 1 (pilot):** implementation, wrapper, smoke and verify runs, and the reduced pilot. The canonical pilot is `results/runs/pilot_20261013T075339_142070` (`f92f0715…`), summarised in `docs/phase1_pilot_report.md`. It was independently audited and remediated, and the baseline was committed as `f77297b`.
- **Phase 2 (production preparation C1–C7):** two independent Codex audits, both remediated. Committed by the user as `9b286e1`.
- **Performance benchmark:** run once (R = 1, seed 20261013): `results/runs/benchmark_20261014T041247_106190` (`77e20ffa…`). It is performance evidence only, excluded from inference. Under the original validation rule its outcome was 2 of 6 primary configurations passed, recorded unchanged.
- **Final production design:** committed by the user as `3529ddd` (the production source). The post-production documentation was then committed by the user as `fb73ecd`.
  - R = 20, with the ARL₀ = 100 sensitivity matched by inheritance.
  - Amended IC validation (`docs/methodology.md` §6, eq. 29): a configuration passes iff its whole independent-validation 95% CI lies in [A₀(1−0.15), A₀(1+0.15)] = [425, 575], with exact inclusive bounds. It is a post-pilot, post-benchmark amendment, conditional on h*, and not a complete equivalence test.
  - Failure policy: run all replicates; never drop, replace or recalibrate.
  - Provenance classification: `scripts/git_provenance.sh`.
  - 80 tests passing.
- **First full production run (14 October 2026; explicitly authorized):**
  - **Directory and hash:** `results/runs/production_20261014T060921_145897/`, results hash `44410144e3feb4a762dd2044fec07a2ddc64fdc742d43637332cc03f731431b8`.
  - **Configuration:** mode `production`; target ARL₀ = 500; R = 20 independent training/calibration replicates; master seed 20261014; 500 RF trees; per replicate 2,000 calibration paths, 2,000 IC-validation paths and 2,000 OOC paths per shift scenario; IC horizon 5,000; OOC horizon H = 500; τ = 50; δ ∈ {1.5, 2, 3}; λ ∈ {0.1, 0.2}. The 12 primary contrasts are unchanged.
  - **Execution:** run from clean committed `3529ddd`. 20/20 replicates, exit status 0, wall about 16 min 27 s, peak RAM about 1.74 GiB.
  - **Validation:** **160/160** IC configurations passed eq. 29. No replicate was discarded, replaced, selectively rerun or recalibrated.
  - **Checks:** all of the run session's internal reproducibility and verification checks passed.
- **Observed findings** (λ = 0.1; simulation only; not causal):
  - Conventional EWMA detected the evaluated persistent increases fastest. Mean restricted delays for conventional / RF / GARCH were 205 / 243 / 249 days at δ = 1.5, 132 / 192 / 202 at δ = 2 and 63 / 126 / 140 at δ = 3.
  - RF–EWMA had shorter restricted delays than GARCH–EWMA, heterogeneous across fitted systems. It showed no distinguishable advantage on X(20).
  - Conventional EWMA forecasts worst but detects best.
  - Adaptation-masking results are **consistent with** the detection ranking. They are not proven to be its cause.
  - Caveats (state them with any result): unadjusted 95% CIs; equal ARL₀ ≠ equal pre-change false-alarm probability; censoring at H = 500; GARCH-generated DGP; IC-validation CIs conditional on h*.
- **P1 independent production-results audit: PASS (27 October 2026).**
  - **What was recomputed:** the 12 primary contrasts and their 4 δ = 1 baselines, from `paths.npz`, by `scripts/audit_p1.py`. The script uses only the stdlib, NumPy and SciPy, runs under `python -I`, and imports no `run` or `src` module.
  - **Comparisons:** **1,768/1,768 primary comparisons bit-identical** to `results.json`. The secondary sweep over all stored paired contrasts found 0 mismatches; its 29 floating-point differences are ≤ 3.6 × 10⁻¹⁵.
  - **Checks:** **518/518 integrity and design checks passed**: file hashes, results and per-path hashes, config, CRN survivor invariance, pairing counts and replicate order.
  - **Artifacts:** the frozen production artifacts are unchanged (17/17 hashes).
  - **Outputs:** `results/derived/p1_audit/`. Report: `docs/p1_audit_report.md`.
  - **Limitation:** P1 verified the **downstream calculations from the stored alarm times**. It did **not** verify the upstream simulation (DGP, forecasters, EWMA, calibration) that produced them. It also did not reproduce `boot_ci95`, and masking, occupancy and IC quantities were outside its scope.
- **P2 supplementary, post hoc multiplicity analysis (27 October 2026):** decided after the primary results were seen; not pre-registered. Two-sided t₁₉ tests of the 20 replicate estimates, with Holm step-down at FWER 0.05 over exactly the 12 primary contrasts.
  - **Rejected:** 6/12, all RF − conventional (Holm p ≤ 9.2 × 10⁻⁵). The sign-test Holm check, which tests a different null (balance of signs), rejects the same 6.
  - **Not rejected:** RF − GARCH RMD₅₀₀ (unadjusted p 0.009–0.011; Holm p 0.0533 at each δ, borderline) and RF − GARCH X(20) (Holm p = 1).
  - **Target:** the mean contrast over fitted systems in this design, not consistent per-system or real-market superiority. The unadjusted primary estimates and CIs are unchanged.
  - **Records:** `docs/p2_multiplicity_report.md`, `scripts/p2_holm.py`, `results/derived/p2_holm/`.
- **P3 production figure repair (27 October 2026):** the fixed 0.03 replicate jitter hid replicates 0–1 (δ = 1) and 18–19 (δ = 3) outside the axes at R = 20, and mixed the δ = 1.5 and 2 clouds.
  - **Fix:** plotting only, `src/report.py` `jitter`, with a regression test.
  - **Output:** regenerated from the frozen `results.json` into `results/derived/p3_figures/` (`fig_replicates.png` `6e4fbcde…`; the original `1af6a110…` is untouched).
  - **Checks:** 41/41 passed; all 280 plotted replicate values equal the stored values; `fig_delay` and `fig_profile` are bit-identical.
  - **Records:** `docs/p3_figure_report.md`, `scripts/p3_figures.py`.
- **P4/P5 exploratory diagnostics (27 October 2026; descriptive, post hoc; no p-values, no causal claims, no retuning):**
  - **P4:** RF − GARCH between-system spread is 3.4–8.2× the MC SE under a change, stable within systems (ρ 0.85–0.97), and most strongly associated with the masking gap (ρ −0.80 to −0.89).
  - **P5:** equal ARL₀ but different run-length shapes. The conventional chart has CV 1.04 and P(T < τ) 0.125, against 0.093 for a geometric run length; GARCH and the oracle are near-geometric; survivor conditioning is non-neutral.
  - **Records:** `docs/p45_diagnostics_report.md`, `scripts/p45_diagnostics.py`, `results/derived/p45_diagnostics/`. Per-path validation run lengths are not stored.
- **Binding design decisions (user, 14 October 2026):**
  - production seed **20261014**, shared by the matched ARL₀ = 100 sensitivity (not an independent experiment)
  - 12 pre-registered primary contrasts: paired RMD₅₀₀ and X(20), RF − GARCH and RF − conventional, λ = 0.1, δ ∈ {1.5, 2, 3}, each with its δ = 1 counterpart; everything else is secondary
  - no multiplicity adjustment was pre-registered; any adjustment is post hoc and supplementary
- **Reproducibility caveat:** the historical pilot came from uncommitted pre-remediation source, and later source does not reproduce its `results.json`. Never alter or regenerate the pilot, benchmark or production artifacts (see `.claude/skills/stc720-project/references/reproducibility.md`).

Current Git state:

- HEAD `5fcdf6b` on `main` = `origin/main` (verified 30 October 2026; public at `https://github.com/stephenjamespienaar/stc720-rf-ewma`). The Stage 1 files are uncommitted until the user commits. `.serena/` is git-ignored development-tool state. The user performs all Git staging, commits and pushes.

Outstanding (details in `docs/project-status.md`):

- **P1: DONE (PASS, 27 October 2026).**
- **P2: DONE (27 October 2026).** Supplementary post hoc Holm analysis; the unadjusted results are kept.
- **P3: DONE (27 October 2026).** Replicate-figure repair; the repaired figure is in `results/derived/p3_figures/`.
- **P4 and P5: DONE (27 October 2026).**
- **Priority 1, the SPY application (P6):** rubric §5. SPY Stage A (implementation and synthetic tests): DONE (27 Oct 2026); awaiting the user's explicit `START SPY APPLICATION`. The guarded `spy` mode is in `run.py`, `src/application.py` and `src/spy.py` (S1), with the episode definition in `src/chart.py`, and is tested by `tests/test_spy.py` (16 tests). The design and the 9 verified reference dates are frozen in methodology v1.6 §11. No SPY data has been downloaded and no real model has been fitted. SPY execution (authorized 27 Oct 2026, "START SPY APPLICATION"): STOPPED AT THE STRICT FOURTH-MOMENT GATE, as designed (exit 3). Run `results/runs/spy_20261027T045319_117125` (results hash `b0e2ade1…`) from clean committed `7e2eaa1`. The snapshot `data/raw/SPY.csv` (SHA-256 `7cd6d400…`, 8,475 rows, 1993-01-29 to 2026-09-30, accessed 2026-10-27T02:53:22Z) passed integrity. The training GARCH(1,1)-t is ω 0.00457, α 0.0599, β 0.9377, ν 7.35: persistence 0.9976 (stationary, flagged near-boundary), fourth-moment coefficient 1.0089 > 0.99 (and ≥ 1). Its unconditional variance of 1.920 differs from the training s² of 1.144. No limit was calibrated and no chart was computed. **Decision needed** on how to proceed (finite-variance option, D2), given the variance-level mismatch. **Do not relax the gate, recalibrate or relaunch without the user's decision.** SPY finite-variance calibration IMPLEMENTED (27 Oct 2026; code and synthetic tests only; post-stop refinement). Model B (variance-targeted GARCH-t) was approved by the user as the fixed SPY specification. `sim.simulate(..., need_m4=False)` is an explicit opt-in used only by `run.SPY['finite_variance_simulation']`; the strict default is bit-identical to committed code. Diagnostics a–i are fixed in `run.SPY['diagnostics']`. Target: the restricted mean run length E[min(T, 5000)] = 500, not E[T]. Tests: 133 passed. Criterion e refined (user decision, 27 Oct 2026, **before any SPY calibration**). These remain **hard stops**: a non-finite or non-positive h*, a failed minimality condition (restricted ARL(h*) ≥ 500 > restricted ARL(h*(1 − 10⁻⁶))), an inconsistent restricted-mean computation, and failed bracketing or bisection (`CalibrationError`). Only the overshoot |restricted ARL(h*)/500 − 1| > 10⁻³ became a **recorded warning** (`e_overshoot`), keeping the exact overshoot, achieved restricted ARL, target deviation and status in `results.json`. Justification: in the frozen production run, 24 of 160 calibrations exceeded 10⁻³ (maximum 0.16%) through the discreteness of the empirical ARL. There is no recalibration, no seed change and no selective rerun, and validation is unchanged. **SPY calibration and relaunch NOT authorized; the SPY application is NOT complete**. SPY variance-targeting remediation (training only; post-stop refinement, 27 Oct 2026; `docs/spy_vt_remediation.md`): the variance-targeted GARCH-t (`forecast.fit_garch_vt`, selected only by `run.SPY['garch_estimator']`) gives ω 0.00513, α 0.0593, β 0.9363, ν 7.63. Its implied variance equals s² (1.144), against 1.920 unrestricted, at a likelihood cost of 0.24, with practically identical training ĥ. It **still fails the fourth-moment gate** (m4 1.0039; E r⁴ = ∞). A finite-variance calibration option, diagnostics a–i and a relaunch are **NOT authorized**. **The SPY application is NOT complete**. Run with `scripts/run_simulation.sh spy --approved`. It stops with exit 3 at the strict fourth-moment gate if the fitted GARCH-t fails it (D2).
- **SPY completed:** SPY APPLICATION EXECUTED (relaunch authorized 27 Oct 2026, "START SPY RELAUNCH"): run `results/runs/spy_20261027T061202_150671`, results hash `5725d5e3…` (`results.json` file `877b5f09…`, `monitor.csv` `3ba20094…`, `frozen.json` `5a979745…`), from clean committed `5fd5653`. Exit 0, wall 43 s, 1.34 GiB peak. Every hard-stop diagnostic passed (a, b, c, d, e); 6/6 eq. 29 validations passed; 2 recorded `e_overshoot` warnings at λ = 0.2 (conventional 0.121%, GARCH 0.151%). Frozen checks true. Independent post-run verification passed: hashes, chronology, GARCH denominators re-filtered from r_{t−1} (6.7e-16), EWMA recursion, exceedances, episodes, reference states. No further SPY runs are authorized.
- **Priority 2, now next:** the final research paper. Stage 1 is done (30 Oct 2026); Stage 2 drafting starts after the user's review. The paper has no code appendix, file paths or commands, only a Code Availability statement (user decision, 30 Oct 2026). Use "pre-specified", not "pre-registered".
- **ARL₀ = 100 sensitivity: DEFERRED** (user, 27 October 2026). It is not authorized and not permanently dropped.

Authorization boundaries:

- **Not authorized:**
  - a production rerun
  - the ARL₀ = 100 sensitivity run
  - another benchmark
  - SPY data download or application

  None of these starts automatically in a new session.
- `production`, `sensitivity_arl100` and `benchmark` refuse to start without `--approved`. The flag never replaces the user's explicit authorization of each run.
- Git writes remain reserved to the user (Section 13).

## 19. Session Continuity

At the start of every session:

1. Read this file.
2. Load the project skill `stc720-project` (`.claude/skills/stc720-project/`).
3. Read `docs/project-status.md`, the authoritative checkpoint and open-task list.
4. Read the frozen production results reference, `.claude/skills/stc720-project/references/production-results.md`.
5. Verify the actual state with read-only commands: `git branch --show-current`, `git rev-parse HEAD`, `git status --short`. Check the production artifacts, e.g. that `sha256sum results/runs/production_20261014T060921_145897/*` matches the recorded hashes and that the recomputed results hash is `44410144…`. Treat anything unverified as incomplete.
6. Read `docs/next-session-handover.md`. Summarise the verified state, then resume from the **highest-priority OPEN task** within its authorized scope. As of 30 Oct 2026 that is the approved figure readability correction, then Stage 2 of the final paper. The SPY application is complete; no SPY run is authorized.
7. **Never rerun production and never start the sensitivity, a benchmark or SPY work without the user's explicit authorization in the current session.** Git writes stay reserved to the user (§13).
8. After each meaningful milestone, update `docs/project-status.md` (verified checkpoint and update log). Do not mark work complete until it is tested and verified.

Restart instruction:

> Use the stc720-project skill and read `docs/next-session-handover.md` first. Inspect the current repository state read-only and resume from the last verified checkpoint (currently the approved publication-size figure readability correction, then Stage 2 of the final paper). Do not rerun production or start the sensitivity, benchmark or SPY work without my explicit authorization.
