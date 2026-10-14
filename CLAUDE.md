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

*Updated 14 October 2026 (session 3). The detailed, authoritative progress record is `docs/project-status.md`.*

Completed and verified:

- Repository, Python environment, dependencies and Zotero MCP set up and verified.
- Research planning: rubric reviewed; `docs/research_plan.md`, `docs/methodology.md` and `docs/references.md` written. The user approved the MODIFY recommendation: conventional EWMA, GARCH–EWMA and RF–EWMA compared on a common score; frozen models; adaptation-masking investigation; pilot-first development.
- Phase 1:
  - core implementation (`src/`, `run.py`)
  - execution wrapper (`scripts/run_simulation.sh`)
  - smoke and verify runs
  - reduced feasibility pilot. The canonical run is `results/runs/pilot_20261013T075339_142070`, summarised in `docs/phase1_pilot_report.md` (revised after the audit; revision log §14).
- Production-readiness review delivered, verdict **CORRECTIONS REQUIRED**. The record is in `.claude/skills/stc720-project/references/production-plan.md`.
- **Phase 1 independently audited and remediated.**
- **Git baseline.** The user committed the verified Phase 1 baseline as `f77297b9a257bbe8ca80c858f6119219471925b8` on `main`, then the documentation commit `87c4dc7` (current HEAD).
- **Phase 2 production preparation (corrections C1–C7) implemented and independently audited** (Codex CLI audit: CORRECTIONS REQUIRED, three major findings, no critical scientific errors). **Major findings M1–M3 and the minor findings remediated and verified with regression tests** (14 Oct 2026):
  - M1: complete result schema and CRN-pairing check when no path survives to τ; unidentified values are None
  - M2: figures omit unidentified points and never zero-fill SEs
  - M3: the variance component is the *residual between-system variability (training, model selection, forest randomness and calibration) after subtracting estimated evaluation Monte Carlo variance*; arithmetic and t intervals unchanged
- **Second independent audit:** M1 and M3 confirmed resolved, M2 plotting fixes confirmed, estimators verified; residual reporting and documentation inconsistencies corrected (14 Oct 2026): report cells distinguish `n/i` (not identifiable), `–` (not applicable) and valid zeros; δ = 1 X(k) cells read the stored estimand; headings are mode-sensitive (only `production` claims primary endpoints; sensitivity all secondary; benchmark performance-only).
- **Tests: 72 passing** (`.venv/bin/python -m pytest -q`): 34 Phase 1, 24 Phase 2, 7 audit-remediation and 7 report-cell regression tests. Smoke and verify pass with identical hashes. The canonical pilot artifacts are unchanged.
- **Design decisions (user, 14 Oct 2026):**
  - production master seed **20261014**, shared by the matched ARL₀ = 100 sensitivity run (not an independent experiment); pilot seed 20261013 unchanged
  - 12 pre-registered primary contrasts: paired RMD₅₀₀ and X(20), RF − GARCH and RF − conventional, λ = 0.1, δ ∈ {1.5, 2, 3}, each with its δ = 1 counterpart; X(5), X(60) and the sensitivity run are secondary
  - `benchmark` mode (R = 1, seed 20261013) is a production-scale performance benchmark only, excluded from all inference
- **Reproducibility caveat.** The historical canonical pilot is preserved unchanged (results hash `f92f0715…`). It was generated from uncommitted pre-remediation source. The **Phase 1 remediation** (committed in `f77297b`) introduced the historical difference: it corrected the slope diagnostic's normalisation (`slope_h` × (n−1)/n), the only output change at that stage. The current **Phase 2** source differs further (output schemas, replicate aggregation, paired intervals and reporting), so it does not reproduce the pilot's `results.json` either, and the slope fix is not the only difference. The original pilot artifacts remain preserved. See `docs/phase1_pilot_report.md` (header note and §5) and `.claude/skills/stc720-project/references/reproducibility.md`. Never alter or regenerate the historical pilot artifacts.

Current Git state:

- All Phase 2 and audit-remediation changes are **uncommitted** on `main` (HEAD `87c4dc7`): modified `run.py`, `src/chart.py`, `src/report.py`, `scripts/run_simulation.sh`, `tests/test_core.py`, docs, skill references and this file; new `src/aggregate.py`. The user commits.

Outstanding:

- User commit review of the Phase 2 changes; then a clean-worktree launch of the production-scale benchmark, only after explicit authorization.
- Remaining limitations: unmeasured runtime and memory (estimated benchmark ≈ 1 min, upper bound 6 min; peak RSS ≈ 1.4–1.8 GiB, upper 3 GiB); 12 primary contrasts not adjusted for multiplicity; smoke-size ARL₀ validation failures are expected and do not validate production.
- **SPY application phase (not started):** data-integrity checks, pipeline, simulation-based control limits, pre-registered reference dates.

Authorization boundaries:

- **Benchmark readiness:** code ready; the benchmark has **not** been run and is **not authorized**.
- **Not authorized:**
  - the production-scale benchmark (`benchmark` mode)
  - full production simulations
  - the ARL₀ = 100 sensitivity run
  - SPY data download or application
- `production`, `sensitivity_arl100` and `benchmark` refuse to start without `--approved`. The flag is a technical safeguard and never replaces the user's explicit authorization of each run.
- Git writes remain reserved to the user (Section 13).

## 19. Session Continuity

At the start of every session:

1. Read this file.
2. Use the project skill `stc720-project` (`.claude/skills/stc720-project/`) and read `docs/project-status.md`.
3. Inspect the repository with read-only Git commands. Verify the recorded status against the actual code and artifacts, and treat anything unverified as incomplete.
4. Summarise the verified state, the next authorized task and pending decisions to the user. Ask for approval before any work outside the authorized scope. Production and sensitivity runs, the runtime benchmark and SPY work stay gated (§18), and Git writes stay reserved to the user (§13).
5. After each meaningful milestone, update `docs/project-status.md` (verified checkpoint and update log). Do not mark work complete until it is tested and verified.

Restart instruction:

> Use the stc720-project skill, inspect the current repository state and resume from the last verified checkpoint. Do not execute production simulations without my explicit authorization.
