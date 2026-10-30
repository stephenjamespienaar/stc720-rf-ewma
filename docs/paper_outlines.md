# Writing outlines for the student-written sections

*Prepared 30 Oct 2026 (Stage 1) for the student's own writing of the Abstract, Introduction, Discussion and Conclusion. These are outlines, arguments and verified evidence, not prose to copy. Every number below is in `report/tables/values.json` (key in brackets) or in the cited project report, and traces to a frozen, hash-checked output. Use "pre-specified", never "pre-registered".*

**Evidence tiers.** Label every claim with the tier it belongs to:

| Tier | What it is | How to word it |
|---|---|---|
| **Primary** | The 12 pre-specified paired contrasts (λ = 0.1; RMD₅₀₀ and X(20); RF − GARCH and RF − conventional; δ ∈ {1.5, 2, 3}), with unadjusted 95% t₁₉ intervals over R = 20 systems | "the pre-specified primary contrasts", "unadjusted 95% intervals" |
| **P1-verified** | The primary contrasts recomputed independently from the stored alarm times (1,768/1,768 identical) | "independently recomputed from the stored alarm times". Never say the simulation itself was verified |
| **Supplementary, post hoc** | Holm adjustment over the 12 contrasts, decided after the results were seen | "as a supplementary, post hoc check" |
| **Exploratory** | P4 heterogeneity and P5 run-length shape; descriptive, no p-values | "an exploratory, descriptive analysis suggests / is consistent with" |
| **Descriptive** | SPY application | "the charts flagged …", never "detected" a change; no accuracy claims |

**Two different "500"s; never conflate them:**
- **RMD₅₀₀** (simulation): the restricted mean *detection delay*, E[min(D, 500)] with horizon H = 500 after the change at τ = 50. A delay, not an ARL₁.
- **E[min(T, 5000)] = 500** (SPY calibration): the restricted mean *in-control run length* targeted when calibrating h* under the fitted SPY model. It is not E[T].
- In the simulation, ARL₀ = 500 is validated as the restricted mean over 5,000 days with at most 0.05% censoring.

---

## A. Abstract (150–250 words; write last)

**Suggested move order (one or two sentences each):**
1. **Problem.** Monitoring for persistent increases in financial volatility. Control charts for squared returns must handle conditional heteroskedasticity.
2. **Method.** One-sided EWMA on the score u_t = r_t²/d_t. Three denominators: the constant training variance (conventional), a frozen GARCH(1,1)-t filter, and a frozen random-forest forecast from lagged squared-return features (proposed). All are calibrated by simulation to a common ARL₀ = 500.
3. **Design.** Monte Carlo under a GARCH(1,1)-t process with a persistent variance-scale change δ ∈ {1.5, 2, 3}; R = 20 independently trained and calibrated systems; paired common random numbers.
4. **Main result (primary).**
   - The conventional chart detected fastest: RMD₅₀₀ 205 / 132 / 63 days, against RF 243 / 192 / 126 and GARCH 249 / 202 / 140.
   - RF − conventional contrasts were large, consistent across all 20 systems, and survived the supplementary Holm adjustment.
   - RF had shorter mean restricted delays than GARCH (6–13 days; unadjusted CIs exclude 0), but this did not survive Holm (adjusted p = 0.053) and varied strongly between systems. There was no difference in X(20).
5. **Mechanism (careful).** The ranking runs opposite to forecast accuracy (QLIKE: GARCH 0.812 < RF 0.841 < conventional 1.019). It is consistent with *adaptation masking*: adaptive denominators absorb a persistent change. This is consistent with the results, not proven as the cause.
6. **Application (descriptive).** SPY 2007–2026, with models trained on 1993–2006. The conventional chart was above its limit on 12.8% of days in 44 episodes, against 2.9% / 20 for GARCH and 4.3% / 27 for RF. These are descriptive counts, not detection accuracy.
7. **Take-away.** Better variance forecasts do not by themselves give faster detection of persistent volatility increases. The choice of denominator decides what the chart monitors: the variance level, or surprises relative to a forecast.

**Keywords (already in the scaffold, ≥ 3):** EWMA control chart; random forest; GARCH; conditional heteroskedasticity; volatility monitoring; run length; S&P 500.

---

## B. Introduction (±1 page; Claude drafts the "Related literature" paragraph separately)

**B1. Motivation (1 paragraph).**
- Volatility monitoring matters for risk management.
- Daily returns are conditionally heteroskedastic (Bollerslev 1986).
- Classical charts assume iid observations. Applied naively to financial data they over-signal: Dumičić & Žmuk (2015) report many signals, mostly regarded as false alarms, when charting index price levels. Use it only as a cautionary example.

**B2. The residual-chart idea and its tension (1 paragraph).**
- Alwan & Roberts (1988): fit a time-series model and chart the one-step prediction errors. They address the mean; applying the idea to the variance is this study's extension.
- Schipper & Schmid (2001): EWMA charts for GARCH processes, including a residual chart (X_t − μ₀)²/σ̂²_t. Under known parameters, normal innovations and in-control ARL 60, it was best in nearly all their cases.
- **The tension to set up:** a forecast that adapts to the data will also *adapt to a persistent change*, absorbing part of the signal the chart is meant to detect.

**B3. Machine learning (1 short paragraph).**
- ML forecasts of realized variance are competitive with HAR-type models (Christensen et al. 2023; their target is intraday realized variance, much less noisy than daily r²).
- Random forests (Breiman 2001) give positive, bounded, non-extrapolating predictions. That property matters here: an RF cannot predict variance far beyond its training range.
- ML has been used in control charts mainly as a classifier, e.g. RF-based real-time contrasts (Lee et al. 2020; cite at abstract level as a materially different formulation). This work instead uses an RF as a *variance forecaster* inside a classical EWMA.

**B4. Gap and research questions (bullets in prose).**
- RQ1: Can an RF trained on lagged squared returns give positive, calibrated one-step variance forecasts, and how close are they to a fitted GARCH?
- RQ2: At a common validated ARL₀, how do the three charts compare in detecting a persistent variance increase?
- RQ3: How much of a persistent shift does each chart still "see" after its forecaster adapts (adaptation masking)?
- RQ4: How do the charts behave on SPY 2007–2026 (descriptive)?

**B5. Contributions (3 bullets in prose).**
1. A like-for-like comparison: a common score, a common EWMA and simulation-calibrated limits validated on independent paths.
2. A replicate design with 20 independently trained systems, which separates Monte Carlo error from between-system variability.
3. Evidence that forecast accuracy and detection speed can rank charts in opposite orders, with a real-data illustration.

**Do not claim:**
- that any paper validates RF–EWMA;
- anything from MacGregor & Harris (1993) or Lu & Reynolds (1999) beyond their titles (metadata only).

---

## C. Discussion (closes §4.2; about ½ page within the 3-page §4 allocation)

**C1. Accuracy–detection inversion (the central point).**
- Forecast ranking by QLIKE against the true h_t [prod:forecast_diag/*/qlike_true]: oracle 0.810 ≈ GARCH 0.812 < RF 0.841 < conventional 1.019.
- The detection ranking is the reverse: conventional < RF < GARCH ≈ oracle in RMD₅₀₀ (Table 1).
- Interpretation: the conventional denominator is fixed, so a persistent δ-fold increase raises the expected score by δ indefinitely (M = 1 by construction). An adaptive denominator raises it only briefly.

**C2. Adaptation masking as the consistent explanation (not proof).**
- Sustained masking ratio M [prod:masking/*/M]: RF 0.342 / 0.308 / 0.281 against GARCH 0.243 / 0.198 / 0.144 (δ = 1.5 / 2 / 3); oracle 0.230 / 0.186 / 0.134.
- The M ranking matches the RMD ranking. RF retains more of the shift because its predictions saturate: in the simulation the RF slope on the true variance is 0.348 against GARCH 0.999 [prod:forecast_diag/rf/slope_h].
- **Wording:** "consistent with"; the charts also differ in run-length shape and score dependence, so causation is not shown.
- The first-order masking theory under-predicts the empirical M by about 0.05–0.07 (production-results.md).

**C3. RF versus GARCH: modest and fragile.**
- Unadjusted primary result: RF − GARCH RMD₅₀₀ of −6.05 / −9.94 / −13.13 days, with CIs excluding 0.
- Not robust to the post hoc Holm adjustment (adjusted p 0.053 at each δ).
- Only 14–15 of 20 systems favour RF.
- No difference in early detection: X(20) contrasts near 0, Holm p = 1.
- **P4 (exploratory):** the between-system spread is 3.4–8.2× the Monte Carlo SE under a change. Each system's effect is stable across δ and λ (ρ 0.85–0.97). Larger RF advantages go with RF systems that retained more of the shift (masking gap, ρ −0.80 to −0.89). Practical meaning: a single fitted RF system may favour either method.

**C4. Equal ARL₀ ≠ equal early false-alarm risk (P5, exploratory).**
- Pre-change false-alarm probability P(T < 50) [prod:validation/0.1/*/p_lt_tau]: conventional 0.125 against GARCH 0.096, RF 0.104 and oracle 0.095. A geometric run length would give 0.093.
  - These are the independent-validation values used in Table 1.
  - The earlier project documents quote the out-of-control paths' pre-change values (conventional 0.125, GARCH 0.094, RF 0.102, oracle 0.093; `ooc/*/p_prechange_fa`), which differ only by Monte Carlo error.
  - Use one source consistently in the paper: the Table 1 values.
- The conventional run length is over-dispersed (CV 1.04).
- This is why the RF − conventional RMD contrast is already −3.80 days at δ = 1, and why X(k), which subtracts the no-change baseline, is the cleaner early-detection comparison.
- Context: Lucas & Saccucci (1990) show a nearly geometric in-control EWMA run length for iid normal data. Squared returns under GARCH are neither iid nor normal, so near-geometric behaviour cannot be assumed here.

**C5. Limits on generalization.**
- The DGP is GARCH(1,1)-t, which gives the GARCH forecaster a home advantage.
- The fault is a pure persistent scale change.
- RMD is censored at H = 500 (GARCH censoring 21% at δ = 1.5).
- IC validation is conditional on h*.
- No multiplicity adjustment was pre-specified.

---

## D. Conclusion and recommendations (±½ page)

**D1. Answers to the RQs (one sentence each):**
- RQ1: the RF gave positive, finite forecasts (the floor never bound) and closed 85% of the constant-to-oracle QLIKE gap, but responded only weakly to the true variance (slope 0.35).
- RQ2: the conventional chart detected fastest. RF beat GARCH on mean restricted delay by a modest, multiplicity-fragile and system-dependent margin.
- RQ3: masking ranks conventional (1) > RF > GARCH ≈ oracle.
- RQ4: on SPY the GARCH- and RF-standardized charts flagged short episodes around the reference stress dates, while the conventional chart stayed above its limit for long high-volatility stretches (longest 183 days from 2008-09-15). Descriptive only.

**D2. Main message.**
- Choosing the denominator chooses the monitoring target.
- A constant denominator monitors the *level* of volatility and is fast for persistent increases.
- A forecast denominator monitors *surprises relative to recent volatility* and largely adapts away persistent changes.
- Better forecasts are not automatically better monitors.

**D3. Recommendations (practical and future work):**
- Match the denominator to the change of interest. Use a level-type chart for regime shifts, and a residual-type chart for shocks relative to the current regime.
- Validate in-control performance by simulation or empirically, not from Gaussian EWMA limits.
- Future work:
  - non-GARCH or regime-switching DGPs (removing the home advantage);
  - the deferred ARL₀ = 100 sensitivity;
  - CUSUM-type charts;
  - realized-variance targets for the RF (Christensen et al. 2023);
  - limits that account for calibration uncertainty.

**D4. Limitations to restate briefly:** simulation DGP; restricted delays; unadjusted primary inference; descriptive SPY results with model-based limits that favour GARCH and an infinite fourth moment.

---

## E. Verified SPY facts for any section (all descriptive)

- **Data.** Yahoo Finance adjusted SPY prices. Training returns 1993-02-01 to 2006-12-29 (n = 3,507); monitoring returns 2007-01-03 to 2026-09-30 (n = 4,967).
- **Calibration model.**
  - Variance-targeted GARCH(1,1)-t: ω 0.0051, α 0.0593, β 0.9363, ν 7.63; persistence 0.9955; fourth-moment coefficient 1.0039 ≥ 1, so E r⁴ = ∞.
  - Variance targeting was adopted after the strict fourth-moment gate stopped the first run, using training data only. It sets the model variance equal to s² = 1.144, against 1.920 for the unrestricted fit.
- **Literature context (Francq, Horváth & Zakoïan 2011; preprint read).** The VT estimator is consistent under mild conditions, but its asymptotic normality requires E ε⁴ < ∞, and for daily index returns this moment condition is often doubtful. Their second step is Gaussian QML, while this study uses a Student-t likelihood. Cite them for the method and the caveat, not as theory for this exact estimator.
- **Limits.** h* = 1.957 / 2.598 / 2.470 (conventional / GARCH / RF, λ = 0.1).
  - Validation 483.5 / 489.2 / 477.4, all passing eq. (3).
  - Two calibration-overshoot warnings at λ = 0.2 (500.6 and 500.8 against the target 500).
- **Monitoring (λ = 0.1).**
  - Exceedance days 638 / 143 / 216; episodes 44 / 20 / 27; longest 183 / 24 / 61 days.
  - QLIKE against r²: 1.462 / 0.915 / 0.986.
  - The RF denominator stayed within 0.277–3.367, against GARCH up to 27.4. This is RF saturation, visible in Figure 5.
- **Never write:** "detected the crisis", "false alarms" (the in-control state of real data is unknown), "more accurate", or anything about trading.
