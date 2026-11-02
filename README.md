# Random Forest–EWMA Monitoring of Financial Market Volatility: A Simulation Study and an Application to the SPDR S&P 500 ETF

**STC 720 Research Report · Group 10 · Department of Statistics, University of Pretoria**

| Author | Student number |
|---|---|
| Stephen James Pienaar | u22594583 |
| Kirsten Ford | u23661926 |
| Kwanele Tlou | u23579472 |

This repository contains the research code, tests, LaTeX manuscript and selected derived results of an unpublished course research report for the module STC 720. The report has not been peer reviewed or published, and the University of Pretoria does not endorse it.

---

## Overview

Large and persistent increases in market volatility change the risk of every portfolio exposed to that market. Statistical process control (SPC) offers a principled way to monitor such changes sequentially: a control chart accumulates evidence day by day and raises an alarm when the evidence exceeds a calibrated limit.

Daily financial returns are a difficult setting for textbook control charts. Their variance changes over time (conditional heteroskedasticity), large moves cluster together, the distribution has heavy tails, and squared returns are strongly autocorrelated. Charts whose limits assume independent, normally distributed observations are therefore unreliable, and the user must decide what a "normal" level of volatility is on any given day.

A natural response is to standardise each squared return by a forecast of its conditional variance and monitor the standardised score with an exponentially weighted moving average (EWMA). Random forests can produce such forecasts without assuming a parametric volatility model. This project asks: **does Random Forest variance forecasting improve an EWMA chart's ability to detect persistent increases in financial-market volatility, compared with a constant-variance chart and a GARCH-based chart?**

## Research methodology

All three charts monitor the same score and differ only in its denominator $d_t$, which uses only information available before day $t$:

```math
u_t = \frac{r_t^2}{d_t}, \qquad Z_t = \lambda u_t + (1-\lambda) Z_{t-1}, \qquad Z_0 = 1,\ 0<\lambda\le 1 .
```

The one-sided chart signals on the first day with $Z_t > h^*$, where $h^*$ is a control limit calibrated by simulation.

| Scheme | Denominator $d_t$ |
|---|---|
| **Conventional EWMA** | Constant: the mean squared return of the training period |
| **GARCH–EWMA** | Conditional-variance forecast of a GARCH(1,1) model with Student-*t* innovations, fitted once and frozen |
| **RF–EWMA** (proposed) | Random Forest forecast of the squared return from the lagged 1-, 5- and 22-day mean squared returns, fitted once, frozen and floored to stay positive |

The choice of denominator determines what the chart monitors. A constant denominator monitors the **level** of volatility: a persistent δ-fold variance increase raises the expected score δ-fold for as long as it lasts. An adaptive forecast denominator monitors **surprises relative to recent volatility**: after a change it rises with the new volatility level and can absorb part of the shift. The manuscript calls this effect *adaptation masking* and measures it with a masking ratio.

Because the scores are serially dependent, skewed and heavy-tailed, Gaussian EWMA limits are not used. Each limit is calibrated empirically on simulated in-control paths and then checked on independent paths. Full definitions, derivations, the calibration rule and the inference procedure are in the manuscript, [`report/main.tex`](report/main.tex).

## Experimental design

- **Data-generating process.** A GARCH(1,1)-*t* process (ω = 0.02, α = 0.07, β = 0.91, ν = 6) with unconditional variance 1 and a finite fourth moment.
- **Fitted systems.** Twenty independent replicates. Each has its own training path (3,500 days), an independent development path for choosing the forest's settings, and separate random streams for calibration, validation and out-of-control evaluation.
- **Changes.** A persistent multiplicative increase in the conditional variance by δ ∈ {1.5, 2, 3} on monitoring day τ = 50, with δ = 1 as the no-change counterpart. Common random numbers mean that every chart monitors identical paths.
- **Smoothing constants.** λ = 0.1 (primary) and λ = 0.2 (secondary). Neither was tuned on out-of-control results.
- **In-control target.** Each limit is calibrated on 2,000 paths so that the restricted mean in-control run length E₀[min(T, 5000)] reaches 500 days. It is accepted only if the 95% confidence interval from 2,000 independent validation paths lies within [425, 575]. All 160 calibrated configurations passed.
- **Endpoints.** The restricted mean detection delay RMD₅₀₀ (delays truncated at H = 500 days, over paths without a pre-change alarm) and the excess early-detection probability X(20) within 20 days. RMD₅₀₀ is a restricted mean and should not be read as an unrestricted out-of-control average run length (ARL).
- **Inference.** Twelve primary paired contrasts (RF − GARCH and RF − conventional for RMD₅₀₀ and X(20) at λ = 0.1) were pre-specified before the main simulation, with unadjusted 95% *t* intervals over the twenty systems. A Holm multiplicity adjustment was added after the results had been seen and is reported only as a supplementary check. The study was not formally preregistered.

## Key findings

Restricted mean detection delay RMD₅₀₀ in trading days at λ = 0.1. Lower is faster; values are means over the twenty systems.

| Variance multiplier δ | Conventional EWMA | GARCH–EWMA | RF–EWMA |
|---:|---:|---:|---:|
| 1.5 | **205.3** | 249.1 | 243.3 |
| 2 | **131.6** | 201.7 | 191.8 |
| 3 | **63.0** | 139.6 | 126.4 |

- **The conventional chart detected fastest** for every studied increase, 37.5–63.6 days sooner on average than RF–EWMA and in all twenty systems. These RF − conventional contrasts remain significant after the supplementary Holm adjustment.
- **RF–EWMA was faster than GARCH–EWMA on average,** by 6–13 days, with unadjusted intervals that exclude zero. This advantage **did not survive** the Holm adjustment (adjusted *p* = 0.053), varied strongly between fitted systems and did not extend to early detection, X(20).
- **Forecast accuracy and detection rank the methods in opposite orders.** The conventional chart's constant variance gives the least accurate forecasts but the fastest detection of persistent increases.
- The masking ratios are **consistent with adaptation masking**: adaptive denominators absorb part of a persistent change. This is a plausible explanation, not an established causal mechanism, because the charts also differ in score dependence, run-length shape and pre-change false-alarm rates.
- The data were generated by a GARCH process, which favours the GARCH forecaster. Other kinds of change, such as transient shocks, may rank the charts differently.

An independent audit recomputed the primary contrasts from the stored alarm times and matched 1,768 of 1,768 primary comparisons exactly ([`docs/p1_audit_report.md`](docs/p1_audit_report.md)). It verified the downstream calculations, not the upstream simulation that produced the alarm times.

## Real-world application: SPY

The illustrative application monitors daily returns of the SPDR S&P 500 ETF Trust (SPY), adjusted for splits and distributions, from a single Yahoo Finance snapshot obtained with `yfinance` and accessed on 27 October 2026. All models were fitted to returns from February 1993 to December 2006 and frozen. Returns from January 2007 to September 2026 were then monitored continuously. Because the fitted GARCH-*t* model failed a pre-specified finite-fourth-moment check, the GARCH denominator is a variance-targeted GARCH(1,1)-*t*; the manuscript explains this change.

| Scheme (λ = 0.1) | Exceedance days | Episodes |
|---|---:|---:|
| Conventional EWMA | 638 | 44 |
| GARCH–EWMA | 143 | 20 |
| RF–EWMA | 216 | 27 |

The conventional chart tracks the level of volatility and stayed above its limit through long high-volatility periods, for example 183 consecutive days from 15 September 2008. The forecast-standardised charts flagged shorter episodes around sharp moves. **These results are descriptive.** The true change points are unknown, an exceedance is not a verified detection, and exceedance counts do not measure detection accuracy or rank the methods. The historical reference dates are not verified statistical change points.

The SPY price snapshot is **not** included in this repository.

## Repository structure

```text
stc720-rf-ewma/
├── run.py              Experiment driver (smoke, pilot, verify; guarded production, sensitivity, benchmark and SPY modes)
├── src/                Simulation (sim), forecasters (forecast), EWMA chart and calibration (chart),
│                       replicate aggregation (aggregate), SPY data and application (spy, application), reporting (report)
├── tests/              pytest unit tests (test_core.py, test_spy.py)
├── scripts/            Run wrapper with resource and provenance logging (run_simulation.sh), independent audit,
│                       Holm analysis, diagnostics, table and figure generation, manuscript number checks
├── report/             LaTeX manuscript (main.tex), bibliography (refs.bib), figures/ and generated tables/
├── results/derived/    Summaries, tables and figures derived from the frozen runs (audits, diagnostics, paper figures)
├── docs/               Methodology, research plan, references, audit and diagnostic reports, project status records
├── data/               Empty placeholders; price data are not tracked
├── requirements.txt    Direct dependencies
└── requirements-lock.txt  Exact versions of the development environment
```

Useful starting points:

- Methodology specification: [`docs/methodology.md`](docs/methodology.md). It is a working document; where it differs from the manuscript, the manuscript is authoritative.
- Independent audit: [`docs/p1_audit_report.md`](docs/p1_audit_report.md). Supplementary Holm analysis: [`docs/p2_multiplicity_report.md`](docs/p2_multiplicity_report.md). Exploratory diagnostics: [`docs/p45_diagnostics_report.md`](docs/p45_diagnostics_report.md).
- Verified literature list: [`docs/references.md`](docs/references.md).

## Installation and environment

The project was developed on Ubuntu under WSL2 with Python 3.14.4 on CPU only.

```bash
git clone https://github.com/stephenjamespienaar/stc720-rf-ewma.git
cd stc720-rf-ewma
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements-lock.txt   # exact versions; requirements.txt lists the direct dependencies
python -m pytest -q                    # unit tests
```

The lock file pins the versions used for the reported results; with a different Python version, `requirements.txt` may be needed instead. On 2 November 2026 the test suite (134 tests) passed in the original development environment in about 20 seconds. A fresh installation from the commands above has not been tested separately.

The manuscript can be compiled from `report/` with a TeX distribution that includes `latexmk`:

```bash
cd report
latexmk -pdf main.tex
```

## Reproducibility and availability of research artifacts

| Artifact | Public in this repository? |
|---|---|
| Source code for simulation, forecasting, charts, calibration, evaluation and the SPY application | Yes (`run.py`, `src/`) |
| Unit tests | Yes (`tests/`) |
| Scripts that produced tables, figures, audits and manuscript checks | Yes (`scripts/`) |
| Generated manuscript tables and figures | Yes (`report/tables/`, `report/figures/`) |
| Summaries of audits, diagnostics and checks | Yes (`results/derived/`) |
| Complete simulation and SPY run outputs, including per-path alarm times (`results/runs/`) | **No** (git-ignored) |
| SPY price snapshot (`data/raw/`) | **No** (git-ignored) |
| Compiled manuscript PDF | **No** (git-ignored) |

Consequences for reproduction:

- The unit tests and the manuscript build use only tracked files.
- The table, figure, audit and manuscript-check scripts read the excluded run outputs. They cannot be rerun from this repository alone.
- The main simulation (twenty systems, ARL₀ = 500) took about 16.5 minutes of wall-clock time on the development machine. It is guarded by an explicit `--approved` flag. A fresh run writes a new run directory; bit-for-bit agreement of a fresh run with the frozen results has not been demonstrated.
- The SPY application needs a price snapshot. Yahoo Finance revises adjusted price histories retrospectively, so a new download may not reproduce the snapshot used in the report.

## Research report

The report is maintained in LaTeX as [`report/main.tex`](report/main.tex), with its bibliography in [`report/refs.bib`](report/refs.bib), figures in [`report/figures/`](report/figures/) and tables in [`report/tables/`](report/tables/). The compiled PDF is not tracked in the repository; it is compiled from the LaTeX source and distributed separately for academic review and submission.

## Collaboration and contributions

Group 10 collaborators can propose changes through pull requests:

1. Create a new branch for your change, for example `git switch -c fix-section-4-wording`.
2. Keep each change focused on one topic, such as a section of the report or one script.
3. Run the relevant checks: `python -m pytest -q` for code changes and a LaTeX build for report changes. Nobody needs to run the full simulation to contribute.
4. Push the branch and open a pull request on GitHub so the change can be reviewed before it is merged into `main`.

**Frozen research outputs must not be changed casually.** The reported numbers come from specific frozen runs. Edits to `results/derived/`, `report/tables/` or `report/figures/` should be regenerated from those runs by the existing scripts, never edited by hand. Changes to the scientific design need the agreement of the authors.

## Academic integrity and AI assistance

Generative AI tools were used extensively in this project, including to discuss the research design, write, test, debug and audit the Python code, review sources and draft the manuscript text. The repository includes the instruction files used by the Claude Code assistant (`CLAUDE.md` and `.claude/`). Every reported number was computed by the project code from stored outputs. The full Generative AI Use Declaration is in the manuscript, directly below the abstract and keywords. It is still subject to confirmation by all three authors.

## References and citation

The literature used in the study is listed in [`report/refs.bib`](report/refs.bib) and documented in [`docs/references.md`](docs/references.md).

This work has no DOI and is not published. Cite it as an unpublished course research report:

> Pienaar, S. J., Ford, K., & Tlou, K. (2026). *Random Forest–EWMA monitoring of financial market volatility: A simulation study and an application to the SPDR S&P 500 ETF* [Unpublished STC 720 research report, Group 10]. Department of Statistics, University of Pretoria. https://github.com/stephenjamespienaar/stc720-rf-ewma

## License

This repository does not include a license file. No open-source license has been granted, so default copyright applies. Contact the authors before reusing the code or text.
