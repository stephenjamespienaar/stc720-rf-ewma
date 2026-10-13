"""One-sided EWMA chart, censored run lengths, calibration, validation,
out-of-control delays and adaptation-masking metrics (methodology §5-8).

Monitoring day t (1-based) is column t-1; a change at day tau affects
columns tau-1 onwards.
"""

import numpy as np
from scipy.signal import lfilter


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
        "se": float(se),
        "ci95": [float(lo), float(hi)],
        "censored": float(cens.mean()),
        "q10": float(q10),
        "q50": float(q50),
        "q90": float(q90),
        "p_le_250": float((t <= 250).mean()),
        "p_lt_tau": float((t < tau).mean()),
        "passed": bool(lo <= target <= hi and abs(arl / target - 1) <= tol),
    }


def delays(z, h, tau, H):
    """Per-path restricted delay D_H = min(T - tau + 1, H) (eq. 17); NaN for
    pre-change false alarms (T < tau). Also returns the censoring flags."""
    if z.shape[1] != tau - 1 + H:
        raise ValueError("out-of-control paths must have tau - 1 + H monitored days")
    t, cens = first_alarm(z, h)
    d = np.where(cens, H, t - tau + 1).astype(float)
    d[t < tau] = np.nan
    return d, cens


def delay_summary(d, cens, early=20):
    """Summary of restricted delays (§7); labelled 'restricted to H' downstream."""
    ok = ~np.isnan(d)
    if not ok.any():
        return {"p_prechange_fa": 1.0, "n_eval": 0}
    dd, cc = d[ok], cens[ok]
    late = dd > early
    return {
        "p_prechange_fa": float(1 - ok.mean()),
        "n_eval": int(ok.sum()),
        "mean_dH": float(dd.mean()),
        "se_dH": float(dd.std(ddof=1) / np.sqrt(len(dd))),
        "median_d": float(np.median(dd)) if cc.mean() < 0.5 else None,
        "p_d_le_5": float(((dd <= 5) & ~cc).mean()),
        "p_d_le_20": float(((dd <= 20) & ~cc).mean()),
        "p_d_le_60": float(((dd <= 60) & ~cc).mean()),
        "p_late_given_gt20": float((late & ~cc).sum() / late.sum()) if late.any() else None,
        "censored": float(cc.mean()),
    }


def paired_diff(d_a, d_b, rng, n_boot=2000):
    """Mean paired difference of restricted delays (a - b) over paths where
    neither chart false-alarmed before the change, with a bootstrap 95% CI."""
    ok = ~np.isnan(d_a) & ~np.isnan(d_b)
    if not ok.any():
        return {"mean": None, "ci95": [None, None], "n": 0}
    diff = d_a[ok] - d_b[ok]
    idx = rng.integers(0, len(diff), (n_boot, len(diff)))
    boot = diff[idx].mean(axis=1)
    lo, hi = np.quantile(boot, [0.025, 0.975])
    return {"mean": float(diff.mean()), "ci95": [float(lo), float(hi)], "n": int(ok.sum())}


def window_mean(a, tau, k0, k1):
    """Mean over paths and over days tau+k0 .. tau+k1 (inclusive) of a[:, ...]."""
    return float(a[:, tau - 1 + k0 : tau + k1].mean())


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
