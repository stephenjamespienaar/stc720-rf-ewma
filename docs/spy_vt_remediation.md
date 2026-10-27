# SPY calibration remediation: variance-targeted GARCH-t (training data only)

*27 Oct 2026. Post-stop methodological refinement, authorized by the user as training-only estimation and synthetic testing. No SPY re-download, no monitoring returns, no charts, no calibration, no simulation of SPY paths. The stopped run, the snapshot and all historical artifacts are unchanged.*

## 1. Why the SPY run stopped

Run `results/runs/spy_20261027T045319_117125/` (results hash `b0e2ade1…`; snapshot `data/raw/SPY.csv` `7cd6d400b798c5e7…`) stopped at the strict fourth-moment gate (exit 3), as designed.

- **The fit.** The unrestricted training GARCH(1,1)-t had α + β = 0.9976 and fourth-moment coefficient β² + 2αβ + κα² = 1.0089. That exceeds the simulator's margin of 0.99, and also 1, so E r⁴ = ∞ under the fit.
- **The level mismatch.** The implied unconditional variance was 1.920, against a training s² of 1.144. Calibration paths simulated from that fit would run at about 1.68 times the data's variance level, which would distort the conventional chart's limit.

## 2. Method: variance targeting (post-stop refinement)

- **Restriction.** ω = s²(1 − α − β), where s² is the mean squared demeaned training return (1993-02-01 to 2006-12-29 only). The model's unconditional variance therefore equals s² exactly.
- **Estimation.** α, β and ν are estimated by maximum likelihood under the standardized Student-t of eqs. 2–4 (unit variance, as in `sim.std_t`), with h₁ = s². The likelihood is `forecast.garch_t_nll` and the estimator `forecast.fit_garch_vt`.
- **Parameterization.** persistence = expit(x₀), α = persistence · expit(x₁), β = persistence − α, ν = 2 + exp(x₂). So α, β ≥ 0, α + β < 1 and ν > 2 hold by construction. Nothing is clipped, and no fourth-moment bound is imposed.
- **Optimization.** BFGS from 12 fixed starts, on the mean negative log-likelihood per observation, so the gradient tolerance does not scale with n. The best optimum is kept and agreement across starts is recorded. A fit is refused, with an explicit error, if the optimizer does not converge or the result is inadmissible.
- **Why a new likelihood was needed.** `arch` 8.0.0 has no variance-targeting GARCH and cannot tie ω to (α, β). The new code is about 60 lines and is tested against SciPy's t density. The unrestricted `fit_garch` and every production default are unchanged.
- **Selection.** The estimator is used only through `run.SPY["garch_estimator"] = "variance_targeted"`. All other configs, and the `application.fit` default, use the unrestricted fit (tested).
- **Literature.** Variance targeting is usually credited to Engle & Mezrich (1996, *Risk* 9(8), 36–40). Its asymptotics and its merits and drawbacks are studied by Francq, Horváth & Zakoïan (2011, *Journal of Financial Econometrics* 9(4), 619–656). **Neither is in the Zotero library, and neither has been inspected.** Their bibliographic details were located by web search ([IDEAS](https://ideas.repec.org/a/oup/jfinec/v9y2011i4p619-656.html), [MPRA working paper](https://mpra.ub.uni-muenchen.de/15143/)). Adding and checking them needs the user's permission (CLAUDE.md §5). Until then the report must not attribute any result to them.

## 3. Training-only comparison

`scripts/spy_vt_review.py` → `results/derived/spy_vt_review/` (`vt_review.json` `0f1fad16…`, `vt_review.md`, `provenance.txt`). The snapshot is sliced to prices up to 2006-12-29 before any return is formed.

**Specifications compared:**
- **A:** the stopped run's unrestricted `arch` fit, with backcast start.
- **A′:** the unrestricted fit under the project likelihood and h₁ = s². This is a like-for-like likelihood reference only, not a candidate.
- **B:** the variance-targeted fit.

| | A (unrestricted, `arch`) | A′ (unrestricted, same likelihood) | B (variance-targeted) |
|---|---|---|---|
| ω / α / β / ν | 0.00457 / 0.0599 / 0.9377 / 7.35 | 0.00477 / 0.0617 / 0.9358 / 7.36 | 0.00513 / 0.0593 / 0.9363 / 7.63 |
| α + β | 0.9976 | 0.9975 | 0.9955 |
| Implied variance / training s² | 1.920 / 1.144 (×1.68) | 1.904 / 1.144 (×1.66) | **1.144 / 1.144 (×1.00)** |
| Fourth-moment coefficient (κ) | 1.0089 (4.79) | 1.0094 (4.78) | **1.0039** (4.65) |
| Finite variance / finite E r⁴ / strict gate | yes / no / no | yes / no / no | yes / **no** / **no** |
| Half-life (days) | 291 | 276 | 154 |
| Log-likelihood (h₁ = s²) | −4626.61 | −4626.59 | −4626.83 |
| Training mean ĥ / mean u / QLIKE | 1.178 / 0.993 / 0.8344 | 1.178 / 0.995 / 0.8343 | 1.148 / 1.014 / 0.8344 |
| ACF₁ of u / excess kurtosis of r/√ĥ | −0.007 / 1.57 | −0.008 / 1.57 | −0.007 / 1.57 |

**Findings:**
- **The level is not identified by these data.**
  - Restricting the unconditional variance from 1.90 to 1.14 costs 0.24 log-likelihood units: twice the difference (A′ − B) is 0.47. This is descriptive only; s² is estimated, so the χ²₁ reference is approximate.
  - The training sample contains three variance regimes, with mean r² of 0.95 (1993–99), 2.01 (2000–03) and 0.44 (2004–06). With persistence near 1, the likelihood is almost flat in the level direction.
- **Training conditional variances are practically identical:** corr(ĥ_A, ĥ_B) = 1.0000, mean ĥ_A/ĥ_B = 1.021, and the 2006-12-29 state is 0.277 under both. In monitoring, the GARCH chart's denominator would differ little between A and B. **The choice matters mainly for the stationary level of simulated calibration paths.**
- **Optimizer reliability, B:** all 12 starts converged, all at the same optimum. The maximum parameter spread is 4.8 × 10⁻⁴, the objective range 2 × 10⁻⁷, and the gradient norm 1.6 × 10⁻⁷. A′ also converged.
- **A reproducibility finding.** `arch`'s unrestricted fit reproduces the stopped run bit-for-bit only with single-threaded BLAS, as the wrapper sets. With multi-threaded BLAS it differs at about 10⁻⁵ relative. The targeted fit is bit-identical under both settings. The review was run with the wrapper's thread settings.
- **The fourth moment.** **B still fails it:** E r⁴ = ∞ under the fitted law, although E r² is finite and κ = E η⁴ is finite (ν > 4).

## 4. Can finite-variance GARCH-t simulation be used for first-alarm calibration under B?

- **Moments.**
  - Under B, E r² = s² is finite and E r⁴ = ∞.
  - On simulated paths, the GARCH chart's score is u ≈ η²: iid after the filter's start-up error decays, with finite mean and variance, since ν > 4.
  - The conventional score (r²/s²) and the RF score (r² over a bounded forecast) have finite mean but **infinite variance**.
- **Are first-alarm run lengths well defined?**
  - α + β < 1 implies E log(β + αη²) ≤ log(α + β) < 0 (Jensen), so the process is strictly stationary [D]. The EWMA of a non-negative, stationary score with finite mean exceeds any h with positive probability.
  - T = inf{t : Z_t > h} is a stopping time. The **restricted** run length min(T, 5000) used in eqs. 15–16 is bounded, so its mean and variance always exist.
  - **The calibration target therefore needs no fourth moment of returns.** Whether E T < ∞ (unrestricted) holds rests on ergodicity results for GARCH(1,1) that are standard but not in the project library; that point is not needed, because only restricted run lengths are used.
- **Finite-horizon Monte Carlo stability.**
  - Because min(T, 5000) is bounded, the validation SE and the normal CI are well founded (conditional on h*).
  - The burn-in condition holds easily: 0.9955²⁰⁰⁰ ≈ 1.2 × 10⁻⁴.
  - Paths of 5,000 days span about 32 half-lives.
  - The remaining risk is numerical: extreme variance excursions. Finiteness is checked.
- **Precision of validation.** High persistence makes run lengths over-dispersed (CV > 1, as with the conventional chart in P5), which widens CIs. For example, CV 1.2 at N = 2,000 gives a 95% half-width of about 26 (about 5%). Eq. 29 can still be met unless the calibration is biased by a few percent.
- **Stability of h*.** It can be checked without extra paths, by splitting the 2,000 calibration paths into halves (proposed below).
- **Residual limitations:**
  - Infinite-variance scores for the conventional and RF charts make their run lengths sensitive to rare extreme returns.
  - The calibration model is a GARCH-t, which favours the GARCH chart: its score is near-iid under the model.
  - The calibration model is fitted to 1993–2006 and cannot represent later regime changes.

**Assessment.** Finite-variance-only simulation under B is mathematically adequate for restricted first-alarm ARL calibration and for its independent validation. The infinite fourth moment does **not** invalidate the run-length estimand; it affects precision and tail sensitivity, which the diagnostics below quantify. The production simulator's 0.99 margin stays the default. SPY calibration would need an explicit, narrowly scoped opt-in (`need_m4=False`, still requiring ω > 0, α, β ≥ 0, α + β < 1 and ν > 2), which is **not yet implemented**.

**Calibration diagnostics and failure criteria, proposed before any calibration:**

| # | Diagnostic | Criterion | On failure |
|---|---|---|---|
| a | Admissibility of the targeted fit | ω > 0, α, β ≥ 0, α + β < 1, ν > 2 (B also has ν > 4) | Stop |
| b | Burn-in memory | (α + β)^burn ≤ 10⁻³ (B: 1.2 × 10⁻⁴ at 2,000) | Stop |
| c | Numerical | All simulated r, h, d, u finite; record max h and max u | Stop |
| d | Calibration censoring | ≤ 1% of calibration paths without an alarm by 5,000 days, per chart and λ (methodology §6) | Stop before monitoring |
| e | Bisection | Calibrated ARL within 10⁻³ relative of 500 | Stop |
| f | Split-half stability | The ARL of each half of the calibration paths at the full-sample h* lies in [425, 575] | Report prominently; no nominal-ARL₀ claim for that chart |
| g | Independent validation | Eq. 29 on 2,000 independent paths | Report and keep; no recalibration (production policy) |
| h | Precision | Validation SE / ARL ≤ 0.04 | Flag |
| i | Tail descriptives | Run-length CV and quantiles of u on validation paths | Report |

Diagnostics c, d, f and i are not yet computed by the pipeline. Items c, d and e partly exist (the finite-score check, the stored censoring fraction and the bisection result); f needs a small addition. All would be implemented and tested before a relaunch.

**If any stop criterion fails,** the defensible alternative is a calibration model that does not rest on the GARCH-t law: for example, a block bootstrap of training returns. That would need a separate decision and a reference.

## 5. Tests and checks

- `pytest -q`: **109 passed** (101 + 8 new, in `tests/test_spy.py`). The new tests cover:
  - the likelihood against an explicit loop with SciPy's t density (rel. 10⁻¹⁰)
  - the targeting identity and admissibility, and recovery of the production DGP from 20,000 simulated observations, with agreement across starts
  - admissibility on near-integrated data with E r⁴ = ∞ (a test-only simulator; the production simulator correctly refuses that law)
  - an explicit refusal on unidentified iid-normal data
  - deterministic fits
  - the distinction between finite second and fourth moments (`sim.moments`)
  - estimator selection only by the SPY config, with the default unchanged
  - the targeted fit being unchanged by post-2006 price changes, inside the pipeline
- **Mutation checks**, each caught: a wrong recursion start, a wrong fourth-moment threshold, a wrong default estimator. Earlier SPY mutations still apply.
- **Review checks (7/7):**
  - training prices end on 2006-12-29
  - n = 3,507
  - the mean and s² equal the stopped run's
  - the unrestricted fit reproduces the stopped run exactly (single-threaded)
  - B targets s² exactly
  - B's optimum agrees across starts
- **Integrity:** production 17/17 unchanged; snapshot hash unchanged; stopped run unchanged.

## 6. Decision and implementation (27 Oct 2026, after this review)

- **Approved.** The user approved **model B** as the fixed SPY specification, using the stored full-precision training fit, and authorized the finite-variance simulation option. **No calibration or relaunch is authorized.**
- **Implemented:**
  - `sim.simulate(..., need_m4=False)`: an explicit opt-in, finite variance only, with no clipping and a non-finite-value check.
  - `application.limits`, extended with restricted-run-length, split-half, precision and tail outputs.
  - `application.diagnose`, for criteria c–h.
  - The pipeline gate in finite-variance mode: criteria a and b, then the limits, then c–h; the run stops before monitoring on any stop criterion.
  - `run.SPY["finite_variance_simulation"]` and `run.SPY["diagnostics"]`.
- **References:** recorded in `references.md` as bibliographic only.
- **Tests:** 126 passed, 17 of them new for this step. Production defaults are confirmed bit-identical to the committed simulator.
- **Criterion e (resolved):** Criterion e refined (user decision, 27 Oct 2026, **before any SPY calibration**). These remain **hard stops**: a non-finite or non-positive h*, a failed minimality condition (restricted ARL(h*) ≥ 500 > restricted ARL(h*(1 − 10⁻⁶))), an inconsistent restricted-mean computation, and failed bracketing or bisection (`CalibrationError`). Only the overshoot |restricted ARL(h*)/500 − 1| > 10⁻³ became a **recorded warning** (`e_overshoot`), keeping the exact overshoot, achieved restricted ARL, target deviation and status in `results.json`. Justification: in the frozen production run, 24 of 160 calibrations exceeded 10⁻³ (maximum 0.16%) through the discreteness of the empirical ARL. There is no recalibration, no seed change and no selective rerun, and validation is unchanged. Tests: 133 passed.

## 7. Original recommendation (before the decision)

1. **Adopt B (variance-targeted GARCH-t) as the SPY GARCH specification**, for both the GARCH chart and the calibration model. It removes the 1.68× level mismatch at negligible likelihood cost, and leaves the training conditional variances practically unchanged. The choice rests on fit and identification evidence from training data only, not on any detection outcome.
2. **A finite-variance calibration option is necessary**, because B also fails the fourth-moment condition. Implement the narrowly scoped `need_m4=False` opt-in for SPY calibration only, with diagnostics a–i, regression tests showing the production defaults unchanged, and disclosure of the infinite fourth moment and of the GARCH home advantage.
3. **Add Francq, Horváth & Zakoïan (2011)**, and optionally Engle & Mezrich (1996), to Zotero before citing them.
4. **Then relaunch once** into a new run directory, reusing the frozen snapshot with no re-download.
