"""Equal-weight aggregation over independently trained replicates (methodology §10.2, eqs. 27-28).

The method-level estimand is theta = E_r[theta_r], the mean over independently
trained and calibrated systems of a quantity defined conditionally on one
system. Paths are never pooled across replicates: inference uses the
between-replicate SD s_b. Only the quantities listed in schema() are aggregated.
Not identifiable values are None throughout.
"""

import numpy as np
from scipy import stats


def across(values, ses=None):
    """Replicate mean, range, every value, sign counts and, for R >= 2: the
    between-replicate SD s_b, the 95% interval mean ± t_{R-1,0.975} s_b/sqrt(R)
    (eq. 27) and an exact two-sided sign test. Given the within-replicate Monte
    Carlo SEs w_r: rms_mc_se = sqrt(mean w_r^2) and the residual between-system
    variance var_between_resid = max(0, s_b^2 - mean w_r^2) (eq. 28): variability
    from training, model selection, forest randomness and calibration, after
    subtracting the estimated evaluation Monte Carlo variance. A descriptive
    method-of-moments approximation, not an identified decomposition of training
    uncertainty."""
    x = np.asarray(values, dtype=float)
    R = len(x)
    s = {"R": R, "mean": float(x.mean()), "min": float(x.min()), "max": float(x.max()), "values": x.tolist(),
         "n_pos": int((x > 0).sum()), "n_neg": int((x < 0).sum())}
    if ses is not None:
        s["rms_mc_se"] = float(np.sqrt(np.mean(np.square(ses))))
    if R < 2:
        return s
    sb = float(x.std(ddof=1))
    half = float(stats.t.ppf(0.975, R - 1)) * sb / np.sqrt(R)
    s |= {"sd_between": sb, "ci95": [s["mean"] - half, s["mean"] + half]}
    if s["n_pos"] + s["n_neg"]:
        s["sign_p"] = float(stats.binomtest(s["n_pos"], s["n_pos"] + s["n_neg"]).pvalue)
    if ses is not None:
        s["var_between_resid"] = max(0.0, sb**2 - s["rms_mc_se"] ** 2)
        s["sd_between_resid"] = float(np.sqrt(s["var_between_resid"]))
    return s


def get(d, path):
    for k in path:
        d = d[k]
    return d


def schema(cfg, charts, pairs):
    """Explicit allowlist of what is aggregated across replicates:
    estimands as (path, sibling SE key or None); flags (booleans, counted over
    replicates); counts (listed with their range, never averaged as estimands).
    Seeds, convergence codes, the RF grid and other metadata are not aggregated.
    Quantities that are zero by construction (X(k) and excess occupancy at
    delta = 1) are omitted."""
    lams = [str(x) for x in cfg["lams"]]
    deltas = [str(x) for x in [1.0, *cfg["deltas"]]]
    ks = cfg["ks"]
    est, flags, counts = [(("s2_train",), None)], [], [("floor_binds",)]
    est += [(("garch_fit", k), None) for k in ("omega", "alpha", "beta", "nu", "persistence")]
    flags += [("garch_fit", "near_boundary"), ("frozen_checks", "rf_unchanged"), ("frozen_checks", "garch_unchanged")]
    for c in charts:
        est += [(("forecast_diag", c, k), None) for k in ("qlike_true", "qlike_proxy", "mse_true", "mean_u", "u_q99")]
        est += [(("forecast_diag", c, "acf_u", f"lag{L}"), None) for L in (1, 5, 22)]
        if c != "conventional":
            est += [(("forecast_diag", c, k), None) for k in ("corr_h", "slope_h")]
    est += [(("forecast_diag", c, "gap_closure"), None) for c in ("garch", "rf")]
    for lam in lams:
        for c in charts:
            est += [(("calibration", lam, c, "h"), None), (("validation", lam, c, "censored"), None)]
            est += [(("validation", lam, c, k), f"se_{k}") for k in ("arl_restricted", "p_lt_tau")]
            flags.append(("validation", lam, c, "passed"))
        est.append((("brook_evans_oracle", lam, "arl_markov"), None))
    for d in deltas:
        shift = d != "1.0"
        mean_keys = ["p_prechange_fa", "rmd", "censored", *[f"p_d_le_{k}" for k in ks], "occupancy_S"]
        mean_keys += [*[f"x_{k}" for k in ks], "occupancy_excess"] if shift else []
        for lam in lams:
            for c in charts:
                est += [(("ooc", d, lam, c, k), f"se_{k}") for k in mean_keys]
                est += [(("ooc", d, lam, c, k), None) for k in ("q25_d", "median_d", "q75_d", "p_late_given_gt20")]
                counts.append(("ooc", d, lam, c, "n_eval"))
            for a, b in pairs:
                for m in ["dH", *([f"x_{k}" for k in ks] if shift else [])]:
                    est.append((("paired", d, lam, f"{a} - {b}", m, "mean"), "se_mean"))
                    counts.append(("paired", d, lam, f"{a} - {b}", m, "n"))
        if shift:
            for c in charts:
                est += [(("masking", d, c, k), f"se_{k}") for k in ("uS_ratio", "uE_ratio", "M")]
            est += [(("masking", d, c, "M_theory"), None) for c in ("garch", "oracle")]
    return {"estimands": est, "flags": flags, "counts": counts}


def collect(reps, sch):
    """Aggregate the schema's paths over the replicate result dicts (equal weights).
    Keys are the '/'-joined paths. An estimand that is None in any replicate is
    listed per replicate without statistics; Monte Carlo SEs enter only if every
    replicate has one."""
    est = {}
    for path, se in sch["estimands"]:
        vals = [get(r, path) for r in reps]
        if any(v is None for v in vals):
            est["/".join(path)] = {"values": vals, "note": "not identifiable in every replicate"}
            continue
        ses = None if se is None else [get(r, path[:-1]).get(se) for r in reps]
        est["/".join(path)] = across(vals, None if ses is None or None in ses else ses)
    flags = {"/".join(p): {"n_true": sum(bool(get(r, p)) for r in reps), "R": len(reps)} for p in sch["flags"]}
    counts = {}
    for p in sch["counts"]:
        v = [get(r, p) for r in reps]
        counts["/".join(p)] = {"values": v, "min": min(v), "max": max(v)}
    return {"estimands": est, "flags": flags, "counts": counts}
