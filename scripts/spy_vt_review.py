"""SPY variance-targeting review (training data only; 27 Oct 2026, post-stop refinement).

Compares, on the frozen pre-2007 SPY training returns only:
  A   the unrestricted GARCH(1,1)-t ML fit used by the stopped run (`arch`, backcast start)
  A'  the unrestricted fit under this project's likelihood (h_1 = s^2), for a like-for-like
      likelihood comparison with B (diagnostic only; not a candidate estimator)
  B   the variance-targeted fit, omega = s^2 (1 - alpha - beta) (forecast.fit_garch_vt)
The snapshot is sliced to prices dated <= 2006-12-29 before any return is formed: no
monitoring return is computed. No simulation, no calibration, no chart.

    .venv/bin/python scripts/spy_vt_review.py
"""

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import scipy  # noqa: E402
from scipy import stats  # noqa: E402
from scipy.optimize import minimize  # noqa: E402
from scipy.special import expit, logit  # noqa: E402

import run  # noqa: E402
from src import forecast as fc  # noqa: E402
from src import sim, spy  # noqa: E402

SNAP = ROOT / "data/raw/SPY.csv"
STOPPED = ROOT / "results/runs/spy_20261027T045319_117125/results.json"
OUT = ROOT / "results/derived/spy_vt_review"
CFG = run.SPY


def unrestricted_same_likelihood(x, s2, start):
    """A': omega free (log-parameterized), same likelihood and h_1 = s^2 as the targeted fit."""
    def unpack(z):
        pers = expit(z[1])
        a = pers * expit(z[2])
        return np.exp(z[0]), a, pers - a, 2 + np.exp(z[3])

    def nll(z):
        return fc.garch_t_nll(x, *unpack(z), s2)[0] / len(x)
    p = start
    z0 = [np.log(p.omega), logit(p.alpha + p.beta), logit(p.alpha / (p.alpha + p.beta)), np.log(p.nu - 2)]
    o = minimize(nll, z0, method="BFGS", options={"gtol": 1e-7, "maxiter": 5000})
    return sim.Garch(*(float(v) for v in unpack(o.x))), o


def describe(name, p, x, s2, info, ll_arch=None):
    nll, h = fc.garch_t_nll(x, p.omega, p.alpha, p.beta, p.nu, s2)
    u = x**2 / h
    z = x / np.sqrt(h)
    m = sim.moments(p)
    return {"name": name, "omega": p.omega, "alpha": p.alpha, "beta": p.beta, "nu": p.nu,
            "persistence": p.alpha + p.beta, "implied_var": p.var, "train_s2": s2, "implied_over_s2": p.var / s2,
            **m, "loglik_project_h1_s2": -nll, "loglik_arch_backcast": ll_arch,
            "optimizer": info, "train_mean_h": float(h.mean()), "train_mean_u": float(u.mean()),
            "train_median_u": float(np.median(u)), "train_qlike_proxy": float(fc.qlike(x**2, h).mean()),
            "train_acf1_u": float(np.corrcoef(u[1:], u[:-1])[0, 1]), "train_excess_kurtosis_z": float(stats.kurtosis(z)),
            "train_min_h": float(h.min()), "train_max_h": float(h.max()), "h_last_training_day": float(h[-1])}, h


def main():
    if OUT.exists():
        sys.exit(f"refusing to overwrite {OUT}")
    close = spy.load_snapshot(SNAP)                                     # SHA-256 checked against SPY.meta.json
    sha = hashlib.sha256(SNAP.read_bytes()).hexdigest()
    assert sha.startswith("7cd6d400b798c5e7"), sha
    close = close[close.index <= pd.Timestamp(CFG["train_end"])]       # training prices only, from here on
    r = spy.log_returns(close)
    r = r[r.index >= pd.Timestamp(CFG["train_start"])]
    mu = float(r.mean())
    x = (r - mu).to_numpy()
    s2 = float(np.mean(x**2))
    stopped = json.loads(STOPPED.read_text())
    checks = {"training prices end 2006-12-29": str(close.index.max().date()) == CFG["train_end"],
              "n_train equals stopped run (3507)": len(x) == stopped["data"]["n_train"] == 3507,
              "training mean equals stopped run": mu == stopped["data"]["train_mean"],
              "s2 equals stopped run": s2 == stopped["fit"]["s2"]}

    pA, iA = fc.fit_garch(x)
    g = stopped["fit"]["garch"]
    checks["unrestricted fit reproduces the stopped run exactly"] = (pA.omega, pA.alpha, pA.beta, pA.nu) == (
        g["omega"], g["alpha"], g["beta"], g["nu"])
    pB, iB = fc.fit_garch_vt(x, s2)
    pA2, oA2 = unrestricted_same_likelihood(x, s2, pA)
    iA2 = {"success": bool(oA2.success), "message": str(oA2.message), "nit": int(oA2.nit),
           "grad_norm": float(np.linalg.norm(oA2.jac))}

    A, hA = describe("A: unrestricted ML (arch)", pA, x, s2, iA, iA["loglik"])
    A2, hA2 = describe("A': unrestricted ML, project likelihood (h1 = s2)", pA2, x, s2, iA2)
    B, hB = describe("B: variance-targeted ML", pB, x, s2, iB)
    checks["B targets s2 exactly"] = abs(pB.var / s2 - 1) < 1e-12
    checks["B optimum agrees across starts"] = iB["n_at_best"] >= 6 and iB["max_param_spread_at_best"] < 1e-3
    lr = 2 * (A2["loglik_project_h1_s2"] - B["loglik_project_h1_s2"])
    sub = {f"{a}–{b}": float(np.mean(x[(r.index >= a) & (r.index <= b)] ** 2))
           for a, b in (("1993-02-01", "1999-12-31"), ("2000-01-01", "2003-12-31"), ("2004-01-01", "2006-12-29"))}
    res = {"label": "post-stop methodological refinement; training data only; no calibration, no monitoring",
           "snapshot_sha256": sha, "n_train": len(x), "train_mean": mu, "train_s2": s2,
           "subperiod_mean_r2": sub, "fits": [A, A2, B],
           "loglik_difference_A_prime_minus_B": lr / 2, "twice_loglik_difference": lr,
           "corr_h_A_B": float(np.corrcoef(hA, hB)[0, 1]), "mean_ratio_h_A_over_B": float(np.mean(hA / hB)),
           "checks": checks}
    OUT.mkdir(parents=True)
    (OUT / "vt_review.json").write_text(json.dumps(res, indent=1, default=float))

    f = lambda v, d=4: "–" if v is None else (f"{v:.{d}f}" if isinstance(v, float) else str(v))  # noqa: E731
    rows = [("ω", "omega", 5), ("α", "alpha", 4), ("β", "beta", 4), ("ν", "nu", 2), ("α + β", "persistence", 4),
            ("Implied unconditional variance", "implied_var", 3), ("Training s²", "train_s2", 3),
            ("Implied / s²", "implied_over_s2", 3), ("Fourth-moment coefficient β²+2αβ+κα²", "m4", 4), ("κ = E η⁴", "kappa", 3),
            ("Finite variance", "finite_variance", 0), ("Finite fourth moment", "finite_fourth_moment", 0),
            ("Strict simulator gate (ν > 4, m4 ≤ 0.99)", "strict_gate", 0), ("Half-life (days)", "half_life_days", 0),
            ("Log-likelihood, project convention (h₁ = s²)", "loglik_project_h1_s2", 2),
            ("Log-likelihood, arch (backcast)", "loglik_arch_backcast", 2),
            ("Training mean ĥ", "train_mean_h", 3), ("Training mean u = r²/ĥ", "train_mean_u", 3),
            ("Training median u", "train_median_u", 3), ("Training QLIKE (proxy r²)", "train_qlike_proxy", 4),
            ("Training ACF₁ of u", "train_acf1_u", 3), ("Excess kurtosis of r/√ĥ", "train_excess_kurtosis_z", 2),
            ("Min / max ĥ", None, 3), ("ĥ on 2006-12-29", "h_last_training_day", 3)]
    md = ["# SPY variance-targeting review (training data only)", "",
          f"Snapshot `{sha[:16]}…`; {len(x)} training returns 1993-02-01 to 2006-12-29; mean {mu:.5f}%, s² {s2:.4f}.", "",
          "| Quantity | " + " | ".join(F["name"] for F in res["fits"]) + " |", "|---|---|---|---|"]
    for lab, k, d in rows:
        if k is None:
            md.append(f"| {lab} | " + " | ".join(f"{F['train_min_h']:.3f} / {F['train_max_h']:.3f}" for F in res["fits"]) + " |")
        else:
            md.append(f"| {lab} | " + " | ".join(f(F[k], d) if not isinstance(F[k], bool) else ("yes" if F[k] else "no")
                                               for F in res["fits"]) + " |")
    md += ["", f"Twice the log-likelihood difference A′ − B (same likelihood and start): {lr:.2f} (descriptive; s² is "
               "estimated, so a χ²₁ reference is only approximate).",
           f"corr(ĥ_A, ĥ_B) over training = {res['corr_h_A_B']:.4f}; mean ĥ_A/ĥ_B = {res['mean_ratio_h_A_over_B']:.3f}.",
           "Sub-period mean r²: " + ", ".join(f"{k} {v:.3f}" for k, v in sub.items()) + ".", "",
           "Optimizer, B: " + json.dumps({k: iB[k] for k in ("convergence_flag", "message", "nit", "grad_norm", "n_starts",
                                                          "n_converged", "n_at_best", "max_param_spread_at_best",
                                                          "objective_range_converged")}),
           "Optimizer, A′: " + json.dumps(iA2), "Optimizer, A (arch): " + json.dumps(
               {k: iA[k] for k in ("convergence_flag", "loglik", "near_boundary")}), "",
           "Checks: " + json.dumps(checks)]
    (OUT / "vt_review.md").write_text("\n".join(md) + "\n")
    git = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    (OUT / "provenance.txt").write_text("\n".join([
        f"run_at: {datetime.now(timezone.utc).isoformat()}", f"git_head: {git} (plus uncommitted variance-targeting code)",
        f"python: {platform.python_version()}  numpy: {np.__version__}  scipy: {scipy.__version__}",
        f"script_sha256: {hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}",
        f"forecast.py_sha256: {hashlib.sha256((ROOT / 'src/forecast.py').read_bytes()).hexdigest()}",
        f"snapshot_sha256: {sha}", ""]))
    print("\n".join(md))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
