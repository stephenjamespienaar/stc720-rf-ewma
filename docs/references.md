# References and Evidence Status

*Version 1.0, 13 Oct 2026. Zotero collection: `STC-720-lib` (key K7HN6JFW), 10 items, no duplicates (checked 13 Oct 2026). DOIs and bibliographic fields were checked against Crossref.*

## Evidence-status codes

| Code | Meaning | What may be claimed |
|---|---|---|
| **FT** | Full text read (Zotero MCP text extraction) | Content, equations (subject to extraction notes), results |
| **FT-img** | Scanned PDF without a text layer, read from rendered page images | Content, equations and results as read from the page images |
| **FT-pre** | Full text of a **preprint** version read; published version not inspected | Content; quote page numbers only after checking the published version |
| **MD** | Metadata/abstract-level verification only; full text **not** read | Existence and topic at title level only. **No** equations, numerical results or detailed methodological conclusions |

---

## Foundation papers (original collection)

**[1] Roberts, S. W. (1959).** Control chart tests based on geometric moving averages. *Technometrics*, 1(3), 239–250. https://doi.org/10.1080/00401706.1959.10489860 — Zotero `S3A6LVHU`

- **Status:** FT.
- **Version note.** The attached PDF is the *Technometrics* 2000 reprint (42(1), 97–101). Cite the 1959 original; page-specific quotes must be checked against the 1959 pagination.
- **Used for:**
  - the EWMA recursion $Z_0=\mu_0,\ Z_j=(1-r)Z_{j-1}+rx_j$ (eq. 1)
  - the iid-normal standard deviation of $Z_j$ (eqs. 4–5)
  - the recommendation to compare tests at a common Type I error level ("more useful comparisons could be made if the limit lines were set so that the tests had a common level of Type 1 errors")
- **Extraction note.** Eqs. 1–5 are garbled in the text layer. The forms used are a **reconstruction**, consistent with the standard EWMA and with Dumičić & Žmuk (2015) eq. 3. The ARL figures are not extractable.

**[2] Alwan, L. C., & Roberts, H. V. (1988).** Time-series modeling for statistical process control. *Journal of Business & Economic Statistics*, 6(1), 87–95. https://doi.org/10.1080/07350015.1988.10509640 — Zotero `M7G7QD2C`

- **Status:** FT.
- **Used for:**
  - the residual ("special-cause") chart paradigm: fit a time-series model and chart one-step prediction errors, with limits based on one-step forecast standard errors
  - the common-cause chart of fitted values
  - their remark that monthly DJIA log-differences are close to iid normal
- **Scope note.** They address the **mean**. Applying the idea to the variance is this study's extension.

**[3] Bollerslev, T. (1986).** Generalized autoregressive conditional heteroskedasticity. *Journal of Econometrics*, 31(3), 307–327. https://doi.org/10.1016/0304-4076(86)90063-1 — Zotero `79MXQ32R`

- **Status:** FT.
- **Used for:**
  - GARCH(p,q) definition (eqs. 1–2) and GARCH(1,1) (eq. 8)
  - Thm 1: wide-sense stationarity iff $\sum\alpha_i+\sum\beta_i<1$, with $\operatorname{var}=\alpha_0/(1-A(1)-B(1))$
  - Thm 2, $m=2$: 4th-moment condition $3\alpha_1^2+2\alpha_1\beta_1+\beta_1^2<1$ under normality
  - the ARMA representation of $\epsilon_t^2$ with a serially uncorrelated $v_t=\epsilon_t^2-h_t$ (eqs. 6–7)
  - the QML conditions $E(\epsilon_t^2h_t^{-1}\mid\psi_{t-1})=1$ (eq. 25)
  - ACF diagnostics of $\epsilon_t^2h_t^{-1}$ (§4, §7)
  - the $100\ln$ return convention (§7)
- **Extraction note.** Eqs. 2, 4–5, 9–11, the kurtosis expression and 18–24 are garbled. The kurtosis formula and moment recursion are **reconstructed** from standard results. The Student-t generalization of the 4th-moment condition is derived in `methodology.md` eq. 5, not taken from this paper.

**[4] Breiman, L. (2001).** Random forests. *Machine Learning*, 45(1), 5–32. https://doi.org/10.1023/A:1010933404324 — Zotero `8IBZX7F6`

- **Status:** FT.
- **Used for:**
  - the regression forest as an average of trees (§11)
  - Thm 11.1 (a.s. convergence of MSE as the number of trees → ∞)
  - Thm 11.2 ($PE^*(\text{forest})\le\bar\rho\,PE^*(\text{tree})$)
- **Caveats to state.**
  - §11 assumes training data drawn **independently**, which does not hold for time series. Out-of-bag error is therefore not used.
  - Breiman's regression experiments use random linear combinations of inputs (Forest-RC). scikit-learn's `RandomForestRegressor` uses random input selection plus bootstrap, and is described as such.
- **Extraction note.** Θ symbols are dropped ("h(x, k)" should read $h(x,\Theta_k)$).

**[5] Dumičić, K., & Žmuk, B. (2015).** Statistical control charts: Performances of short term stock trading in Croatia. *Business Systems Research Journal*, 6(1), 22–35. https://doi.org/10.1515/bsrj-2015-0002 — Zotero `5VI85G6N`

- **Status:** FT.
- **Used for (cautionary precedent).** I, MR, EWMA (λ = 0.30) and CUSUM charts were applied to CROBEX10 **price levels** for 2012. They report too many signals, mostly regarded as false alarms. Prices are non-normal with lag-1 autocorrelation ≈ 0.93–0.99 (Table 6), and there is no ARL evaluation.
- **Our interpretation (labelled as such).** The failure is consistent with charting a non-stationary level with iid-normal limits, as Alwan & Roberts (1988) warn.
- **Extraction note.** Eqs. 1–4 are severely garbled. The EWMA limit form is a **reconstruction**.

## Additional papers (approved 13 Oct 2026, added to Zotero by the student)

**[6] Schipper, S., & Schmid, W. (2001).** Control charts for GARCH processes. *Nonlinear Analysis: Theory, Methods & Applications*, 47(3), 2049–2060. https://doi.org/10.1016/S0362-546X(01)00332-7 — Zotero `FIXUEAWI`

- **Status:** FT-img. The PDF is a scan with no text layer, so Zotero's full-text index returns 404. All 12 pages were read from rendered images on 13 Oct 2026.
- **Content verified:**
  - Target process: GARCH, eqs. 1–2.
  - Observed process, eq. 3: $X_t=Y_t$ for $t<\tau$; $\mu_0+\Delta(Y_\tau-\mu_0)+a\sqrt{\gamma_0}$ at $t=\tau$; $\mu_0+\Delta(Y_t-\mu_0)$ for $t>\tau$. Here Δ is a scale change and $a$ an additive outlier.
  - $\hat\sigma_t^2$ is the best linear predictor of $X_t^2$ computed under in-control parameters assumed **known**.
  - Simultaneous mean and variance EWMA schemes, with variance charts based on:
    - squared observations (§3.1)
    - conditional variance (§3.2)
    - RiskMetrics exponentially weighted variance with λ = 0.06 (§3.3)
    - log squared observations (§3.4)
    - residuals $(X_t-\mu_0)^2/\hat\sigma_t^2$ with $Z_{2,0}=1$ (§3.5)
  - Monte Carlo setup (§4): in-control ARL 60; τ = 1; GARCH(1,1) with $\alpha_0=0.1,\alpha_1=0.05,\beta_1=0.9$ ($\gamma_0=2$); normal innovations; 100,000 replications; minimum out-of-control ARL over a λ grid per chart.
  - Finding (p. 2057): *"In nearly all cases the residual chart with λ₂ = 0.1 turns out to be the best chart. Only if Δ is close to 1 other charts have a slightly smaller out-of-control ARL."*
- **Used for:**
  - the fault model (our eq. 6)
  - the conventional and GARCH–EWMA benchmarks as established charts
  - prior evidence for H4
  - their stated reason for choosing λ per chart ("it is not correct to compare the charts for the same smoothing parameters"). Our design differs: λ is pre-registered and the full grid is reported.

**[7] MacGregor, J. F., & Harris, T. J. (1993).** The exponentially weighted moving variance. *Journal of Quality Technology*, 25(2), 106–118. https://doi.org/10.1080/00224065.1993.11979433 — Zotero `FR3PG7SM`

- **Status: MD only.** No PDF; the student could not obtain one through UP institutional access.
- **May be claimed.** The paper exists and, by its title, concerns an exponentially weighted moving variance for monitoring. Schipper & Schmid (2001, ref. [3]) cite it among control-chart methods for dependent processes.
- **Must not be claimed.** Its equations, ARL results, recommended parameters or detailed conclusions.

**[8] Patton, A. J. (2011).** Volatility forecast comparison using imperfect volatility proxies. *Journal of Econometrics*, 160(1), 246–256. https://doi.org/10.1016/j.jeconom.2010.03.034 — Zotero `X6MRG2UH`

- **Status:** FT.
- **Used for:**
  - The squared return (zero mean) as a conditionally unbiased volatility proxy (§1).
  - MSE $L(\hat\sigma^2,h)=(\hat\sigma^2-h)^2$ (eq. 5) and QLIKE $L=\log h+\hat\sigma^2/h$ (eq. 6), where $\hat\sigma^2$ is the **proxy** and $h$ the **forecast** in Patton's notation.
  - Prop. 1: robust loss functions are exactly the form of eq. 23, and MSE and QLIKE belong to this class (Remark 2).
  - Table 1: both MSE and QLIKE are minimised by $\sigma_t^2$ under normal and Student-t returns.

**[9] Christensen, K., Siggaard, M., & Veliyev, B. (2023).** A machine learning approach to volatility forecasting. *Journal of Financial Econometrics*, 21(5), 1680–1727. https://doi.org/10.1093/jjfinec/nbac020 — Zotero `SA4UZ9NE`

- **Status:** FT-pre. The attached PDF is the arXiv version (arXiv:2601.13014v1, draft dated May 2022), not the typeset journal article. Cite the published version and check any page-specific quote against it.
- **Used for:**
  - ML (regularization, bagging, random forest, gradient boosting, neural networks) is competitive with the HAR family for forecasting **realized variance** of DJIA constituents. This holds even with only daily, weekly and monthly lags, and they note similar findings for SPY.
  - HAR feature structure $RV_{t-1},RV_{t-1|t-5},RV_{t-1|t-22}$ (eq. 5).
  - RF settings: 500 trees, min. node size 5, feature split $J/3$ (Table 15).
  - Chronological train/validation/test split, with no k-fold CV because it "violates the time-series structure".
  - iid bootstrap retained.
- **Caveat.** Their target is intraday realized variance, much less noisy than daily $r^2$, so their accuracy findings may not transfer.

**[10] Lu, C.-W., & Reynolds, M. R. (1999).** EWMA control charts for monitoring the mean of autocorrelated processes. *Journal of Quality Technology*, 31(2), 166–188. https://doi.org/10.1080/00224065.1999.11979913 — Zotero `AYZH39D9`

- **Status: MD only.** No PDF; not obtainable through UP access.
- **May be claimed.** EWMA charts for monitoring the mean of autocorrelated processes have been studied (title level).
- **Must not be claimed.** Any statement about residual-based versus observation-based charts, ARL values or recommendations.

## Variance-targeting references (SPY post-stop refinement, 27 Oct 2026)

These are **not in the Zotero library**, and their full texts **have not been reviewed**. The bibliographic details below were verified independently by the student on 27 Oct 2026 and located by web search (IDEAS/RePEc; MPRA). Status: **bibliographic only** (weaker than MD: no abstract was read through Zotero).

**[11] Francq, C., Horváth, L., & Zakoïan, J.-M. (2011).** Merits and drawbacks of variance targeting in GARCH models. *Journal of Financial Econometrics*, 9(4), 619–656. https://doi.org/10.1093/jjfinec/nbr004

- **Role.** The main theoretical reference for variance targeting in the SPY application.
- **May be claimed.** Variance targeting reparameterizes the GARCH model so that the unconditional variance is set equal to a first-step sample estimate, with the remaining parameters estimated in a second step. The paper studies the method's statistical properties (title and bibliographic level; consistent with the publisher's and RePEc abstracts as seen in search results).
- **Must not be claimed.** Any specific theorem, asymptotic condition (such as moment requirements), numerical result or recommendation, until the full text has been read.

**[12] Engle, R. F., & Mezrich, J. (1996).** GARCH for groups. *Risk*, 9(8), 36–40.

- **Role.** The conventional attribution of variance targeting, cited only as the origin of the term and method.
- **Must not be claimed.** Any content of the article; it has not been seen.

## Library items not cited (for reference)

- Montgomery, D. C., & Mastrangelo, C. M. (1991). Some statistical process control methods for autocorrelated data. *JQT*, 23(3), 179–193. https://doi.org/10.1080/00224065.1991.11979321. In the library (`JJZE5AS3`) but outside the collection, with no PDF (MD only).

## Software (to be cited in the report)

- Python 3.14.4; NumPy 2.5.4; pandas 3.0.6; SciPy 1.18.1; scikit-learn 1.9.1; arch 8.0.0; Matplotlib 3.11.2; yfinance 1.7.0 (versions from `requirements-lock.txt`).
