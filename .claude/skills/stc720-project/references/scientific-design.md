# Scientific design, pilot evidence and corrected interpretations

The authoritative full definitions are in [`docs/methodology.md`](../../../../docs/methodology.md) (equations 1–22, labelled [E]/[L]/[P]/[D]) and [`docs/research_plan.md`](../../../../docs/research_plan.md). This file summarises them and adds the corrections from the production-readiness review.
- **Applied on 14 Oct 2026** to the pilot report and methodology (independent-audit remediation): corrected interpretations 1, 2, 4 and 5 below, and errata A2 and A6–A8.
- **Applied on 14 Oct 2026 (session 3, C7):** A1 (8-row table), A3 ("1 by construction"), A4 (M has no SE in the pilot) and A5 (X̂(k) derived from stored values); no pilot rerun.
- **Phase 2 estimators (14 Oct 2026):** methodology v1.2 eqs. 23–28 — normal paired SE, X(k), censoring-aware quantiles, masking delta-method SE, equal-weight replicate aggregation with the residual between-system SD σ̂_sys (training, model selection, forest randomness and calibration; descriptive, after the Phase 2 audit relabelling); 12 pre-registered primary contrasts (§7.4); production seed 20261014 (§10.1).

## Research questions

| RQ | Question |
|---|---|
| RQ1 | Can an RF on HAR-type lagged squared returns give positive, calibrated one-step variance forecasts, and how close does it come to GARCH? |
| RQ2 | At a common validated ARL₀, how do the three charts compare in detecting persistent volatility-scale increases? |
| RQ3 | How much of a persistent shift does each chart retain after its forecaster adapts (adaptation masking)? |
| RQ4 | How do the charts behave on SPY in 2007–2026? Descriptive only. |

**Forecasting accuracy and change-detection efficiency are different objectives.** A better forecaster adapts faster and therefore *masks* persistent shifts. The pilot ranked forecasting accuracy and detection speed in opposite orders. No scheme is claimed to be universally superior.

## The three primary charts and the diagnostic

All charts monitor the same score, and differ only in the denominator $d_t$:

$$u_t=\frac{r_t^2}{d_t},\qquad Z_t=\lambda u_t+(1-\lambda)Z_{t-1},\ Z_0=1,\qquad T=\inf\{t\ge1:Z_t>h\}.$$

The chart is one-sided upper. $h$ is calibrated empirically; Gaussian limits are not used.

| Chart | $d_t$ | Frozen after training | Updates sequentially from new returns |
|---|---|---|---|
| 1. Conventional EWMA | training variance $s^2=\frac1n\sum r_i^2$ | $s^2$ | nothing |
| 2. GARCH–EWMA | $\hat h_t=\hat\omega+\hat\alpha r_{t-1}^2+\hat\beta\hat h_{t-1}$ (GARCH(1,1)-t, ML via `arch`, zero mean) | $\hat\theta$ | the filter state |
| 3. RF–EWMA | $\max\{\hat f(x_t), 10^{-4}s^2\}$, with $x_t=(r_{t-1}^2,\ \overline{r^2}_{t-5..t-1},\ \overline{r^2}_{t-22..t-1})$; squared-error RF on target $r_t^2$ | the forest | the lagged-feature inputs |
| Diagnostic only ("oracle") | GARCH filter with the **true in-control** parameters, known and frozen | – | the filter state |

- The diagnostic is **not a fourth competitor**. It equals $h_t$ while in control, so its input is iid and the Brook–Evans ARL check applies. It must **not** use the true post-change variance; that would blind it to the change.
- No signed-return (leverage) feature is used, so information use is symmetric with GARCH(1,1).
- RF grid: `min_samples_leaf` ∈ {50, 200, 800} × `max_features` ∈ {1, 3}, selected by development-path QLIKE against $r^2$ (never by detection results). Tree predictions are summed in a fixed order, so results are deterministic.

## Primary simulation (approved)

**Data-generating process:**
- In control: GARCH(1,1), $r_t=\sqrt{h_t}\eta_t$, $h_t=\omega+\alpha r_{t-1}^2+\beta h_{t-1}$, with standardized Student-$t_\nu$ innovations.
- Parameters: **α = 0.07, β = 0.91, ν = 6, σ² = 1 (ω = 0.02)**. Persistence is 0.98, κ_η = 6, and the 4th-moment coefficient β² + 2αβ + κα² = 0.985 (required ≤ 0.99).

**Constraints asserted in code:**
- ω > 0
- α, β ≥ 0
- α + β < 1
- ν > 4
- 4th-moment margin
- fitted GARCH checked after every fit

**Fault:** a persistent scale change $r_t\to\sqrt\delta\,r_t$ for $t\ge\tau$, with δ ∈ {1.5, 2, 3}. It is exactly GARCH(δω, α, β) after the change, and is the fault model of Schipper & Schmid (2001) eq. 3 with Δ = √δ, a = 0.

**Fixed settings:**
- ARL₀ target **500** (sensitivity: 100, secondary)
- λ = **0.1** primary, **0.2** secondary; never tuned per chart on out-of-control results
- change point at monitoring day **τ = 50**
- burn-in 500, pre-monitoring history W = 250
- n_train = n_dev = 3,500

**Independent roles**, each with its own `SeedSequence(master, spawn_key=(replicate, role))` stream: training, development, calibration, validation, out-of-control (OOC), RF seed, bootstrap.
- Calibration paths are shared by all chart × λ configurations within a replicate; each chart gets its own h*.
- Validation paths are independent of calibration.
- OOC base paths are reused across all δ with common random numbers (CRN).
- δ = 1, the no-change counterfactual of the same paths, is always evaluated.

**Run lengths:**
- One monitoring opportunity is one trading day after the history window.
- Restricted mean $\hat A(h)=\frac1N\sum\min(T_i,T_{\max})$; $h^*=\min\{h:\hat A\ge A_0\}$ by bisection.
- Validation (amended 14 Oct 2026, after the benchmark, before production; methodology §6, eq. 29): passes iff the whole independent-validation 95% CI lies in $[A_0(1-0.15), A_0(1+0.15)]$, i.e. [425, 575] at ARL₀ = 500 and [85, 115] at 100; bounds inclusive, compared exactly (`chart.ic_equivalence`). The CI is conditional on h* (calibration uncertainty excluded), so the rule is not a complete equivalence test, and individual CIs give no family-wise coverage. The original rule ($A_0$ in the 95% CI and within ±15%) judged the pilot and the benchmark; those recorded outcomes are unchanged.
- Production failure handling: run all R = 20 replicates; never drop, replace or recalibrate on validation; report every per-replicate result and pass counts; flag failures next to the primary results.
- **Pre-change false alarm:** T < τ. These are counted and excluded from delay statistics, which are conditional on T ≥ τ.
- Delay $D=T-\tau+1$; restricted delay $D_H=\min(D,H)$; right-censored if $T>\tau+H-1$.
- Never call a restricted mean "ARL₁".

## Adaptation masking

**Definition (exact, as coded):**
- $\bar u_S(\delta)$ is the mean of $u$ over **all OOC paths** and days τ+100 … τ+499.
- $\bar u_S(1)$ is the same quantity on the **same paths without the change** (CRN counterfactual).

$$M=\frac{\bar u_S(\delta)/\bar u_S(1)-1}{\delta-1}.$$

M is the fraction of the shift still visible after adaptation. It is a ratio of pooled means, and independent of λ and of alarms. The early window is k ∈ [0, 19].

**Conventional chart: M ≡ 1 by construction (algebraic, not empirical).** On the same path, $u_t(\delta)=\delta u_t(1)$ for every post-change day, because the denominator is fixed and the fault is purely multiplicative. M = 1 is therefore an exactness check and carries no comparative evidence.

**First-order theory for the frozen GARCH filter:**

$$R_G(\delta)=\frac{\delta(\hat\omega+\hat\alpha\sigma^2)}{\hat\omega+\hat\alpha\delta\sigma^2},\qquad M_G=\frac{R_G-1}{\delta-1},$$

with the bound $(1-\beta)/\alpha\approx1.29$. This is a ratio-of-means approximation. In the pilot it **underestimated M by about 30–35%**, as Jensen's inequality predicts.

**Transient:** every adaptive denominator is $\mathcal F_{\tau-1}$-measurable, so on day k = 0 the paired ratio equals δ exactly for every chart. GARCH then adapts within about 30–50 days.

## Phase 1 pilot evidence (one training replicate, 300 paths per role)

Full tables are in `results/runs/pilot_20261013T075339_142070/tables.md` (git-ignored, regenerable). The narrative summary is [`docs/phase1_pilot_report.md`](../../../../docs/phase1_pilot_report.md); read it together with the corrections below.

- **29 tests passed.**
- **8 configurations** = 3 primary charts × 2 λ (**6 primary**) + oracle × 2 λ (**2 diagnostic**). All 8 validated at ARL₀ = 500; validated ARL₀ was 467–511. Calibration censoring was ≤ 1/300 (0.33%; one path, conventional chart, λ = 0.1), and validation censoring was 0.
- **Markov-chain check:** Brook–Evans ARL 508 against validated 511 (λ = 0.1), and 488 against 473 (λ = 0.2).
- **Forecast accuracy (QLIKE against true h):** oracle 0.810 < GARCH 0.811 < RF 0.835 < constant 1.003.
  - RF closes 87% of the constant-to-oracle gap.
  - RF forecasts respond less than proportionally to h: slope 0.345 on h, correlation 0.684. The cause is not isolated (interpretation 5).
  - The pilot slope values carry an n/(n−1) normalisation factor (1 + 1.1×10⁻⁶; ddof mismatch), fixed in code on 14 Oct (`forecast.slope`).
  - Floor binds 0 of 900,000.
- **Detection at δ = 2, λ = 0.1** (restricted to H = 500):

  | Chart | Median delay (days) | Restricted mean |
  |---|---|---|
  | Conventional | 94 | 134.5 |
  | RF | 137 | 183.5 |
  | GARCH | 158 | 211.3 |

  At δ = 3 the medians were 37 / 68 / 93.
- **Masking M** (δ = 1.5 / 2 / 3):

  | Chart | M |
  |---|---|
  | GARCH | 0.200 / 0.160 / 0.114 |
  | RF | 0.384 / 0.353 / 0.336 |
  | Known-parameter GARCH | 0.226 / 0.182 / 0.132 |
  | Conventional | 1 by construction |
- **Alarm occupancy** in days 100–499 at δ = 3: conventional 0.295, RF 0.112, GARCH 0.018. The no-change baselines are 0.042, 0.018 and 0.009.
- **Resources:** 4.10 s wall, 7.0 s CPU, peak RSS 364,856 KiB (356.3 MiB, 373.6 MB), measured with GNU `time`.

**Corrected interpretations (from the readiness review; they override the pilot report):**
1. The RF − GARCH contrast "−28 days" is a **paired difference in restricted mean delay** (H = 500) over the 271 paths where neither chart false-alarmed before τ. It is not a difference of medians: 137 − 158 = −21. The CI is a percentile bootstrap over paths, which preserves the CRN pairing (implied within-path correlation ≈ 0.74).
2. Pilot CIs are **conditional on one trained system** (fitted θ̂, one RF, one s², fixed h*). They exclude variation across training replicates, calibration uncertainty and multiplicity. "Significantly faster" means only that the Monte Carlo CI excludes zero *for that replicate*.
3. **Late alarms must be read against the no-change baseline.** With no change, 64–67% of evaluable paths alarm within 500 days after τ, and P(late | D > 20) is 0.62–0.65.
4. Restricted delays already differ between charts with no change (conventional 321 against RF 303). This may come from conditioning on T ≥ τ combined with non-geometric run lengths, as well as Monte Carlo noise. Always report each contrast's δ = 1 counterpart.
   - Pilot δ = 1 paired contrasts at λ = 0.1: RF − GARCH −3.5 [−14.4, 8.3]; RF − conventional −14.3 [−34.9, 5.9]. All six δ = 1 CIs include 0.
   - Per-chart summaries use each chart's own evaluable set (267 conventional, 279 GARCH, 273 RF). Contrasts use the pairwise intersections (271 and 262 paths).
5. The RF chart's detection advantage over GARCH is **not explained by better forecasting**, since its QLIKE is worse. It **coincides with** reduced forecast responsiveness (slope 0.345) and a higher retained shift (M ≈ 0.34–0.38). The cause is **not isolated**: even the exact E[h|x] has slope var(E[h|x])/var(h) < 1, so limited predictor information, estimation, regularization or saturation could each contribute (methodology §9).
6. The reversal of Schipper & Schmid's (2001) ranking may reflect the higher ARL₀ (sustained signal versus transient signal). This is **untested**; the ARL₀ = 100 sensitivity run addresses it, and no causal claim should be made.

## Known limitations to state in the article

- GARCH has a home advantage under a GARCH DGP.
- Symmetric information only (no leverage).
- Results are conditional on the training replicates and n_train = 3,500.
- The masking theory is first-order.
- The SPY UCL rests on an assumed in-control model.
- Two references are metadata-only.
