# Research Plan — RF–EWMA Monitoring of Financial Volatility

*STC 720 individual research project, University of Pretoria. Version 1.0, 13 Oct 2026.*
*Submission deadline: Thu 5 Nov 2026, 23:59 SAST (ClickUP).*

Companion documents: [`methodology.md`](methodology.md) (numbered equations, design labels) and [`references.md`](references.md) (verified bibliography and evidence status).

---

## 1. Scope and administrative decisions

| Item | Decision (user-confirmed 13 Oct 2026) |
|---|---|
| Assignment mode | **Individual project.** The rubric header says "Group of 3 students"; the student is undertaking it individually. All workload planning assumes one person. |
| Code submission | The complete source code, tests, configurations and reproduction scripts live in the student's GitHub repository. The report appendix gives a concise description of the implementation and reproduction instructions, plus the repository link. Code is **not** compressed to fit the appendix. |
| Git | Claude Code performs read-only Git inspection only. The student alone stages, commits, pushes and publishes. No AI co-author attribution. |
| Rubric topic | ML-based frameworks #16 "Machine learning control chart for monitoring financial time-series data". |
| Phase authorised | Phase 1: planning docs, core implementation, unit tests, smoke test, reduced feasibility pilot. **Production simulations need separate approval after pilot review.** |

## 2. Research objective

To evaluate, by Monte Carlo simulation and a descriptive SPY illustration, whether standardizing squared returns by a **Random Forest (RF)** one-step variance forecast gives a one-sided EWMA chart that detects persistent changes in the volatility-generating process better or worse than two classical charts. All three charts are calibrated to a common in-control average run length (ARL₀).

The study does **not** assume the RF-based chart is superior. Negative or mixed results will be reported as found.

## 3. Charts compared

All charts monitor the same score u_t = r_t²/d_t with the same EWMA and calibration; only the denominator differs (methodology §4–5).

| Chart | Denominator d_t | Adapts to new data? | Status |
|---|---|---|---|
| Conventional EWMA | training sample variance s² | no | established (squared-observation EWMA; Schipper & Schmid 2001 §3.1; MacGregor & Harris 1993) |
| GARCH–EWMA | frozen GARCH(1,1)-t filter ĥ_t | filter updates; parameters frozen | established form (residual chart, Schipper & Schmid 2001 §3.5), here with *estimated* parameters |
| RF–EWMA | frozen RF on lagged squared-return features | features update; forest frozen | proposed combination |

A known-parameter GARCH denominator (the filter with the true in-control parameters, equal to h_t in control) is computed in simulation as an **internal diagnostic only**. It is not a fourth competitor.

## 4. Research questions

- **RQ1 (forecasting).** Can an RF trained on HAR-type lagged squared returns produce positive, well-calibrated one-step variance forecasts? How close do they come to a fitted GARCH(1,1)?
- **RQ2 (monitoring).** At a common validated ARL₀, how do the conventional, GARCH- and RF-standardized EWMA charts compare in detecting a persistent volatility-scale increase?
- **RQ3 (adaptation masking).** How much of a persistent shift does each chart still "see" after its forecaster has adapted? How does this split detection into initial sensitivity and sustained response?
- **RQ4 (illustration).** How do the three charts behave on SPY daily returns, 2007–2026? This is descriptive only.

## 5. Pre-registered hypotheses and expectations

These are fixed before the pilot is run. Directional statements follow from theory (methodology §8–9), not from assumed results.

| ID | Statement | Basis |
|---|---|---|
| H1 | Forecast accuracy (QLIKE against true h_t): oracle < GARCH ≤ RF < constant. GARCH is correctly specified, so the RF is not expected to beat it. | Correct specification of GARCH under the DGP |
| H2 | All charts can be calibrated to ARL₀ = 500 and validated on independent paths within ±15%. | Empirical calibration (methodology §6) |
| H3 | The GARCH-standardized chart shows a transient after the change, with ū_E/ū₀ near δ. Its sustained masking ratio M_G is near the first-order prediction: 0.16, 0.125 and 0.09 for δ = 1.5, 2, 3 under the pilot DGP. The conventional chart has M ≈ 1. | Derived (methodology eq. 20) |
| H3-RF | Exploratory, no directional hypothesis. RF saturation (no extrapolation) may give M_RF > M_G for large δ, at the cost of a higher in-control spread. | Derived property of RF predictions |
| H4 | No directional hypothesis between charts for detection delay. Paired differences with CIs are reported. | Prior evidence (Schipper & Schmid 2001) favours the residual chart, but under known parameters, change at t = 1, normal innovations and ARL₀ = 60, which differs from our design |

## 6. Design summary (details in methodology)

| Element | Adopted value | Note |
|---|---|---|
| In-control DGP | GARCH(1,1), standardized Student-t, α = 0.07, β = 0.91, ν = 6, σ² = 1 (ω = 0.02) | **Default D1 adopted.** 4th-moment value 0.985 < 0.99. SPY-training estimates to be reported alongside once the SPY snapshot exists |
| Fault | Persistent scale change r_t → √δ r_t for t ≥ τ, δ ∈ {1.5, 2, 3} | Schipper & Schmid (2001) eq. 3 with a = 0, Δ = √δ |
| Target ARL₀ | 500 trading days | **Default D2** |
| Change point | monitoring day τ = 50 | after a 250-day pre-monitoring history |
| λ | 0.1 primary, 0.2 secondary; same grid for all charts | not tuned on out-of-control results |
| Masking windows | early k ∈ [0, 19], sustained k ∈ [100, 499] | |
| Training length | n = 3,500 days (≈ SPY 1993–2006) | |
| RF | `RandomForestRegressor`, squared error. Grid `min_samples_leaf` ∈ {50, 200, 800} × `max_features` ∈ {1, 3}, chosen by development-path QLIKE | `max_features` = 1 is the p/3 Breiman–Cutler default used by Christensen et al. (2023); 3 is sklearn's default (bagging) |
| SPY | train 1993-02 → 2006-12; monitor 2007-01 → 2026-09-30; model-based UCL | **Default D3**, executed after pilot approval |

## 7. Experimental roles (no leakage)

Training → development (RF grid) → calibration of h* → independent in-control validation → out-of-control evaluation (common random numbers, CRN) → SPY monitoring window (untouched until used once).

Each role draws from its own `SeedSequence` stream. RF tuning uses forecast loss only, never detection results.

## 8. Feasibility pilot (Phase 1)

**Size:**
- 1 training replicate
- 100 trees
- 300 calibration paths (T_max = 3,000)
- 300 validation paths
- 300 out-of-control paths per δ (H = 500)

**Success criteria (fixed in advance):**

| Q | Criterion |
|---|---|
| Q1 | RF forecasts finite and > 0; floor binds on < 0.1% of days; RF closes ≥ 50% of the constant-to-oracle QLIKE gap; mean u_RF ∈ [0.9, 1.1] |
| Q2 | No NaN/inf; identical outputs on rerun with the same seed |
| Q3 | Censored fraction < 1%; validation passes for all charts |
| Q4 | Restricted delay decreases in δ; masking metrics computed; GARCH M compared with theory |
| Q5 | Paired comparisons computable (no requirement that RF wins) |
| Q6 | Pilot < 10 min, peak RSS < 4 GB; production cost extrapolated |

**Stop rules:**
- Q1 or Q3 fails → stop, diagnose, report. No rescue by parameter search.
- Complete masking is a finding, not a failure.

**Decision gate:** the student reviews the Phase 1 report and approves (or changes) the production configuration.

## 9. Report mapping (rubric page budgets)

| Section | Content | Budget |
|---|---|---|
| Abstract (150–250 words), ≥3 keywords, generative AI declaration below keywords | | |
| 1 Introduction | SPC for dependent data (Alwan & Roberts 1988), finance SPC (Schipper & Schmid 2001; Dumičić & Žmuk 2015 as cautionary), ML volatility (Christensen et al. 2023) | ±1 p |
| 2.1 Existing charts | EWMA (Roberts 1959), squared-observation and residual charts, GARCH (Bollerslev 1986) | ±1.5 p |
| 2.2 Machine learning | RF regression (Breiman 2001), target and features, evaluation (Patton 2011) | ≤2 p |
| 3 Proposed chart | score, EWMA, calibration, run-length conventions, masking theory | ≤3 p |
| 4.1 / 4.2 Results | ≥1 table (title above), ≥1 figure (caption below) | ≤2 p + 1 p |
| 5 Illustrative example | SPY, descriptive only | ±2 p |
| 6 Conclusion | | ±½ p |
| Appendix | implementation summary, reproduction steps, GitHub link | ±1.5 p |

## 10. Timeline

| Dates | Work |
|---|---|
| 13–17 Oct | Phase 1: docs, code, tests, smoke, pilot, completion report |
| 18 Oct | **Gate:** pilot review and production approval (student) |
| 19–22 Oct | Production simulation; SPY snapshot and application; results freeze |
| 15–23 Oct | Draft Introduction, Background, Method (in parallel) |
| 23–31 Oct | Results, Application, Conclusion, Abstract, Appendix |
| 1–3 Nov | Number tracing, proofreading, AI declaration, Turnitin (≤20%) |
| **4 Nov** | **Submit on ClickUP** (buffer to 5 Nov 23:59) |

## 11. Main risks

| Risk | Mitigation |
|---|---|
| Scope creep | Optional extensions (dynamics or tail change, GJR) only after production finishes |
| GARCH home advantage under GARCH DGP | Stated up front; SPY gives a real-data contrast |
| Results conditional on one trained model | Replicates sized from pilot timings |
| Model-based SPY UCL favours GARCH | Disclosed; SPY results descriptive only |
| Two references without full text | MacGregor & Harris (1993) and Lu & Reynolds (1999) are cited at metadata level only (see `references.md`) |
