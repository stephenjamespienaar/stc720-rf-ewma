"""One-sided EWMA chart, censored run lengths, calibration, validation,
out-of-control delays, paired contrasts and adaptation-masking metrics
(methodology §5-8).

Monitoring day t (1-based) is column t-1; a change at day tau affects
columns tau-1 onwards. Out-of-control paths have M = tau - 1 + H monitored
days. An alarm on day M is the last observable detection (D = H); a path
without an alarm by day M is right-censored and its alarm day is coded
M + 1 (D > H). For tau = 50, H = 500: day 549 is a detection, 550 is censored.

An estimate stored under key x carries its Monte Carlo SE under se_x.
"""

import numpy as np
from scipy.signal import lfilter


def mean_se(name, x):
    """{name: mean, se_name: sd/sqrt(n)} of per-path values x (Monte Carlo SE, ddof = 1;
    for 0/1 values this is the binomial SE times sqrt(n/(n-1)))."""
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return {name: None, f"se_{name}": None}
    return {name: float(x.mean()), f"se_{name}": float(x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else None}


def ewma(u, lam, z0=1.0):
    """Z_t = lam u_t + (1 - lam) Z_{t-1}, Z_0 = z0, along axis 1 (eq. 13)."""
    u = np.atleast_2d(u)
    zi = np.full((u.shape[0], 1), (1.0 - lam) * z0)
    z, _ = lfilter([lam], [1.0, -(1.0 - lam)], u, axis=1, zi=zi)
    return z


def first_alarm(z, h):
    """Alarm time T = inf{t: Z_t > h} (eq. 14), 1-based, and censoring flag.
    Censored paths get T = number of monitored days."""
    exceed = z > h
    hit = exceed.any(axis=1)
    t = np.where(hit, exceed.argmax(axis=1) + 1, z.shape[1])
    return t, ~hit


def alarm_days(z, h):
    """Alarm day T (1-based) per path; a path without an alarm in its n monitored
    days is right-censored and coded n + 1, so an alarm on day n stays distinct."""
    t, cens = first_alarm(z, h)
    return np.where(cens, z.shape[1] + 1, t)


def calibrate(z, target, rtol=1e-7):
    """h* = min{h: restricted ARL(h) >= target} (eqs. 15-16) by bisection on
    fixed in-control paths. Run lengths are nondecreasing in h path-wise."""
    n, m = z.shape
    if m < target:
        raise ValueError("monitoring horizon shorter than target ARL")
    cm = np.maximum.accumulate(z, axis=1)

    def arl(h):
        return np.minimum((cm <= h).sum(axis=1) + 1, m).mean()

    lo, hi = 0.0, float(cm[:, -1].max()) + 1.0
    while hi - lo > rtol * hi:
        mid = 0.5 * (lo + hi)
        if arl(mid) >= target:
            hi = mid
        else:
            lo = mid
    return hi, float(arl(hi))


def validate(z, h, target, tau, tol=0.15):
    """In-control run-length summary on independent paths with h fixed (§6)."""
    t, cens = first_alarm(z, h)
    arl = t.mean()
    se = t.std(ddof=1) / np.sqrt(len(t))
    q10, q50, q90 = np.quantile(t, [0.1, 0.5, 0.9])
    lo, hi = arl - 1.96 * se, arl + 1.96 * se
    return {
        "arl_restricted": float(arl),
        "se_arl_restricted": float(se),
        "ci95": [float(lo), float(hi)],
        "censored": float(cens.mean()),
        "q10": float(q10),
        "q50": float(q50),
        "q90": float(q90),
        "p_le_250": float((t <= 250).mean()),
        **mean_se("p_lt_tau", t < tau),
        "passed": bool(lo <= target <= hi and abs(arl / target - 1) <= tol),
    }


def delays_from_days(T, tau, H):
    """Restricted delay D_H = min(T - tau + 1, H) (eq. 17) from alarm days coded as
    in alarm_days over M = tau - 1 + H monitored days; NaN for pre-change false
    alarms (T < tau). Censored iff T = M + 1; an alarm on day M has D = H and is a
    detection. Also returns the censoring flags."""
    T = np.asarray(T)
    if (T > tau + H).any() or (T < 1).any():
        raise ValueError(f"alarm days must lie in 1 .. {tau + H} (censored = {tau + H})")
    cens = T > tau - 1 + H
    d = np.minimum(T - tau + 1, H).astype(float)
    d[T < tau] = np.nan
    return d, cens


def delays(z, h, tau, H):
    """Per-path restricted delay D_H = min(T - tau + 1, H) (eq. 17); NaN for
    pre-change false alarms (T < tau). Also returns the censoring flags."""
    if z.shape[1] != tau - 1 + H:
        raise ValueError("out-of-control paths must have tau - 1 + H monitored days")
    return delays_from_days(alarm_days(z, h), tau, H)


def detected(d, cens, k):
    """Per-path indicator 1{D <= k} of an alarm within k days of the change (float);
    censored paths (D > H) are never detections; NaN for pre-change false alarms."""
    return np.where(np.isnan(d), np.nan, (d <= k) & ~cens)


def cond_quantile(d, cens, p):
    """p-quantile of the delay D given T >= tau: inverted empirical CDF over the
    evaluable paths, i.e. the ceil(p n)-th smallest detected delay (integer days).
    Censored paths count in n but are never treated as detections; None when fewer
    than ceil(p n) paths alarmed within H (quantile not identifiable, eq. 25)."""
    ok = ~np.isnan(d)
    det = np.sort(d[ok & ~cens])
    j = int(np.ceil(p * ok.sum()))
    return float(det[j - 1]) if 1 <= j <= len(det) else None


def delay_summary(d, cens, early=20, base=None, ks=(5, 20, 60)):
    """Out-of-control summary over the evaluable paths E = {T >= tau} (§7), with
    Monte Carlo SEs. base = (d, cens) of the same paths without the change
    (delta = 1) adds the paired excess detection X(k) (eq. 24); E must then be the
    same in both, as common random numbers before the change guarantee.
    The key set never depends on the data: with no evaluable path (n_eval = 0)
    every conditional estimate and SE is None (not identifiable), and only
    p_prechange_fa, which uses all paths, is reported."""
    ok = ~np.isnan(d)
    if base is not None and not np.array_equal(np.isnan(base[0]), ~ok):
        raise ValueError("CRN pairing broken: pre-change false alarms differ from the no-change counterfactual")
    dd, cc = d[ok], cens[ok]
    s = {"n_eval": int(ok.sum()), **mean_se("p_prechange_fa", ~ok), **mean_se("rmd", dd), **mean_se("censored", cc)}
    for k in ks:
        hit = detected(d, cens, k)
        s |= mean_se(f"p_d_le_{k}", hit[ok])
        if base is not None:
            s |= mean_se(f"x_{k}", (hit - detected(*base, k))[ok])
    for name, p in (("q25_d", 0.25), ("median_d", 0.5), ("q75_d", 0.75)):
        s[name] = cond_quantile(d, cens, p)
    late = dd > early
    s["p_late_given_gt20"] = float((late & ~cc).sum() / late.sum()) if late.any() else None
    return s


def paired_diff(a, b, rng=None, n_boot=0):
    """Mean paired difference a - b of per-path values over the paths where both are
    defined (non-NaN; for delays E_a ∩ E_b, CRN), with the normal paired SE
    sd(diff)/sqrt(n) and its 95% CI (eq. 23). n_boot > 0 adds a percentile-bootstrap
    CI over paths as a check. Not identifiable parts are None: everything if
    n = 0; the SE and intervals if n = 1."""
    ok = ~np.isnan(a) & ~np.isnan(b)
    n = int(ok.sum())
    diff = a[ok] - b[ok]
    s = mean_se("mean", diff) | {"n": n, "ci95": [None, None]}
    if n < 2:
        return s
    s["ci95"] = [s["mean"] - 1.96 * s["se_mean"], s["mean"] + 1.96 * s["se_mean"]]
    if n_boot:
        boot = diff[rng.integers(0, n, (n_boot, n))].mean(axis=1)
        s["boot_ci95"] = [float(q) for q in np.quantile(boot, [0.025, 0.975])]
    return s


def window_mean(a, tau, k0, k1):
    """Per-path mean of a over days tau+k0 .. tau+k1 (inclusive)."""
    return a[:, tau - 1 + k0 : tau + k1].mean(axis=1)


def ratio_se(a, b):
    """R = mean(a)/mean(b) for paired per-path values, with the delta-method SE
    sqrt(sum_i (a_i - R b_i)^2 / (N (N - 1))) / mean(b) (eq. 26)."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    n, r = len(a), a.mean() / b.mean()
    return float(r), float(np.sqrt(((a - r * b) ** 2).sum() / (n * (n - 1))) / b.mean())


def masking_ratio(u_s, u_0, delta):
    """M = (u_S/u_0 - 1)/(delta - 1) (eq. 19)."""
    return (u_s / u_0 - 1.0) / (delta - 1.0)


def garch_masking_theory(p_hat, var, delta):
    """First-order prediction R_G and M_G for the frozen GARCH filter (eq. 20)."""
    r_g = delta * (p_hat.omega + p_hat.alpha * var) / (p_hat.omega + p_hat.alpha * delta * var)
    return r_g, (r_g - 1.0) / (delta - 1.0)


def brook_evans_arl(cdf, lam, h, z0=1.0, m=500):
    """Markov-chain (Brook-Evans) approximation to the ARL of the upper EWMA
    (eqs. 13-14) for iid nonnegative input with distribution function `cdf`."""
    w = h / m
    mid = (np.arange(m) + 0.5) * w
    edges = np.arange(m + 1) * w
    a = (edges[None, :] - (1.0 - lam) * mid[:, None]) / lam
    F = np.where(a > 0, cdf(np.maximum(a, 0.0)), 0.0)
    Q = np.diff(F, axis=1)
    arl = np.linalg.solve(np.eye(m) - Q, np.ones(m))
    return float(arl[min(int(z0 / w), m - 1)])
