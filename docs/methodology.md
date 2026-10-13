# Methodology — RF–EWMA Monitoring of Financial Volatility

*Version 1.1, 14 Oct 2026 (v1.0: 13 Oct 2026; v1.1 revises §7 paired-comparison populations and the §9 slope interpretation after an independent audit). Equation numbers are stable references for code, tests and the report.*

**Labels used throughout:**
- **[E]** established method, with source
- **[L]** design choice supported by the cited literature
- **[P]** design choice proposed in this study and justified here
- **[D]** result derived in this document

Evidence status of each source is in [`references.md`](references.md).

---

## 1. Returns and information set

$$ r_t = 100\,\ln(P_t/P_{t-1}) \tag{1} $$

Percent log returns [L: Bollerslev (1986, §7) uses $100\ln(GD_t/GD_{t-1})$]. For SPY, returns are demeaned by the **training-window** mean only [P].

$\mathcal F_{t-1}=\sigma(r_s:s\le t-1)$. Every forecast used at time $t$ is $\mathcal F_{t-1}$-measurable. Tests verify this (no look-ahead).

## 2. In-control data-generating process (simulation)

$$ r_t=\sqrt{h_t}\,\eta_t, \tag{2} $$
$$ h_t=\omega+\alpha r_{t-1}^2+\beta h_{t-1}, \tag{3} $$
$$ \eta_t=\sqrt{(\nu-2)/\nu}\;T_t,\qquad T_t\overset{iid}{\sim}t_\nu . \tag{4} $$

GARCH(1,1) is [E: Bollerslev 1986, eq. 8], whose conditional distribution is normal. Standardized Student-t innovations are [P]. They represent the heavy tails of daily returns, and Patton (2011, Table 1) analyses Student-t returns in the same forecast-evaluation setting.

**Constraints (asserted in code):**

| Condition | Consequence | Source |
|---|---|---|
| $\omega>0,\ \alpha\ge0,\ \beta\ge0,\ h_0>0$ | $h_t>0$ for all $t$ | [E] Bollerslev (1986) eq. 2 conditions |
| $\alpha+\beta<1$ | covariance-stationary, $\sigma^2=\omega/(1-\alpha-\beta)$ | [E] Bollerslev (1986) Thm 1 |
| $\nu>2$ | standardized $t$ has unit variance | [D] |
| $\nu>4$ | $\kappa_\eta=E\eta^4=3(\nu-2)/(\nu-4)<\infty$ | [D] |
| $\beta^2+2\alpha\beta+\kappa_\eta\alpha^2<1$ (margin: $\le0.99$) | $E r_t^4<\infty$, so $\operatorname{Var}(r_t^2)<\infty$ | [D], eq. 5 |

$$ \sigma^2=\frac{\omega}{1-\alpha-\beta},\qquad E h_t^2=\frac{\omega^2+2\omega(\alpha+\beta)\sigma^2}{1-(\beta^2+2\alpha\beta+\kappa_\eta\alpha^2)},\qquad E r_t^4=\kappa_\eta E h_t^2 . \tag{5} $$

*Derivation [D].* Square (3) and take expectations, using independence of $\eta_{t-1}$ and $h_{t-1}$, so that $E r_{t-1}^4=\kappa_\eta E h_{t-1}^2$ and $E[r_{t-1}^2h_{t-1}]=E h_{t-1}^2$. This gives $E h_t^2=\omega^2+2\omega(\alpha+\beta)\sigma^2+(\kappa_\eta\alpha^2+2\alpha\beta+\beta^2)E h_{t-1}^2$, a linear recursion with a finite stationary solution iff the coefficient is $<1$. For $\kappa_\eta=3$ (normal) it reduces to Bollerslev's (1986, Thm 2, $m=2$) condition $3\alpha^2+2\alpha\beta+\beta^2<1$.

**Adopted values (default D1) [P]:**
- α = 0.07, β = 0.91, ν = 6, σ² = 1 (ω = 0.02)
- persistence 0.98
- κ_η = 6
- 4th-moment coefficient 0.9849
- E h² = 2.62, kurtosis of r_t ≈ 15.7

These are stylized daily-equity values. The SPY-training GARCH-t estimates will be reported beside them.

**Scale invariance [D].** Replacing $r$ by $cr$ multiplies every denominator in §4 by $c^2$, so all scores (12) are unchanged:
- $s^2$ scales by $c^2$.
- The QML/ML GARCH fit is equivariant, with $\hat\omega\to c^2\hat\omega$, so $\hat h\to c^2\hat h$.
- CART split choices are invariant: impurity reductions all scale by $c^4$, the bootstrap draws are the same and the split thresholds scale. Leaf means therefore scale by $c^2$.

Hence σ² = 1 is without loss of generality, up to floating point.

## 3. Fault model (persistent volatility-scale change)

$$ r_t^{\text{obs}}=\begin{cases} r_t, & t<\tau,\\ \sqrt{\delta}\,r_t, & t\ge\tau .\end{cases} \tag{6} $$

[L: Schipper & Schmid (2001), eq. 3, with outlier size $a=0$ and scale $\Delta=\sqrt\delta$, $\mu_0=0$.]

By (3), $\delta h_t=\delta\omega+\alpha(r_{t-1}^{\text{obs}})^2+\beta\,\delta h_{t-1}$ for $t>\tau$. So after the change the observed process is exactly GARCH($\delta\omega,\alpha,\beta$) with state $\delta h_\tau$ [D]:
- All constraints are preserved.
- The unconditional variance becomes $\delta\sigma^2$.

Primary δ ∈ {1.5, 2, 3}, i.e. Δ ≈ 1.22, 1.41, 1.73. The innovations are common random numbers (CRN) across δ.

## 4. Forecasters: frozen after training, forecasts update sequentially

The training sample is one simulated path of length $n=3500$ (simulation) or the SPY training window.

**4.1 Constant [E: squared-observation EWMA, Schipper & Schmid 2001 §3.1; MacGregor & Harris 1993].**
$$ d_t^{C}=s^2=\tfrac1n\textstyle\sum_{i=1}^n r_i^2 . \tag{7} $$

**4.2 GARCH [E: Bollerslev 1986; residual chart of Schipper & Schmid 2001 §3.5].**
- $\hat\theta=(\hat\omega,\hat\alpha,\hat\beta,\hat\nu)$ is estimated once by Student-t maximum likelihood (`arch`, zero mean) and then **frozen**.
- The filter runs sequentially over all newly observed returns:
$$ \hat h_t=\hat\omega+\hat\alpha r_{t-1}^2+\hat\beta\hat h_{t-1},\qquad \hat h=\hat\omega/(1-\hat\alpha-\hat\beta)\ \text{at the start of the pre-monitoring history.} \tag{8} $$
- The history is $W=250$ days, and $\hat\beta^{W}\approx0$, so initialisation is immaterial.
- $\hat\nu$ is used in estimation only; $d_t^{G}=\hat h_t$.
- *Difference from Schipper & Schmid [P]:* they use the best linear predictor with **known** parameters. We use the GARCH filter with **estimated**, frozen parameters, as a practitioner would.

**4.3 Random Forest [E: Breiman 2001; L: Christensen et al. 2023 for HAR-type lags, chronological splits and iid bootstrap].**
$$ x_t=\Big(r_{t-1}^2,\ \tfrac15\textstyle\sum_{j=1}^{5}r_{t-j}^2,\ \tfrac1{22}\sum_{j=1}^{22}r_{t-j}^2\Big), \tag{9} $$
$$ y_t=r_t^2,\qquad \hat f=\arg\min \text{(squared error, forest)},\qquad m(x)=E[r_t^2\mid x_t=x], \tag{10} $$
$$ d_t^{RF}=\hat\sigma_t^2=\max\{\hat f(x_t),\,c\,s^2\},\qquad c=10^{-4}. \tag{11} $$

- The squared-error regression forest averages trees whose leaf values are bootstrap means of $y$ [E: Breiman 2001 §11, eq. 11].
- **Positivity [D].** Every prediction is a convex combination of nonnegative training targets. It is therefore $>0$ unless every target in a leaf is exactly 0. The floor (11) is a guard; the number of times it binds is counted and tested.
- **No extrapolation (saturation) [D].** $\hat f(x)\le$ the largest leaf mean.
- **Interpretation [D].** $E[r_t^2\mid\mathcal F_{t-1}]=h_t+(E[r_t\mid\mathcal F_{t-1}])^2$. With zero conditional mean (simulation), this equals $h_t$. The RF estimates $E[h_t\mid x_t]\neq h_t$, because $x_t$ is a coarsening of $\mathcal F_{t-1}$.
- **Features.** Only the symmetric magnitude features in (11) are used. No signed return is included, so the RF and the symmetric GARCH(1,1) use information symmetrically [P].
- **Hyperparameters [P/L].**
  - 100 trees in the pilot.
  - Grid: `min_samples_leaf` ∈ {50, 200, 800} × `max_features` ∈ {1, 3}.
  - Selection: lowest mean QLIKE (21) against the proxy $r^2$ on an independent development path.
  - Large leaves are used because the target $r^2=h\eta^2$ is far noisier than the realized-variance target of Christensen et al. (2023, who use min. node size 5).
  - The grid and selection rule are fixed in advance.
- **Deterministic prediction [P].** Tree predictions are averaged in fixed tree order, parallel across row chunks. This avoids thread-order floating-point nondeterminism.

## 5. Monitoring score and EWMA

$$ u_t^{(k)}=r_t^2/d_t^{(k)},\qquad k\in\{C,G,RF\}\ (\text{plus diagnostic } d_t^{O}=\text{filter (8) with the true in-control }\theta), \tag{12} $$

The diagnostic $d^{O}$ is the GARCH filter with the **true in-control parameters, known and frozen**. This is the known-parameter setting of Schipper & Schmid (2001), though with a filter rather than their best linear predictor. It equals $h_t$ while the process is in control, up to an initialisation error of order $\beta^{W}$. It is **not** the true post-change variance: a denominator that knew the change would make the chart blind to it by construction.
$$ Z_t=\lambda u_t+(1-\lambda)Z_{t-1},\qquad Z_0=1,\qquad 0<\lambda\le1, \tag{13} $$
$$ T=\inf\{t\ge1: Z_t>h\}. \tag{14} $$

- The EWMA is [E: Roberts 1959, eq. 1], applied to squared-observation and residual statistics as in Schipper & Schmid (2001, §3.1, §3.5; residual chart started at 1).
- The chart is one-sided upper [P].
- **Gaussian limits are not used.** $u$ is skewed, heavy-tailed and serially dependent (except for the known-parameter diagnostic). Roberts' limits (eqs. 4–5) assume iid normal data.

**Properties of u [D]:**
- Known parameters, in control: $u_t=\eta_t^2$ is iid with $E u=1$ and $\operatorname{Var}u=\kappa_\eta-1=5$ (ν = 6). This allows an independent Markov-chain (Brook–Evans) check of the calibration machinery.
- Estimated denominator: $u_t=\eta_t^2 h_t/d_t$, so $E[u_t\mid\mathcal F_{t-1}]=h_t/d_t$. The ratio $h_t/d_t$ is persistent, so $u$ inherits dependence.
- If $d_t=h_t\xi_t$ with $E\xi_t=1$, $\xi_t$ independent of $\eta_t$, then $E u_t=E[1/\xi_t]\ge1$ by Jensen. Noisier forecasts raise the in-control mean and spread of $u$, and hence the UCL.

## 6. Run lengths, calibration and validation

**Timeline.** Each path has a 500-observation burn-in (discarded), then $W=250$ pre-monitoring days (forecaster history), then monitoring days $t=1,2,\dots$ One monitoring opportunity equals one trading day; warm-up days are never counted.

**Censoring.** In-control paths have $T_{\max}$ monitoring days. We observe $\min(T,T_{\max})$ and $\mathbb 1\{T>T_{\max}\}$.

$$ \hat A(h)=\frac1N\sum_{i=1}^N\min\{T_i(h),T_{\max}\}. \tag{15} $$

- (15) is the **restricted** mean run length, a lower bound on $E[T]$.
- $T_i(h)$ is nondecreasing in $h$ for every path [D], so $\hat A$ is monotone.
- The censored fraction is reported; $T_{\max}$ is sized so that it is $<1\%$, and is increased if exceeded, never extrapolated.

$$ h^{*}=\min\{h:\hat A(h)\ge A_0\},\qquad A_0=500, \tag{16} $$

found by bisection on fixed calibration paths [P]. Because (15) is a lower bound, $h^*$ is slightly conservative.

**Validation** uses independent paths with $h^*$ fixed. It reports:
- $\hat A_{\text{val}}$, with $SE=\widehat{sd}/\sqrt N$ and a 95% CI
- censored fraction
- RL quantiles (10%, 50%, 90%)
- $P(T\le250)$ and $P(T<\tau)$

It passes if $A_0$ lies in the CI and $|\hat A_{\text{val}}/A_0-1|\le0.15$.

ARL₀ is **conditional on the trained forecasters** of the replicate. Variation across training samples needs replicates (sized after the pilot).

## 7. Out-of-control evaluation

The change occurs at monitoring day τ = 50. Paths have $\tau-1+H$ monitoring days ($H=500$ in the pilot).

$$ \text{pre-change false alarm: } T<\tau;\qquad D=T-\tau+1\ \ (T\ge\tau);\qquad D_H=\min(D,H). \tag{17} $$

**Reported:**
- $\hat P(T<\tau)$, checked against the validation $P(T<\tau)$
- conditional on $T\ge\tau$: the restricted mean $E[D_H]$, **labelled "restricted to H"** and never called ARL₁
- median $D$
- $P(D\le5)$, $P(D\le20)$, $P(D\le60)$
- censored fraction $P(T>\tau+H-1)$

**Paired comparisons.** With CRN, per-path differences in $D_H$ between two charts are taken over paths with $T\ge\tau$ for both. CIs come from a nonparametric bootstrap over paths (B = 2000) [P].

- **Populations.** Per-chart summaries are over the chart's own evaluable set $E_k=\{i:T_i^{(k)}\ge\tau\}$, which differs between charts. Paired contrasts are over $E_a\cap E_b$. A paired contrast in restricted mean delay therefore need not equal the difference of the per-chart restricted means, and it is never a difference of medians.
- **Baseline.** Every contrast is reported with its δ = 1 (no-change) counterpart on the same paths.
- **Scope.** Within a replicate, the intervals are Monte Carlo intervals **conditional on the trained forecasters and the calibrated $h^*$**. They exclude training variability and calibration uncertainty, and they are not adjusted for multiple comparisons.

## 8. Adaptation masking (pre-registered analysis)

$$ \bar u_k=\frac1N\sum_i u_{i,\tau+k},\ \ k=0,\dots,H-1;\qquad \bar u_E=\text{mean}_{k\in[0,19]}\bar u_k,\quad \bar u_S=\text{mean}_{k\in[100,499]}\bar u_k, \tag{18} $$

computed on full paths whether or not an alarm occurred; data generation never depends on alarms. The out-of-control paths are CRN, so each path is also evaluated **without** the change ($\delta=1$, the no-change counterfactual) [P]. This gives:
- a false-alarm baseline for every detection metric
- a paired denominator for the masking ratio

$$ M=\frac{\bar u_S(\delta)/\bar u_S(1)-1}{\delta-1}\qquad(\text{fraction of the shift still visible after adaptation}). \tag{19} $$

For the conventional chart $u$ scales exactly by δ, so $M=1$ identically. The paired form removes the sampling noise that an unpaired in-control mean would add.

**First-order theory for the frozen GARCH filter [D].**
- Under the post-change process $E r^2=\delta\sigma^2$.
- The stationary mean of (8) is $E\hat h=(\hat\omega+\hat\alpha\delta\sigma^2)/(1-\hat\beta)$, against $(\hat\omega+\hat\alpha\sigma^2)/(1-\hat\beta)$ in control.
- Normalising the ratio of means by its in-control value:

$$ R_G(\delta)=\frac{\delta(\hat\omega+\hat\alpha\sigma^2)}{\hat\omega+\hat\alpha\delta\sigma^2},\qquad M_G^{\text{pred}}=\frac{R_G(\delta)-1}{\delta-1},\qquad \lim_{\delta\to\infty}R_G=\frac{\hat\omega+\hat\alpha\sigma^2}{\hat\alpha\sigma^2}. \tag{20} $$

With $\hat\omega=(1-\hat\alpha-\hat\beta)\sigma^2$ the limit is $(1-\hat\beta)/\hat\alpha$, which is about 1.29 for the pilot DGP. At the true pilot values, $R_G$ is 1.08, 1.125 and 1.17, and $M_G^{\text{pred}}$ is 0.16, 0.125 and 0.087, for δ = 1.5, 2, 3. This is a ratio-of-means approximation ($E[r^2/\hat h]\ne E r^2/E\hat h$) and is checked, not assumed.

**Transient [D].** $\hat h_\tau$ is $\mathcal F_{\tau-1}$-measurable and unaffected by the change. Hence $E[u_\tau\mid\mathcal F_{\tau-1}]=\delta\,h_\tau/\hat h_\tau$, i.e. the full shift is visible initially. The filter then adapts at a rate of order $\hat\beta^k$. The RF adapts through its 1-, 5- and 22-day features, so within at most 22 days, but only up to its saturation level.

**Further reported metrics:**
- initial detection: $P(D\le5)$, $P(D\le20)$
- late detection: $P(20<D\le H\mid D>20)$
- **alarm occupancy**: the fraction of days $k\in[100,499]$ with $Z_{\tau+k}>h^*$, with no reset

## 9. Forecast evaluation (separate from monitoring)

$$ L_{\text{QLIKE}}(p,f)=\log f+p/f,\qquad L_{\text{MSE}}(p,f)=(p-f)^2, \tag{21} $$

[E: Patton 2011, eqs. 6 and 5. Both are robust to a conditionally unbiased noisy proxy (Prop. 1, Remark 2).] In simulation the target is $p=h_t$ (true) and also $p=r_t^2$ (proxy); on SPY only the proxy is available.

$$ G=\frac{\bar L_C-\bar L_{RF}}{\bar L_C-\bar L_{\text{oracle}}}\quad(\text{QLIKE vs true }h;\ \text{oracle = known-parameter filter}). \tag{22} $$

Diagnostics:
- mean of $u$
- average within-path ACF of $u$ at lags 1, 5, 22 [L: Bollerslev 1986 §4, §7 uses autocorrelations of $\epsilon_t^2h_t^{-1}$ for diagnostic checking]
- floor-binding rate
- quantiles of $u$
- slope of the forecast on the true variance, $\operatorname{cov}(d,h)/\operatorname{var}(h)$, with one normalisation for both moments. A value below 1 means the forecast varies less than proportionally with $h$ (reduced responsiveness). **It does not identify the cause [D].** For the exact conditional expectation $d^*=E[h_t\mid x_t]$, $\operatorname{cov}(d^*,h_t)=\operatorname{var}(d^*)$, so its slope is $\operatorname{var}(d^*)/\operatorname{var}(h_t)\le1$, with equality only if $h_t$ is a function of $x_t$. A slope below 1 can therefore come from limited predictor information alone, as well as from estimation error, regularization (leaf size, bootstrap averaging) or saturation (§4.3).

## 10. Experimental roles and random numbers

| Role | Content | Pilot size |
|---|---|---|
| Training | 1 path, $n=3500$ | 1 |
| Development | 1 independent path, $n=3500$ (+22 lags) | 1 |
| Calibration | in-control paths, $W+T_{\max}$ | 300 × (250 + 3000) |
| Validation | independent in-control paths | 300 × (250 + 3000) |
| Out-of-control | independent paths, CRN across δ and charts | 300 × (250 + 549) |

- Streams come from `numpy.random.SeedSequence(master, spawn_key=(replicate, role))`. The RF `random_state` is drawn from its own stream.
- Seeds and spawn keys are written to every run directory.
- Bit-for-bit reproducibility is claimed only where `run.py verify` demonstrates it (same machine and environment).

## 11. SPY application protocol (executed after pilot approval)

| Element | Choice |
|---|---|
| Source | Yahoo Finance via `yfinance` (1.7.0), ticker SPY, `auto_adjust=True` (split- and dividend-adjusted close) |
| Snapshot | One download saved to `data/raw/` with access timestamp and SHA-256. The analysis reads only the snapshot |
| Training | 1993-02-01 → 2006-12-29. RF grid chosen by chronological split (fit 1993–2003, validate 2004–2006, QLIKE), then refit on 1993–2006 and frozen. GARCH(1,1)-t fitted on 1993–2006 and frozen |
| Monitoring | 2007-01-03 → 2026-09-30. Filter and features update daily; no refits |
| UCL | Calibrated to ARL₀ = 500 on in-control paths simulated from the training GARCH-t fit, with the frozen SPY forecasters applied. **This assumption favours GARCH and is disclosed** |
| Output | Z paths with UCL; QLIKE/MSE against the $r^2$ proxy; alarm days per year; first signal after pre-registered reference dates |

**Interpretation limits.** Alarms are descriptive. They are **not** validated predictions of market events, and imply nothing about trading profitability. No trading or backtesting code is in scope.

## 12. Known limitations (to be stated in the report)

1. The DGP is correctly specified for GARCH (home advantage). The RF can at best tie in simulation.
2. Information is symmetric; the leverage effect is ignored by both forecasters.
3. Performance is conditional on the training replicate(s).
4. The masking theory (20) is a first-order approximation.
5. The model-based SPY calibration assumes the training GARCH-t is the in-control law.
6. MacGregor & Harris (1993) and Lu & Reynolds (1999) are cited at metadata level only.
