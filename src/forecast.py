"""Variance forecasters (methodology §4) and forecast losses (§9).

All forecasters are fitted once on training data and then frozen; their
forecasts update only through newly observed returns.
"""

from concurrent.futures import ThreadPoolExecutor

import numpy as np
from arch import arch_model
from sklearn.ensemble import RandomForestRegressor

from .sim import Garch, constraint_violations

LAGS = (1, 5, 22)
MAXLAG = max(LAGS)


def har_features(r):
    """x[..., t, :] = (r_{t-1}^2, mean r^2 over t-5..t-1, mean r^2 over t-22..t-1)
    (eq. 9). Built from r[..., :t] only; rows t < 22 contain NaN."""
    r2 = np.asarray(r, dtype=float) ** 2
    T = r2.shape[-1]
    c = np.concatenate([np.zeros(r2.shape[:-1] + (1,)), np.cumsum(r2, axis=-1)], axis=-1)
    x = np.full(r2.shape + (len(LAGS),), np.nan)
    for k, L in enumerate(LAGS):
        x[..., L:, k] = (c[..., L:T] - c[..., : T - L]) / L
    return x


def fit_garch(r):
    """Student-t maximum-likelihood GARCH(1,1) with zero mean, via `arch`.
    Returns the frozen parameters and fit diagnostics; raises if the fitted
    parameters violate positivity or stationarity."""
    res = arch_model(r, mean="Zero", vol="GARCH", p=1, q=1, dist="t", rescale=False).fit(disp="off")
    pr = res.params
    p = Garch(float(pr["omega"]), float(pr["alpha[1]"]), float(pr["beta[1]"]), float(pr["nu"]))
    info = {
        "convergence_flag": int(res.convergence_flag),
        "loglik": float(res.loglikelihood),
        "persistence": p.alpha + p.beta,
        "m4": float(p.m4),
        "near_boundary": bool(p.alpha + p.beta >= 0.995 or p.alpha < 1e-4),
    }
    v = constraint_violations(p, need_m4=False)
    if v or info["convergence_flag"] != 0:
        raise RuntimeError(f"GARCH fit unusable: violations={v}, info={info}")
    return p, info


def garch_filter(r, p):
    """hhat[..., t] = omega + alpha r_{t-1}^2 + beta hhat[..., t-1] (eq. 8), i.e. the
    forecast of r_t^2 from r[..., :t], started at the fitted unconditional variance."""
    r2d = np.asarray(r, dtype=float).reshape(-1, np.shape(r)[-1])
    hh = np.empty_like(r2d)
    hv = np.full(r2d.shape[0], p.var)
    for t in range(r2d.shape[1]):
        hh[:, t] = hv
        hv = p.omega + p.alpha * r2d[:, t] ** 2 + p.beta * hv
    return hh.reshape(np.shape(r))


def fit_rf(r, min_samples_leaf, max_features, n_trees, seed, n_jobs=1):
    """Squared-error random forest of r_t^2 on x_t (eqs. 9-10), fitted on one
    training path (rows t >= 22)."""
    x = har_features(r)[MAXLAG:]
    y = np.asarray(r, dtype=float)[MAXLAG:] ** 2
    rf = RandomForestRegressor(
        n_estimators=n_trees,
        min_samples_leaf=min_samples_leaf,
        max_features=max_features,
        bootstrap=True,
        random_state=seed,
        n_jobs=n_jobs,
    )
    return rf.fit(x, y)


def predict_rf(rf, x, floor, n_jobs=1, chunk=100_000):
    """Floored forest forecast (eq. 11) for features x[..., 3].

    Trees are summed in a fixed order within each row chunk (chunks run in
    threads), so results do not depend on thread scheduling.
    Returns (forecast, number of floor binds)."""
    X = np.ascontiguousarray(x.reshape(-1, x.shape[-1]), dtype=np.float32)
    if not np.isfinite(X).all():
        raise ValueError("non-finite features passed to the forest")

    def part(sl):
        acc = np.zeros(sl.stop - sl.start)
        for est in rf.estimators_:
            acc += est.predict(X[sl], check_input=False)
        return acc / len(rf.estimators_)

    slices = [slice(i, min(i + chunk, len(X))) for i in range(0, len(X), chunk)]
    with ThreadPoolExecutor(max(1, n_jobs)) as ex:
        f = np.concatenate(list(ex.map(part, slices)))
    binds = int((f < floor).sum())
    return np.maximum(f, floor).reshape(x.shape[:-1]), binds


def qlike(p, f):
    """QLIKE loss log f + p/f (Patton 2011 eq. 6): p = proxy or true variance, f = forecast."""
    return np.log(f) + p / f


def mse(p, f):
    """MSE loss (p - f)^2 (Patton 2011 eq. 5)."""
    return (p - f) ** 2


def slope(f, p):
    """OLS slope of forecast f on target p, cov(f, p)/var(p) (methodology §9).
    Both moments share one normalisation, which cancels."""
    p = np.ravel(p) - np.mean(p)
    return float(p @ np.ravel(f) / (p @ p))
