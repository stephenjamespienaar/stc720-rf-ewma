# Methodology — RF–EWMA Monitoring of Financial Volatility

*Version 1.8, 27 Oct 2026 (v1.8 adds the approved finite-variance calibration design and diagnostics a–i in §11; v1.7 records the post-stop variance-targeting refinement in §11; v1.6 freezes the SPY application design and reference dates in §11 before any SPY data; v1.5 adds the supplementary post hoc Holm analysis note in §7.4; v1.0: 13 Oct 2026; v1.1 revises §7 paired-comparison populations and the §9 slope interpretation after an independent audit; v1.2 adds the Phase 2 production estimators — eqs. 23–28, alarm-day coding, X(k), conditional quantiles, masking SE, replicate aggregation, pre-registered primary endpoints, production and sensitivity configurations, §10.1–10.3; v1.3 applies the Phase 2 audit: eq. 28 relabelled as residual between-system variance σ̂²_sys (arithmetic unchanged), matched sensitivity design, reconstruction scope of `paths.npz`, primary-endpoint scope, smoke versus validation; v1.4 records the post-benchmark amendments made before production — R = 20 training replicates and the equivalence-style in-control validation rule, eq. 29, with the production failure-handling policy). Equation numbers are stable references for code, tests and the report; v1.2 appends equations and renumbers none.*

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

**Validation rule (amended, v1.4).** *Post-pilot, post-benchmark methodological amendment made before production (user decision, 14 Oct 2026); recorded in each run's configuration (`config["ic_validation"]`) before any computation.* With target $A_0$, tolerance $\varepsilon=0.15$ and the independent-validation interval $[L,U]=\hat A_{\text{val}}\mp1.96\,SE$,
$$ \text{PASS}\iff L\ge A_0(1-\varepsilon)\ \text{ and }\ U\le A_0(1+\varepsilon), \tag{29} $$
i.e. the whole 95% CI lies in [425, 575] for $A_0=500$ and in [85, 115] for the ARL₀ = 100 sensitivity. The bounds are exactly $A_0(1\pm\varepsilon)$ and inclusive. The code compares them in exact rational arithmetic (`chart.ic_equivalence`), so the binary representation of ε cannot move a bound (tested at the bounds and one floating-point step either side). Each validation result stores $A_0$, ε, the bounds, $\hat A_{\text{val}}/A_0-1$, $N$ and the outcome.
- **Original rule (v1.0–v1.3; historical).** $A_0$ inside the 95% CI and $|\hat A_{\text{val}}/A_0-1|\le0.15$. It judged the pilot and the production-scale benchmark, whose recorded outcomes are unchanged (benchmark: 2 of 6 primary and 2 of 2 diagnostic configurations passed).
- **Reason for the amendment.** The CI condition of the original rule tests *exact* calibration. It ignores the Monte Carlo error of $h^*$ from the 2,000 calibration paths, which is of similar size to the validation SE, so an unbiased calibration fails it more often than 5%. Rule (29) asks instead whether the in-control ARL is demonstrably within the practical tolerance. **Disclosure:** the amendment was adopted after the benchmark had been seen. Evaluated hypothetically under (29), all eight benchmark CIs lie in [425, 575]. This does not alter the benchmark's recorded outcome, and the benchmark remains excluded from all inference.
- **Caveats.**
  - The CI is conditional on the replicate's calibrated $h^*$ and does not include the uncertainty of estimating $h^*$. Conditional on $h^*$, (29) is approximately a two-one-sided-tests check at level 0.025 per side. It operationalizes practical adequacy under this design and is **not** a complete formal equivalence test.
  - It is applied to 6 primary and 2 diagnostic chart × λ configurations in each of $R$ replicates. The individual 95% CIs give no simultaneous (family-wise) coverage, so pass counts are descriptive.
  - At $N=2000$ the validation SE is about 2.2–2.3% of $\hat A_{\text{val}}$ (benchmark), so passing requires roughly $445\lesssim\hat A_{\text{val}}\lesssim550$ for $A_0=500$. A systematic shortfall of a few percent can pass; it remains visible in the reported relative deviation.

**Production failure handling** (fixed before production; user decision, 14 Oct 2026):
1. All 20 predefined training-and-calibration replicates are run.
2. Replicates that fail validation are neither discarded nor selectively replaced.
3. Thresholds are never recalibrated on validation observations, nor adjusted after validation outcomes are seen.
4. Every per-replicate validation estimate, CI, relative deviation, $N$ and outcome is reported (report Table 3).
5. Pass counts are reported for every chart and λ.
6. Primary results are reported over all replicates. Failures that limit comparability or confidence in nominal ARL₀ control are flagged next to them (`report.validation_failures`: under Table 3 and before the primary-endpoint table).
7. If any configuration fails, the report does not claim that all schemes achieved nominal calibration.

Interpretation questions about severe failures go to a separate, documented scientific decision. There are no post hoc exclusions or reruns.

ARL₀ is **conditional on the trained forecasters** of the replicate. Variation across training samples is captured by independent training replicates (production R = 20, §10.1) and aggregated as in §10.2.

## 7. Out-of-control evaluation

The change occurs at monitoring day τ = 50. Paths have $M=\tau-1+H$ monitoring days ($H=500$, so $M=549$).

$$ \text{pre-change false alarm: } T<\tau;\qquad D=T-\tau+1\ \ (T\ge\tau);\qquad D_H=\min(D,H). \tag{17} $$

**Alarm-day coding [P].** The alarm day is stored per path as an integer $T\in\{1,\dots,M+1\}$. $T=M$ (day 549) is the last observable alarm: $D=H$, a **detection**. $T=M+1$ (550) is the sentinel for right-censoring (no alarm by day $M$, so $D>H$). Both have $D_H=H$, but only the first is a detection; a censored path is never counted as a detection by any estimator below (`chart.alarm_days`, `chart.delays_from_days`; regression-tested, including the round trip through the stored per-path file).

### 7.1 Per-chart estimators (within one replicate)

All are conditional on $T\ge\tau$, over the chart's own evaluable set $E_k=\{i:T_i^{(k)}\ge\tau\}$, which is identical across δ by CRN. Each has a Monte Carlo SE, sample SD$/\sqrt{|E_k|}$ (for proportions this is the binomial SE up to $\sqrt{n/(n-1)}$).
- $\hat P(T<\tau)$ over all $N$ paths, checked against the validation $P(T<\tau)$ (A9).
- Restricted mean delay $\mathrm{RMD}_H=\overline{D_H}$, **labelled "restricted to H"** and never called ARL₁.
- $\hat P(D\le k)$ for $k\in\{5,20,60\}$, and the censored fraction $P(T>M)$.
- **Excess detection** (baseline-adjusted, paired with the no-change counterfactual of the same path) [P]:
$$ \hat X(k)=\frac1{|E|}\sum_{i\in E}\Big[\mathbb 1\{D_i(\delta)\le k\}-\mathbb 1\{D_i(1)\le k\}\Big],\qquad SE=\frac{\widehat{sd}}{\sqrt{|E|}} . \tag{24} $$
  At δ = 1 it is 0 by construction. Because $E$ is the same at δ and at 1, $\hat X(k)=\hat P(D(\delta)\le k)-\hat P(D(1)\le k)$, but the SE uses the paired differences.
- **Conditional quantiles of $D$** under administrative censoring at $H$ [P]: inverted empirical CDF over $E$, with censored paths in the denominator but never treated as detections,
$$ \hat q_p=D_{(\lceil p|E|\rceil)}^{\text{det}}\ \text{ if }\ \lceil p|E|\rceil\le\#\{i\in E:\ T_i\le M\},\ \text{ else not identifiable (not reported)}, \tag{25} $$
  where $D^{\text{det}}_{(j)}$ is the $j$-th smallest detected delay; $p\in\{0.25,0.5,0.75\}$. No interpolation; the value $H$ of a censored path is never returned.
- $P(20<D\le H\mid D>20)$ (late detection) and, over all $N$ paths, **alarm occupancy** in the sustained window with its paired excess over δ = 1 (§8).

### 7.2 Paired comparisons between charts

With CRN, per-path differences between two charts are taken over the paths with $T\ge\tau$ for **both**, $E_a\cap E_b$:
$$ \hat\Delta(a,b)=\frac1n\sum_{i\in E_a\cap E_b}(y_i^{a}-y_i^{b}),\qquad SE=\frac{\widehat{sd}(y^{a}-y^{b})}{\sqrt n},\qquad \text{95\% CI } \hat\Delta\pm1.96\,SE, \tag{23} $$
with $y=D_H$ (restricted-mean contrast) or $y_i=\mathbb 1\{D_i(\delta)\le k\}-\mathbb 1\{D_i(1)\le k\}$ (paired excess-detection contrast, $X_a(k)-X_b(k)$ on $E_a\cap E_b$). The normal paired SE replaces the pilot's percentile bootstrap [P]; a percentile bootstrap over paths (B = 2000) is retained as a check (`boot_ci95`).
- **Populations.** Per-chart summaries are over $E_k$; contrasts over $E_a\cap E_b$. A paired contrast therefore need not equal the difference of the per-chart summaries, and it is never a difference of medians.
- **Baseline.** Every $D_H$ contrast is reported with its δ = 1 (no-change) counterpart on the same paths; $X(k)$ contrasts are 0 at δ = 1 by construction.
- **Scope.** Within a replicate, intervals are Monte Carlo intervals **conditional on the trained forecasters and the calibrated $h^*$**. They exclude training variability (handled across replicates, §10.2) and calibration uncertainty, and are not adjusted for multiple comparisons.

### 7.3 Horizon H = 500

$H=500$ (not 1,000) [P, readiness review]: with no change, 64–67% of evaluable pilot paths alarmed within 500 days after τ, so later alarms are dominated by false-alarm timing; $H=500$ also halves the out-of-control cost. Every delay quantity is labelled restricted to $H$.

### 7.4 Pre-registered primary endpoints

*Pre-specified after the exploratory pilot, before production (user decision, 14 Oct 2026); recorded in the run configuration (`config["primary"]`), so each run's `config.json` captures them before computation.*

The **12 primary contrasts** are (23) at λ = 0.1 for
- the pairs RF − GARCH and RF − conventional,
- the metrics $\mathrm{RMD}_{500}$ and the paired excess detection $X(20)$,
- δ ∈ {1.5, 2, 3}, each shown with its δ = 1 counterpart,

each aggregated over training replicates as in §10.2. Only these paired $\mathrm{RMD}_{500}$ and $X(20)$ contrasts are primary. Everything else is secondary or descriptive: λ = 0.2, GARCH − conventional, $X(5)$ and $X(60)$ (including their paired contrasts), quantiles, occupancy, masking, per-chart levels including per-chart $X(20)$, and **every result of the ARL₀ = 100 sensitivity run**. No multiplicity adjustment is applied; the article must say so.

**Supplementary post hoc multiplicity analysis (v1.5, 27 Oct 2026).** This was decided **after** the production results were seen, so it is **not** pre-registered, and the primary analysis above is unchanged. The analysis:
- applies two-sided one-sample t₁₉ tests of H₀: θ = 0 to the 20 equal-weight replicate estimates of each of the 12 primary contrasts, in the framework of eq. 27
- adjusts them with Holm's step-down procedure at family-wise α = 0.05 over exactly these 12 contrasts
- adds a descriptive robustness check: exact sign tests, Holm-adjusted. These test the balance of replicate signs, which is a different null from the mean-zero t test

The δ = 1 baselines are outside the family. The inferential target is the mean paired contrast over independently generated and fitted systems under this design. Results: [`p2_multiplicity_report.md`](p2_multiplicity_report.md).

## 8. Adaptation masking (pre-registered analysis)

$$ \bar u_k=\frac1N\sum_i u_{i,\tau+k},\ \ k=0,\dots,H-1;\qquad \bar u_E=\text{mean}_{k\in[0,19]}\bar u_k,\quad \bar u_S=\text{mean}_{k\in[100,499]}\bar u_k, \tag{18} $$

computed on full paths whether or not an alarm occurred; data generation never depends on alarms. The out-of-control paths are CRN, so each path is also evaluated **without** the change ($\delta=1$, the no-change counterfactual) [P]. This gives:
- a false-alarm baseline for every detection metric
- a paired denominator for the masking ratio

$$ M=\frac{\bar u_S(\delta)/\bar u_S(1)-1}{\delta-1}\qquad(\text{fraction of the shift still visible after adaptation}). \tag{19} $$

For the conventional chart $u$ scales exactly by δ, so $M=1$ identically (**by construction**, an exactness check that carries no comparative evidence). The paired form removes the sampling noise that an unpaired in-control mean would add.

**Uncertainty of M [P].** With per-path window means $A_i=\bar u_{S,i}(\delta)$ and $B_i=\bar u_{S,i}(1)$ over all $N$ paths, $\hat R=\bar A/\bar B$ and, by the delta method,
$$ SE(\hat R)\approx\frac{1}{\bar B}\sqrt{\frac{\sum_{i=1}^N(A_i-\hat RB_i)^2}{N(N-1)}},\qquad SE(\hat M)=\frac{SE(\hat R)}{\delta-1}. \tag{26} $$
The same formula gives the SE of the early-window ratio. For the conventional chart $A_i=\delta B_i$, so $SE=0$ up to floating point (tested).

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

| Role | Content | Pilot size | Production size |
|---|---|---|---|
| Training | 1 path, $n=3500$ | 1 | 1 per replicate |
| Development | 1 independent path, $n=3500$ (+22 lags) | 1 | 1 per replicate |
| Calibration | in-control paths, $W+T_{\max}$ | 300 × (250 + 3000) | 2000 × (250 + 5000) |
| Validation | independent in-control paths | 300 × (250 + 3000) | 2000 × (250 + 5000) |
| Out-of-control | independent paths, CRN across δ and charts | 300 × (250 + 549) | 2000 × (250 + 549) |

- Streams come from `numpy.random.SeedSequence(master, spawn_key=(replicate, role))`. The RF `random_state` is drawn from its own stream.
- Seeds and spawn keys are written to every run directory.
- Bit-for-bit reproducibility is claimed only where `run.py verify` demonstrates it (same machine and environment).
- Per-path outputs (alarm day, occupancy count, window means; δ = 1 included) are stored in `paths.npz`. The detection, occupancy and empirical masking statistics of a replicate (§7.1–7.2, §8) are deterministic functions of them and can be recomputed (tested). The bootstrap check intervals additionally require the same configuration ($B$) and the replicate's fresh bootstrap stream. Complete daily score profiles cannot be reconstructed: only their path averages are stored (in `results.json`).

### 10.1 Production and sensitivity configurations

| | Production (primary) | Sensitivity (secondary) | Benchmark (performance only) |
|---|---|---|---|
| Mode | `production` | `sensitivity_arl100` | `benchmark` |
| Target ARL₀ | 500 | **100** | 500 |
| Replicates R | **20** (amended from 10 after the benchmark, before production) | 20 (inherits production) | 1 |
| Master seed | **20261014** | 20261014 (same models and paths as production; limits calibrated and validated separately, on the same paths, to the other target) | 20261013 |
| Other settings | $n_{\text{train}}=n_{\text{dev}}=3500$; 2,000 calibration, 2,000 validation and 2,000 OOC paths per replicate; $T_{\max}=5000$; $\tau=50$; $H=500$; δ ∈ {1, 1.5, 2, 3}; λ ∈ {0.1 (primary), 0.2}; RF 500 trees, grid as §4.3; B = 2000 | as production | as production |

- The production seed 20261014 is new [P, user decision 14 Oct 2026], so production evidence shares no random numbers with the exploratory pilot (seed 20261013, whose replicate 0 would otherwise reuse the pilot's training path and leading draws).
- **Production and sensitivity are matched, not independent experiments.** They reuse the same simulation streams (training, development, calibration, validation and out-of-control paths, and the fitted forecasters) and differ only in the target ARL₀ and hence in the separately calibrated control limits. Differences between them isolate the effect of the target, but their Monte Carlo errors are correlated, so their results must not be treated as independent replications. Every sensitivity result is secondary.
- The **benchmark** is a production-scale performance benchmark (R = 1, seed 20261013). It is not a reproduction of the original pilot, and its outputs are **excluded** from the primary production inference and from the ARL₀ = 100 sensitivity results.
- Production, sensitivity and benchmark refuse to start without `--approved`. The flag is a technical safeguard only; each run needs the student's explicit authorization.

### 10.2 Aggregation over training replicates

Within a replicate, every quantity is conditional on its trained system: θ̂, the selected and fitted forest, s² and the calibrated h*. The method-level estimand is $\theta=E_r[\theta_r]$, estimated with **equal weights** over the $R$ independently trained and calibrated systems; paths are never pooled across replicates [P]:
$$ \bar\theta=\frac1R\sum_{r=1}^R\hat\theta_r,\qquad s_b^2=\frac{1}{R-1}\sum_r(\hat\theta_r-\bar\theta)^2,\qquad \text{95\% CI } \bar\theta\pm t_{R-1,0.975}\,\frac{s_b}{\sqrt R}, \tag{27} $$
with $t_{19}=2.093$ for production R = 20. With $w_r$ the within-replicate (evaluation) Monte Carlo SE of $\hat\theta_r$, $\operatorname{Var}(\hat\theta_r)\approx\sigma^2_{\text{sys}}+E[w_r^2]$, hence
$$ \hat\sigma^2_{\text{sys}}=\max\Big(0,\ s_b^2-\frac1R\sum_r w_r^2\Big),\qquad \hat\sigma_{\text{sys}}=\sqrt{\hat\sigma^2_{\text{sys}}} . \tag{28} $$
$\hat\sigma^2_{\text{sys}}$ is the **residual between-system variability (training, model selection, forest randomness and calibration), after subtracting the estimated evaluation Monte Carlo variance** (`var_between_resid`, `sd_between_resid`). It does **not** isolate training-sample variability: each replicate also has its own calibration paths, so its h* varies, and this variation is included. This holds for every chart, including the conventional chart, whose s² and calibrated limit both vary across replicates, so its residual component need not be zero. Equation (28) is a descriptive method-of-moments approximation, not a separately identified (causal) decomposition of model-training uncertainty; the truncation at 0 and the small R make it imprecise. The mean of the squared SEs is used, not the square of the mean SE ($\bar w^2\le\overline{w^2}$ by Jensen, so $\bar w^2$ would overstate $\hat\sigma_{\text{sys}}$). The t interval (27) uses $s_b$ alone and does not depend on (28).

Also reported: every replicate value, the range, and the sign counts with an exact two-sided sign test. Only an explicit list of estimands is aggregated (`aggregate.schema`); validation pass flags and frozen-model checks are reported as counts of replicates, sample sizes ($|E|$, paired $n$) as ranges, and seeds and other metadata are not aggregated. A quantity not identifiable in some replicate (e.g. a conditional quantile) is listed per replicate without an aggregate.

**Smoke runs are not validation.** `smoke` and `verify` check that the pipeline executes and is reproducible at toy size (60 paths, ARL₀ = 50); ARL₀ validation can fail there and failures are reported, never dropped. Under rule (29) a smoke configuration essentially cannot pass: its CI half-width exceeds the ±15% margin. Calibration and validation adequacy are judged only on the production-size runs.

**Limitations.** With R = 20 the t interval rests on approximate normality of $\hat\theta_r$, which cannot be checked well; $s_b$ is imprecise; results are conditional on the DGP and $n_{\text{train}}$.

### 10.3 Original objectives, pilot-motivated refinements and secondary analyses

| Category | Items |
|---|---|
| **Original research objectives** (research plan, approved 13 Oct) | RQ1–RQ4; three charts on a common score with frozen forecasters; empirical calibration to a common ARL₀ with independent validation; CRN out-of-control evaluation at δ ∈ {1.5, 2, 3}; adaptation masking M (eq. 19) |
| **Pilot-motivated refinements** (readiness review and audit; fixed before production) | replicates R = 10 (amended to 20, next row) with equal-weight aggregation (§10.2); H = 500 (§7.3); X(k) (eq. 24) and occupancy excess; normal paired SE with bootstrap check (eq. 23); masking SE (eq. 26); censoring-aware quantiles (eq. 25); δ = 1 counterpart for every contrast; pre-registered primary endpoints (§7.4); new production seed |
| **Post-benchmark amendments** (user decision 14 Oct 2026, after the performance benchmark, before production) | production and sensitivity R = 10 → 20; in-control validation rule (29) replacing the original rule (§6); production failure-handling policy (§6); provenance distinguishes tracked changes, untracked files and development-tool state |
| **Secondary sensitivity** | ARL₀ = 100 (§10.1), testing whether the ranking depends on ARL₀. A reversal is declared only if the aggregate CIs exclude 0 with opposite signs at ARL₀ = 500 and 100; otherwise "inconclusive"; never a causal claim |

## 11. SPY application protocol (v1.6: design frozen 27 Oct 2026, before any SPY data was downloaded)

*Original design approved 13 Oct 2026; the binding decisions D1–D6 were made by the user on 27 Oct 2026. Implemented as the guarded `spy` mode (`run.py`, `src/application.py`, `src/spy.py`) and tested on synthetic prices only.*

| Element | Choice |
|---|---|
| Source (D1) | Yahoo Finance via `yfinance` 1.7.0, ticker SPY. `auto_adjust=True` (split- and dividend-adjusted), `multi_level_index=False`, `repair=False`, `keepna=True` (missing rows surface instead of being dropped), `ignore_tz=True` |
| Snapshot (D6) | A single download, `end` exclusive 2026-10-01, saved as `data/raw/SPY.csv` with all adjusted columns. `SPY.meta.json` records the access time (UTC), software versions, the download arguments and the SHA-256. The analysis reads only the snapshot, and a snapshot is never overwritten. It is not committed to Git. Yahoo back-adjusts its history, so a later download can differ: the frozen file and its hash are the record, and the report discloses this |
| Integrity (S1) | **Hard errors stop the analysis:** an empty series, duplicate or non-increasing dates, a timezone-aware index, non-finite or non-positive prices, a first date other than 1993-01-29, or a last date after 2026-09-30. **Diagnostics only:** the row count (expected 8,480–8,490) and calendar gaps over 4 days. Nothing is inserted, interpolated or deleted; a multi-day closure stays a single return. The 10 largest absolute returns are listed for an independent check |
| Returns | $r_t=100\ln(P_t/P_{t-1})$ of the adjusted close, demeaned by the **training** mean only. The run stops unless the first training return is 1993-02-01, the last training return is 2006-12-29, the first monitoring return is 2007-01-03, and no return lies between them |
| Training (D5) | 1993-02-01 → 2006-12-29 (training only). $s^2$ = the mean of demeaned $r^2$. GARCH(1,1)-t is fitted by ML with zero mean and frozen. RF: the six-cell grid (`min_samples_leaf` ∈ {50, 200, 800} × `max_features` ∈ {1, 3}, 500 trees, floor $10^{-4}s^2$) is fitted on 1993–2003 and selected by mean QLIKE against $r^2$ on 2004–2006 (rows dated ≥ 2004-01-01, with features from the continuous training series). The selected cell is then refitted on 1993–2006 and frozen. Master seed **20261028**, with streams `SeedSequence(20261028, spawn_key=(role,))` for rf, cal and val |
| Fourth-moment gate (D2) | Before any limit is calibrated, the fitted $\hat\theta$ is checked with the production simulator's **unchanged** strict check (ν > 4 and $\beta^2+2\alpha\beta+\kappa\alpha^2\le0.99$). If it fails, the run stops (status `stopped_at_fourth_moment_gate`, exit 3): no limit is calibrated and no monitoring return is used. Only then may a narrowly scoped finite-variance option be implemented, which requires ω > 0, α, β ≥ 0, α + β < 1 and ν > 2. It must preserve the production defaults, be regression-tested and be documented. Parameters are never clipped |
| Limits | $h^*$ by bisection to ARL₀ = 500 (eqs. 15–16) on 2,000 in-control paths of W + 5,000 days, **simulated from the fitted SPY GARCH-t** (burn-in 2,000, longer than the simulation's 500 because the persistence may be near 1), with the frozen SPY $s^2$, GARCH filter and RF applied. These are validated on 2,000 independent simulated paths (eq. 29). **This calibration model favours GARCH, and the report must say so prominently.** Monitoring data are never used for limits, and there is no recalibration after a validation failure: failures are reported |
| Monitoring (D3) | 2007-01-03 → 2026-09-30. The last W = 250 training returns are the pre-monitoring history, as in the simulation, and the GARCH state and RF lag features update daily from past returns only. Parameters, trees, $s^2$ and $h^*$ are fixed. **Continuous chart:** $Z_0=1$ on the first monitoring day, with no reset after alarms and no restarts at events. λ = 0.1 is primary; λ = 0.2 is secondary and reported briefly |
| Alarms | An **exceedance day** has $Z_t>h^*$. An **episode** begins on a day with $Z_t>h^*\ge Z_{t-1}$ ($Z_0=1$) and lasts while $Z>h^*$ (`chart.episodes`). ARL₀ = 500 is a first-alarm target: it does not determine the expected number of continuous-chart episodes, and no episode-count benchmark is reported |
| Reference dates (D4) | For each date below: $Z_t/h^*$ on the date, whether an episode is active, and, within the **63 trading days** starting on the date, the first exceedance (days from the date), the number of exceedance days, the number of threshold crossings (episode starts), the maximum $Z/h^*$, and the mean score $u$. These are descriptive only: they are **not** detection delays, and the events are **not** verified change points. A date that is not a monitoring day stops the run; dates are never moved |
| Outputs | Tables S1–S5 (data and fits; limits and validation; exceedance days and episodes; reference-date states; forecast diagnostics: QLIKE and MSE against $r^2$, mean, median and ACF₁ of $u$, RF floor binds). Two figures: $Z_t/h^*$ for the three charts, and returns with the variance denominators. `frozen.json` is written before monitoring and checked afterwards; `monitor.csv` holds the daily series; all files are hashed |

**Frozen reference dates (D4).** These were selected retrospectively as major, well-documented US equity-market stress dates. They were verified against the sources below on 27 Oct 2026, before any SPY data or monitoring output existed. All nine were checked by web search of the cited sources. Entries 1, 2 and 8 were also confirmed by reading the cited page. The student should spot-check the list before the run. They are descriptive anchors, and their selection involves hindsight.

| # | Date | Event | Why it is a useful anchor | Source |
|---|---|---|---|---|
| 1 | 2007-08-09 | BNP Paribas suspends redemptions from three funds exposed to US subprime securitisations | Widely dated as the start of the 2007–09 crisis | Marketplace, "When did the financial crisis begin? Some say August 9, 2007 — in France", 9 Aug 2017 (marketplace.org/story/2017/08/09/…); contemporaneous: Marketplace, 9 Aug 2007, and NPR, 10 Aug 2007 |
| 2 | 2008-09-15 | Lehman Brothers files for Chapter 11 | The largest US bankruptcy; the acute phase of the crisis | Wikipedia, "Bankruptcy of Lehman Brothers" ("filed for Chapter 11 bankruptcy protection on Monday, September 15, 2008"); background: Bernanke, testimony of 20 Apr 2010 (federalreserve.gov) |
| 3 | 2010-05-06 | "Flash Crash" | An intraday market-wide liquidity collapse | SEC–CFTC joint staff report, *Findings Regarding the Market Events of May 6, 2010* (30 Sep 2010; sec.gov/files/marketevents-report.pdf) |
| 4 | 2011-08-08 | First trading session after S&P's downgrade of the US to AA+ (announced Fri 5 Aug 2011); S&P 500 about −6.7% | Sovereign-risk shock with a large one-day fall | CNNMoney, 8 Aug 2011 (money.cnn.com/2011/08/08/markets/markets_newyork/) |
| 5 | 2015-08-24 | China-led global sell-off; Dow −1,089 points in the first minutes | Global shock transmitted to US equities | Fortune, 24 Aug 2015 (fortune.com/2015/08/24/dow-plunges-1000-points-stocks-markets) |
| 6 | 2018-02-05 | Volatility shock: Dow −1,175 points, a record one-day VIX jump | A volatility-specific event after a long calm period | Bloomberg, "The Day the VIX Doubled", 6 Feb 2019 |
| 7 | 2020-02-24 | COVID-19 sell-off as cases spread outside China; Dow about −1,030 points | Onset of the 2020 crash | Fox Business / NPR, 24 Feb 2020 |
| 8 | 2024-08-05 | Global sell-off with the yen carry-trade unwind: S&P 500 down more than 3%, Nikkei down more than 12%, VIX at a four-year high | A short, sharp volatility spike | CNN, "Markets saw a massive shift this week. Here's what happened", 9 Aug 2024 |
| 9 | 2025-04-03 | Sell-off after the 2 April tariff announcement; S&P 500 −4.8% | Policy shock; the largest fall since 2020 at that time | Axios, 3 Apr 2025 |

From the earlier candidate list, 2007-02-27 (China-led sell-off) and 2016-06-24 (Brexit result) were **removed for concision** before any SPY data existed. Both are documented events, but they are less central to US equity volatility than those kept. No date was selected, removed or moved on the basis of chart outcomes.

**Carried over from the simulation:**
- the score (eq. 12), the EWMA (eq. 13), λ, the RF features, grid, floor and QLIKE selection
- the frozen-model protocol and the W = 250 history
- calibration by bisection, and validation by eq. 29

**Adapted, with the reasons recorded here:**
- chronological RF selection with a refit on all of training, since no independent development path exists
- a limit calibrated under a fitted real-data model
- a burn-in of 2,000
- continuous monitoring with episodes and reference-date states, instead of first-alarm run lengths
- no oracle chart, since the true parameters are unknown
- training-mean demeaning

**Post-stop refinement (v1.7, 27 Oct 2026; user-authorized, training data only).** The first SPY run stopped at the strict fourth-moment gate: the unrestricted fit had m4 1.0089 and implied variance 1.920, against s² 1.144. The SPY configuration now selects a **variance-targeted** GARCH-t: ω = s²(1 − α − β), with α, β and ν by ML, h₁ = s², and admissibility by parameterization (`forecast.fit_garch_vt`; `docs/spy_vt_remediation.md`). It removes the level mismatch at a likelihood cost of 0.24, but **still fails the fourth-moment condition** (m4 1.0039). Any finite-variance calibration option, its diagnostics and a relaunch need separate approval. References for variance targeting (Engle & Mezrich 1996; Francq, Horváth & Zakoïan 2011) are not yet in the library.

**Finite-variance calibration (v1.8, 27 Oct 2026; post-stop refinement; implemented and tested, not yet executed).** The user approved model B, the variance-targeted GARCH-t, as the fixed SPY specification. The choice rests on the training-data variance mismatch and the likelihood comparison, not on monitoring outcomes. The main reference for variance targeting is Francq, Horváth & Zakoïan (2011), with the method conventionally attributed to Engle & Mezrich (1996); both are bibliographic only (`references.md` [11], [12]).

Model B has a **finite unconditional variance** (α + β < 1) but **no finite unconditional fourth moment** (β² + 2αβ + κα² ≥ 1). Calibration and validation paths are therefore drawn with the simulator's explicit opt-in `need_m4=False`, used only when `finite_variance_simulation` is set (SPY configuration). That opt-in still requires ω > 0, α, β ≥ 0, α + β < 1 and ν > 2, refuses non-finite or non-positive simulated values, and never clips parameters. The production default is unchanged and bit-identical.

**Target.** h* is calibrated to the **restricted** mean run length $E[\min(T, 5000)] = 500$ (eqs. 15–16; a path without an alarm by day 5,000 counts 5,000). This is **not** the unrestricted ARL₀ = E[T], and the two are not claimed to be equal: the restricted mean is a lower bound on E[T], and the gap is controlled by the calibration-censoring criterion d. Independent validation uses the calibrated h* unchanged, judged by eq. 29 conditional on h*. Every failure is kept and disclosed.

**Diagnostics** (fixed in `run.SPY["diagnostics"]` before any calibration; recorded machine-readably in `results.json["diagnostics"]`):

| ID | Criterion | Action |
|---|---|---|
| a | ω > 0, α, β ≥ 0, α + β < 1, ν > 2 | stop |
| b | (α + β)^burn ≤ 10⁻³ (burn = 2,000) | stop |
| c | All simulated r, h, d and u finite and h > 0 | stop |
| d | Calibration censoring ≤ 0.01 per chart and λ (full precision) | stop before monitoring |
| e | h* finite and > 0; minimal (restricted ARL(h*) ≥ 500 > ARL(h*(1 − 10⁻⁶))); consistent restricted-mean computation; bracketing and bisection succeed | stop |
| e_overshoot | \|restricted ARL(h*)/500 − 1\| ≤ 10⁻³; exact overshoot, achieved restricted ARL and deviation recorded | warn (refined; see note) |
| f | Restricted ARL of each half of the calibration paths at the full-sample h* in [425, 575] (exact bounds) | warn only; never recalibrates |
| g | Eq. 29 on 2,000 independent validation paths | report and keep |
| h | Validation SE / restricted ARL ≤ 0.04 | warn |
| i | Run-length CV, quantiles and maximum of u, maximum h | descriptive |

**Note on e.** Criterion e refined (user decision, 27 Oct 2026, **before any SPY calibration**). These remain **hard stops**: a non-finite or non-positive h*, a failed minimality condition (restricted ARL(h*) ≥ 500 > restricted ARL(h*(1 − 10⁻⁶))), an inconsistent restricted-mean computation, and failed bracketing or bisection (`CalibrationError`). Only the overshoot |restricted ARL(h*)/500 − 1| > 10⁻³ became a **recorded warning** (`e_overshoot`), keeping the exact overshoot, achieved restricted ARL, target deviation and status in `results.json`. Justification: in the frozen production run, 24 of 160 calibrations exceeded 10⁻³ (maximum 0.16%) through the discreteness of the empirical ARL. There is no recalibration, no seed change and no selective rerun, and validation is unchanged.

**Interpretation limits.**
- Alarms are descriptive. They are **not** validated predictions of market events, alarm counts do not rank the methods, and they imply nothing about trading profitability.
- No trading or backtesting code is in scope.

## 12. Known limitations (to be stated in the report)

1. The DGP is correctly specified for GARCH (home advantage). The RF can at best tie in simulation.
2. Information is symmetric; the leverage effect is ignored by both forecasters.
3. Within-replicate results are conditional on the trained system; method-level statements rest on R = 20 training replicates (§10.2), with $n_{\text{train}}=3500$ and the simulated DGP.
4. The masking theory (20) is a first-order approximation.
5. The model-based SPY calibration assumes the training GARCH-t is the in-control law.
6. MacGregor & Harris (1993) and Lu & Reynolds (1999) are cited at metadata level only.
7. In-control validation (29) is conditional on each calibrated $h^*$, excludes calibration uncertainty, gives no family-wise coverage, and was adopted after the benchmark (§6).
