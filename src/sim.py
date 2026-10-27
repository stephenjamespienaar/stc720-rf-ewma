"""GARCH(1,1) simulation with standardized Student-t innovations and the
persistent volatility-scale fault (methodology eqs. 2-6)."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Garch:
    omega: float
    alpha: float
    beta: float
    nu: float

    @property
    def var(self):
        """Unconditional variance omega/(1-alpha-beta) (eq. 5)."""
        return self.omega / (1.0 - self.alpha - self.beta)

    @property
    def kappa(self):
        """E[eta^4] of the standardized t innovation; infinite for nu <= 4."""
        return 3.0 * (self.nu - 2.0) / (self.nu - 4.0) if self.nu > 4 else np.inf

    @property
    def m4(self):
        """Fourth-moment coefficient beta^2 + 2 alpha beta + kappa alpha^2 (eq. 5)."""
        return self.beta**2 + 2 * self.alpha * self.beta + self.kappa * self.alpha**2


def constraint_violations(p, need_m4=True, m4_margin=0.99):
    """List of violated constraints (methodology §2 table); empty if all hold."""
    v = []
    if not p.omega > 0:
        v.append("omega > 0")
    if not (p.alpha >= 0 and p.beta >= 0):
        v.append("alpha, beta >= 0")
    if not p.alpha + p.beta < 1:
        v.append("alpha + beta < 1")
    if not p.nu > 2:
        v.append("nu > 2")
    if need_m4:
        if not p.nu > 4:
            v.append("nu > 4")
        elif not p.m4 <= m4_margin:
            v.append(f"m4 = {p.m4:.4f} <= {m4_margin}")
    return v


def moments(p):
    """Which moments the fitted law has (methodology §2): finite variance iff alpha + beta < 1
    (then E log(beta + alpha eta^2) <= log(alpha + beta) < 0 by Jensen, so the process is also
    strictly stationary); finite E r^4 iff nu > 4 and m4 < 1; the production simulator's
    strict gate additionally needs m4 <= 0.99. Descriptive; changes no default."""
    second = bool(p.alpha + p.beta < 1)
    fourth = bool(p.nu > 4 and p.m4 < 1)
    return {"finite_variance": second, "finite_fourth_moment": fourth, "m4": float(p.m4), "kappa": float(p.kappa),
            "strict_gate": not constraint_violations(p),
            "half_life_days": float(np.log(0.5) / np.log(p.alpha + p.beta)) if second and p.alpha + p.beta > 0 else None}


def check(p, **kw):
    v = constraint_violations(p, **kw)
    if v:
        raise ValueError(f"GARCH constraints violated for {p}: {v}")
    return p


def std_t(rng, nu, size):
    """Student-t draws scaled to unit variance (eq. 4)."""
    return rng.standard_t(nu, size) * np.sqrt((nu - 2.0) / nu)


def simulate(p, n_paths, n, rng, burn=500, need_m4=True):
    """Simulate (n_paths, n) returns r and true conditional variances h.

    h[:, t] is the variance of r[:, t] given the past; the first `burn`
    observations (started at the unconditional variance) are discarded.
    need_m4=True (default; production) enforces the strict constraints, including
    nu > 4 and the fourth-moment margin. need_m4=False is an explicit opt-in used only
    by the SPY application (methodology §11, post-stop refinement): it still requires
    omega > 0, alpha, beta >= 0, alpha + beta < 1 and nu > 2 (finite variance) but allows
    an infinite fourth moment, and it refuses non-finite or non-positive simulated values.
    Parameters are never clipped.
    """
    check(p, need_m4=need_m4)
    eta = std_t(rng, p.nu, (n_paths, burn + n))
    r = np.empty_like(eta)
    h = np.empty_like(eta)
    hv = np.full(n_paths, p.var)
    for t in range(burn + n):
        h[:, t] = hv
        r[:, t] = np.sqrt(hv) * eta[:, t]
        hv = p.omega + p.alpha * r[:, t] ** 2 + p.beta * hv
    if not need_m4 and not (np.isfinite(r).all() and np.isfinite(h).all() and (h > 0).all()):
        raise FloatingPointError("finite-variance simulation produced non-finite or non-positive values")
    return r[:, burn:], h[:, burn:]


def scale_shift(r, h, start, delta):
    """Persistent scale fault (eq. 6): r -> sqrt(delta) r and h -> delta h from
    column `start` on. Equivalent to GARCH(delta*omega, alpha, beta) after the
    change (Schipper & Schmid 2001, eq. 3 with a = 0, Delta = sqrt(delta))."""
    r, h = r.copy(), h.copy()
    r[:, start:] *= np.sqrt(delta)
    h[:, start:] *= delta
    return r, h
