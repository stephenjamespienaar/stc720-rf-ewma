# P2: supplementary post hoc multiplicity analysis of the primary contrasts

*27 Oct 2026. Input: the frozen, P1-audited `results/runs/production_20261014T060921_145897/results.json` (SHA-256 `716862ab…`). Script: `scripts/p2_holm.py` (SHA-256 `36453af7…`), run on HEAD `53552a9`. Outputs: `results/derived/p2_holm/`. No simulation was run, and no frozen file was changed.*

> **Status of this analysis.** It is **supplementary and post hoc**. It was decided on 27 Oct 2026, after the primary production results had been seen, and it is **not** a pre-registered adjustment. The pre-registered primary analysis (methodology §7.4) is unchanged: the unadjusted estimates and unadjusted 95% t₁₉ confidence intervals of the 12 primary contrasts, with no multiplicity adjustment. Those values are reproduced unchanged below. The Holm results complement them and do not replace them.

## 1. Specification (fixed before any p-value was computed)

**Inferential target.** The mean paired contrast across independently generated and fitted monitoring systems, under the specified simulation design. The design is:
- a GARCH(1,1)-t DGP
- ARL₀ = 500 and λ = 0.1
- restricted delay at H = 500
- paths in the common survivor set E_a ∩ E_b

The target is **not** consistent superiority in every fitted system, and **not** superiority in real markets.

**Family.** The m = 12 pre-specified primary contrasts:
- pairs: {RF − GARCH, RF − conventional}
- metrics: {paired RMD₅₀₀, paired X(20)}
- δ ∈ {1.5, 2, 3}

The δ = 1 RMD baselines are shown for context and are outside the family. The δ = 1 X(20) baselines are 0 by construction.

**Test.** A two-sided one-sample t test of H₀: θ = 0 on the R = 20 equal-weight replicate estimates θ̂_r:
- t = θ̄ / (s_b/√20), with df = 19
- This is the framework of the stored t₁₉ intervals (eq. 27). By duality, 0 lies outside the 95% CI exactly when p < 0.05, which was checked for all 14 rows.

**Adjustment.** Holm step-down, controlling the family-wise error rate at α = 0.05:
- p̃₍ᵢ₎ = max_{j ≤ i} min{1, (m − j + 1) p₍ⱼ₎}
- Holm is valid under arbitrary dependence between the tests. That matters here because all 12 tests share the same 20 systems and the same paths.
- Decisions use unrounded values. `holm_summary.json` stores full float precision; the tables below are rounded for reading only.

**Robustness (descriptive).** The exact two-sided sign test of the replicate signs (zeros excluded), Holm-adjusted over the same family.
- It tests whether positive and negative replicate effects are balanced (median zero). That is **a different null hypothesis** from the mean-zero t test.
- A disagreement between the two is information about the shape of the replicate distribution. It is not, by itself, evidence that the t test is invalid.

## 2. Results

**Table P2.** *Supplementary post hoc multiplicity analysis of the 12 pre-specified primary contrasts (λ = 0.1, R = 20 independently fitted systems, two-sided t₁₉ tests, Holm step-down at FWER 0.05).* The estimates and CIs are the unadjusted primary results, unchanged.
- RMD is in trading days; a negative RMD contrast means RF detects faster.
- X(20) is the baseline-adjusted excess probability of detection within 20 days; a positive X(20) contrast favours RF.

| Contrast | δ | Estimate | Unadjusted 95% t₁₉ CI | s_b | t₁₉ | Raw p | Holm rank | Holm p | Reject at FWER 0.05 | Signs +/− | Sign p (raw / Holm) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RF − GARCH, RMD₅₀₀ | 1.5 | −6.05 | [−10.47, −1.63] | 9.45 | −2.866 | 0.00989 | 8 | 0.0533 | no | 6/14 | 0.115 / 0.577 |
| RF − GARCH, RMD₅₀₀ | 2 | −9.94 | [−17.08, −2.80] | 15.3 | −2.915 | 0.00888 | 7 | 0.0533 | no | 5/15 | 0.0414 / 0.248 |
| RF − GARCH, RMD₅₀₀ | 3 | −13.13 | [−22.88, −3.39] | 20.8 | −2.822 | 0.0109 | 9 | 0.0533 | no | 6/14 | 0.115 / 0.577 |
| RF − GARCH, X(20) | 1.5 | +0.0009 | [−0.0021, +0.0039] | 0.00633 | +0.626 | 0.538 | 11 | 1 | no | 10/10 | 1 / 1 |
| RF − GARCH, X(20) | 2 | +0.0013 | [−0.0027, +0.0054] | 0.00862 | +0.686 | 0.501 | 10 | 1 | no | 12/8 | 0.503 / 1 |
| RF − GARCH, X(20) | 3 | −0.0005 | [−0.0092, +0.0081] | 0.0185 | −0.131 | 0.897 | 12 | 1 | no | 13/7 | 0.263 / 0.790 |
| RF − conventional, RMD₅₀₀ | 1.5 | +37.54 | [+32.96, +42.11] | 9.78 | +17.167 | 5.01 × 10⁻¹³ | 1 | 6.02 × 10⁻¹² | yes | 20/0 | 1.91 × 10⁻⁶ / 2.29 × 10⁻⁵ |
| RF − conventional, RMD₅₀₀ | 2 | +60.40 | [+52.96, +67.84] | 15.9 | +16.991 | 6.03 × 10⁻¹³ | 2 | 6.64 × 10⁻¹² | yes | 20/0 | 1.91 × 10⁻⁶ / 2.29 × 10⁻⁵ |
| RF − conventional, RMD₅₀₀ | 3 | +63.63 | [+53.01, +74.25] | 22.7 | +12.536 | 1.23 × 10⁻¹⁰ | 5 | 9.87 × 10⁻¹⁰ | yes | 20/0 | 1.91 × 10⁻⁶ / 2.29 × 10⁻⁵ |
| RF − conventional, X(20) | 1.5 | −0.0081 | [−0.0110, −0.0052] | 0.00621 | −5.822 | 1.31 × 10⁻⁵ | 6 | 9.20 × 10⁻⁵ | yes | 1/18 | 7.63 × 10⁻⁵ / 5.34 × 10⁻⁴ |
| RF − conventional, X(20) | 2 | −0.0251 | [−0.0290, −0.0212] | 0.00837 | −13.436 | 3.76 × 10⁻¹¹ | 4 | 3.38 × 10⁻¹⁰ | yes | 0/20 | 1.91 × 10⁻⁶ / 2.29 × 10⁻⁵ |
| RF − conventional, X(20) | 3 | −0.0608 | [−0.0693, −0.0524] | 0.0181 | −15.029 | 5.32 × 10⁻¹² | 3 | 5.32 × 10⁻¹¹ | yes | 0/20 | 1.91 × 10⁻⁶ / 2.29 × 10⁻⁵ |
| *Context, not in family:* RF − GARCH, RMD₅₀₀ | 1 | +0.27 | [−1.24, +1.79] | 3.24 | +0.378 | 0.710 | – | – | – | 9/11 | 0.824 |
| *Context, not in family:* RF − conventional, RMD₅₀₀ | 1 | −3.80 | [−6.53, −1.07] | 5.84 | −2.913 | 0.00893 | – | – | – | 5/15 | 0.0414 |

The δ = 1 X(20) baselines are 0 in all 20 replicates by construction, so they have no test.

**Summary.**
- **6 of 12** hypotheses are rejected at FWER 0.05 under Holm: all six RF − conventional contrasts. The sign-test Holm check rejects the same six.
- No RF − GARCH contrast is rejected. RF − GARCH RMD₅₀₀ has unadjusted p of 0.0089–0.0109, and its CIs exclude 0. Its Holm-adjusted p is **0.05327** (unrounded 0.053269536812497534) for all three δ, just above 0.05.

**How Holm produces this.**
- The six RF − conventional tests take ranks 1–6. The first RF − GARCH RMD test (δ = 2) is rank 7, with p̃ = 6 × 0.008878 = 0.05327 > 0.05.
- The procedure stops at the first non-rejection. Ranks 8 and 9 inherit 0.05327 through the cumulative maximum, even though their own products (5 × 0.009895 = 0.0495 and 4 × 0.010896 = 0.0436) are below 0.05.
- The result is therefore borderline, not clear-cut. It is reported as computed, with the family, α and the method as fixed in advance.

## 3. Interpretation for the report

1. **RF − conventional.** After a family-wise adjustment over all 12 primary contrasts, the evidence remains very strong that conventional EWMA detects the evaluated persistent variance increases faster than RF–EWMA, as a mean over fitted systems in this design.
   - The RMD contrasts are +37.5 to +63.6 days.
   - The X(20) contrasts are −0.008 to −0.061.
   - Every system shares the sign of the mean (20/0 and 0/20), except one of 19 non-zero systems for X(20) at δ = 1.5.
   - The t test and the sign test agree.
2. **RF − GARCH, restricted mean delay.** The unadjusted primary analysis gives a mean RF advantage of 6–13 days, with CIs excluding 0. That advantage **does not survive Holm control of the FWER at 0.05**: adjusted p = 0.053 at each δ.
   - The sign tests are weaker (raw p 0.115 / 0.041 / 0.115; Holm 0.58 / 0.25 / 0.58). Only 14–15 of 20 fitted systems favour RF.
   - The appropriate statement: there is some evidence of a mean RF advantage over GARCH in restricted delay, but it is **not robust to multiplicity adjustment**, and it is **not consistent across fitted systems**.
3. **RF − GARCH, X(20).** There is no evidence of a difference in early (≤ 20-day) baseline-adjusted detection, with or without adjustment (Holm p = 1).
4. **Between-system heterogeneity.**
   - The test unit is the fitted system. s_b therefore contains the variability from training sample, model selection, forest randomness and calibration, as well as the within-replicate Monte Carlo error. The p-values concern the **mean over systems**.
   - For RF − GARCH RMD, s_b (9.4–20.8 days) is 3–8 times the Monte Carlo SE (about 2.7). A practitioner who fits a single system can see an advantage for either method; 5–6 of 20 systems favoured GARCH.
   - The sources of this heterogeneity are P4's subject. Nothing here is tuned on it.
5. **t-test assumptions.**
   - With R = 20 the t₁₉ test relies on approximate normality, or the central-limit behaviour, of the replicate estimates. That cannot be checked well, and no formal normality test was added.
   - The sign test answers a different question: the balance of signs, not the mean. For RF − GARCH RMD the two differ. The t test sees a mean shifted from 0 relative to s_b. The sign test sees a 14:6 or 15:5 split, which is unremarkable at this R.
   - Read together, the evidence is distributionally fragile, which makes the borderline Holm result appropriately cautious. Neither test is taken to invalidate the other.
6. **Survivor conditioning.**
   - Every contrast is conditional on the paths with no pre-change alarm for either chart (E_a ∩ E_b), so the tests concern that conditional estimand.
   - Because equal ARL₀ does not equalize pre-change false alarms (conventional 0.125 against RF 0.102 and GARCH 0.094), the RF − conventional RMD contrast is already −3.80 days at δ = 1 (raw p 0.009; context only).
   - For RF − conventional RMD, H₀ "θ = 0" is therefore not a "no change effect" null. The δ > 1 contrasts are of opposite sign and 10–17 times larger in magnitude, so this does not affect the conclusion.
   - The X(20) contrasts are baseline-adjusted by construction. No baseline-subtracted RMD test was added; it would be a new, non-pre-specified estimand.
7. **Unchanged caveats.**
   - RMD is a restricted mean (censoring at H = 500), not ARL₁.
   - The GARCH-generated DGP favours the GARCH forecaster.
   - IC calibration is conditional on each h*.
   - Holm-compatible simultaneous intervals are not given; only the unadjusted CIs are reported.
   - Significance is not causal evidence for the adaptation-masking explanation.

**Suggested article wording (Results §4.2):** "As a supplementary, post hoc check, decided after the primary results were seen, we applied Holm's step-down procedure to two-sided t₁₉ tests of the 12 primary contrasts. All six RF − conventional contrasts remained significant at a family-wise level of 0.05 (adjusted p ≤ 9.2 × 10⁻⁵), but none of the RF − GARCH contrasts did. The RF advantage in restricted mean delay over GARCH had adjusted p = 0.053 at each δ, and only 14–15 of the 20 fitted systems favoured RF. The unadjusted estimates and intervals in Table X remain the pre-registered primary results."

## 4. Verification

**Checks: 90/90 passed.**
- Input hash and the P1 verdict.
- For each of the 14 rows:
  - R = 20 finite values
  - stored mean and CI exactly equal to the P1-audited values
  - t and p equal to `scipy.stats.ttest_1samp`
  - recomputed mean, s_b and CI equal to the stored values (to 10⁻¹⁰)
  - CI–test duality
  - sign counts and exact sign p equal to the stored values
- Hand Holm equal to `statsmodels.multipletests(method="holm")` to 10⁻¹², for both the t-test and the sign-test p-values, with identical reject decisions.
- Adjusted p ≥ raw p and non-decreasing in rank.
- No `run` or `src` module imported.

**Self-test (hand-computed):**
- Holm on (0.01, 0.04, 0.03, 0.005) gives (0.03, 0.06, 0.06, 0.02), with ranks (2, 4, 3, 1).
- The cap at 1.
- t = √15 for (1, 2, 3, 4).
- Exact sign-test values: p(6, 14) = 120920/2²⁰.

Four deliberate mutations were each caught: no cumulative maximum, an off-by-one multiplier, a one-sided p and ddof = 0.

**Integrity.** All 17 production files are unchanged after the run, and `.venv/bin/python -m pytest -q` reports 80 passed.

## 5. Reproduction

```bash
.venv/bin/python -I scripts/p2_holm.py --selftest
mv results/derived/p2_holm results/derived/p2_holm.prev   # the script refuses to overwrite
.venv/bin/python -I scripts/p2_holm.py                    # exit 0 iff all checks pass
```

**Outputs** in `results/derived/p2_holm/`:
- `holm_summary.json`: full precision, label, target, family, rows and checks
- `holm_table.md`: rounded, for reading
- `p2_log.txt`
- `p2_provenance.txt`: time, HEAD, versions, script and input hashes
