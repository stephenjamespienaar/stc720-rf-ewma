"""Experiment driver.

    python run.py smoke  [--out DIR]   tiny end-to-end run, 2 replicates (< 1 min)
    python run.py pilot  [--out DIR]   reduced feasibility pilot (Phase 1, historical)
    python run.py verify [--out DIR]   runs smoke twice and compares result hashes
    python run.py production         --approved [--out DIR]   primary simulation (R = 20, ARL0 = 500)
    python run.py sensitivity_arl100 --approved [--out DIR]   secondary ARL0 = 100 sensitivity
    python run.py benchmark          --approved [--out DIR]   production-scale performance benchmark (R = 1)
    python run.py spy                --approved [--out DIR]   SPY real-data application (methodology §11)

The last four refuse to start without --approved. The flag is a technical
safeguard against accidental launches; it never replaces the student's explicit
authorization of each run.

Normally launched through scripts/run_simulation.sh, which records wall/CPU
time, peak memory, logs and provenance. Refuses to write into a directory that
already holds experiment artifacts (the wrapper's provenance and log files are fine).
Writes config.json (before computing), results.json, paths.npz (per-path
outputs), tables.md and figures.
"""

import argparse
import contextlib
import hashlib
import json
import platform
import resource
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy import stats

from src import aggregate, application, chart, report, sim
from src import forecast as fc

DGP = {"omega": 0.02, "alpha": 0.07, "beta": 0.91, "nu": 6.0}  # default D1, methodology §2

BASE = {
    "master_seed": 20261013,
    "dgp": DGP,
    "burn": 500,
    "warmup": 250,
    "floor_c": 1e-4,
    "rf_trees": 100,
    "rf_leaf": [50, 200, 800],
    "rf_max_features": [1, 3],
    "early": [0, 19],
    "n_boot": 2000,
    "n_jobs": 16,
    "replicates": 1,
    "ks": [5, 20, 60],
    # Primary endpoints (methodology §7.4): paired contrasts of these metrics for these
    # pairs, at this lambda and every delta in the config, each with its delta = 1 counterpart.
    "primary": {"lam": 0.1, "pairs": ["rf - garch", "rf - conventional"], "metrics": ["dH", "x_20"],
                "label": "pre-specified after the exploratory pilot, before production"},
    # In-control validation rule (methodology §6, eq. 29), recorded in config.json before any computation.
    "ic_validation": {"tol": 0.15,
                      "rule": "pass iff the independent-validation 95% CI lies within [A0(1 - tol), A0(1 + tol)]",
                      "label": "post-pilot, post-benchmark methodological amendment made before production (user "
                               "decision, 14 Oct 2026); the pilot and the benchmark were judged by the original rule "
                               "(A0 inside the 95% CI and |A_val/A0 - 1| <= tol)"},
}

# Production sizes (production-plan.md); seed 20261014 keeps production evidence disjoint from the pilot's.
PRODUCTION = {**BASE, "master_seed": 20261014, "n_train": 3500, "n_dev": 3500, "n_cal": 2000, "n_val": 2000,
              "n_ooc": 2000, "t_max": 5000, "target_arl": 500, "tau": 50, "H": 500, "deltas": [1.5, 2.0, 3.0],
              "lams": [0.1, 0.2], "sustained": [100, 499], "rf_trees": 500, "replicates": 20}

CONFIGS = {
    "smoke": {**BASE, "n_train": 1000, "n_dev": 1000, "n_cal": 60, "n_val": 60, "n_ooc": 60, "t_max": 600,
              "target_arl": 50, "tau": 20, "H": 100, "deltas": [2.0], "lams": [0.1], "rf_trees": 20,
              "rf_leaf": [50, 200], "rf_max_features": [1], "sustained": [40, 99], "n_jobs": 4, "n_boot": 200,
              "replicates": 2},
    "pilot": {**BASE, "n_train": 3500, "n_dev": 3500, "n_cal": 300, "n_val": 300, "n_ooc": 300, "t_max": 3000,
              "target_arl": 500, "tau": 50, "H": 500, "deltas": [1.5, 2.0, 3.0], "lams": [0.1, 0.2],
              "sustained": [100, 499]},
    # Guarded modes: each run needs the student's explicit authorization and --approved.
    "production": {**PRODUCTION, "label": "primary production simulation (ARL0 = 500)"},
    "sensitivity_arl100": {**PRODUCTION, "target_arl": 100,
                           "label": "secondary sensitivity: ARL0 = 100 with the production seed, models and paths; "
                                    "limits calibrated and validated separately on the same matched paths, so it is "
                                    "matched to production, not an independent experiment"},
    "benchmark": {**PRODUCTION, "replicates": 1, "master_seed": 20261013,
                  "label": "production-scale performance benchmark (R = 1, seed 20261013); not a reproduction of "
                           "the original pilot; excluded from the primary production inference and from the "
                           "ARL0 = 100 sensitivity results"},
}
GUARDED = ("production", "sensitivity_arl100", "benchmark", "spy")

# SPY application (methodology §11; user decisions D1-D6, 27 Oct 2026). Reference dates were verified
# against the cited sources and frozen before any SPY monitoring output existed.
SPY = {
    "master_seed": 20261028, "ticker": "SPY", "snapshot": "data/raw/SPY.csv",
    "first_price": "1993-01-29", "download_end_exclusive": "2026-10-01",
    "train_start": "1993-02-01", "dev_start": "2004-01-01", "train_end": "2006-12-29",
    "monitor_start": "2007-01-03", "monitor_end": "2026-09-30", "expected_rows": [8480, 8490],
    "burn": 2000, "warmup": 250, "floor_c": 1e-4, "rf_trees": 500, "rf_leaf": [50, 200, 800], "rf_max_features": [1, 3],
    "n_jobs": 16, "n_cal": 2000, "n_val": 2000, "t_max": 5000, "target_arl": 500, "tau": 50,
    "lams": [0.1, 0.2], "primary_lam": 0.1, "event_window": 63,
    "ic_validation": {"tol": 0.15, "rule": BASE["ic_validation"]["rule"],
                      "label": "eq. 29, applied to validation paths simulated from the fitted SPY GARCH-t"},
    "reference_dates": [
        {"date": "2007-08-09", "event": "BNP Paribas suspends three ABS funds"},
        {"date": "2008-09-15", "event": "Lehman Brothers Chapter 11 filing"},
        {"date": "2010-05-06", "event": "Flash Crash"},
        {"date": "2011-08-08", "event": "first session after the S&P US downgrade"},
        {"date": "2015-08-24", "event": "China-led global sell-off"},
        {"date": "2018-02-05", "event": "volatility shock (record VIX jump)"},
        {"date": "2020-02-24", "event": "COVID-19 sell-off as cases spread outside China"},
        {"date": "2024-08-05", "event": "yen carry-trade unwind sell-off"},
        {"date": "2025-04-03", "event": "sell-off after the 2 April tariff announcement"},
    ],
    "label": "SPY real-data application: illustrative and descriptive; limits from simulation under the fitted "
             "1993-2006 GARCH(1,1)-t, which favours GARCH",
}
CONFIGS["spy"] = SPY

# Files and directories run.py writes into an output directory; existing ones are never overwritten.
ARTIFACTS = ("config.json", "results.json", "paths.npz", "tables.md", "fig_delay.png", "fig_profile.png",
             "fig_replicates.png", "verify.txt", "verify_a", "verify_b", "frozen.json", "monitor.csv",
             "fig_spy_charts.png", "fig_spy_variance.png")
ROLES = {"train": 0, "dev": 1, "cal": 2, "val": 3, "ooc": 4, "rf": 5, "boot": 6}
CHARTS = ("conventional", "garch", "rf", "oracle")
PAIRS = (("rf", "garch"), ("rf", "conventional"), ("garch", "conventional"))


class Timer:
    """Per-stage wall time, process CPU time and cumulative peak RSS."""

    def __init__(self):
        self.stages = {}

    @contextlib.contextmanager
    def __call__(self, name):
        w, c = time.perf_counter(), time.process_time()
        yield
        t = self.stages.setdefault(name, {"wall": 0.0, "cpu": 0.0})
        t["wall"] += time.perf_counter() - w
        t["cpu"] += time.process_time() - c
        # ru_maxrss is in KiB on Linux, so this value is MiB (key name kept for existing results.json files)
        t["peak_rss_mb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def streams(cfg, rep):
    """Independent generators per experimental role (methodology §10)."""
    return {role: np.random.default_rng(np.random.SeedSequence(cfg["master_seed"], spawn_key=(rep, k)))
            for role, k in ROLES.items()}


def acf(u, lags=(1, 5, 22)):
    """Average within-path autocorrelation of u at the given lags."""
    x = u - u.mean(axis=1, keepdims=True)
    v = (x**2).mean(axis=1)
    return {f"lag{L}": float(((x[:, L:] * x[:, :-L]).mean(axis=1) / v).mean()) for L in lags}


def scores(r, s2, gp, p_true, rf, cfg, timer, tag):
    """Monitoring-period denominators d and scores u = r^2/d for every chart
    (eq. 12). r has W + M columns; outputs have the last M columns. The
    diagnostic 'oracle' is the GARCH filter with the true in-control
    parameters (known, frozen), which equals h_t while the process is in control."""
    W = cfg["warmup"]
    d = {"conventional": np.full(r[:, W:].shape, s2)}
    with timer(f"garch_filter_{tag}"):
        d["garch"] = fc.garch_filter(r, gp)[:, W:]
        d["oracle"] = fc.garch_filter(r, p_true)[:, W:]
    with timer(f"rf_predict_{tag}"):
        d["rf"], binds = fc.predict_rf(rf, fc.har_features(r)[:, W:], cfg["floor_c"] * s2, cfg["n_jobs"])
    r2 = r[:, W:] ** 2
    u = {k: r2 / v for k, v in d.items()}
    for k, v in u.items():
        if not np.isfinite(v).all():
            raise FloatingPointError(f"non-finite score for {k} ({tag})")
    return d, u, binds


def replicate(cfg, rep, timer, paths=None):
    """One independently trained system: train, calibrate, validate, evaluate.
    Returns a JSON-serializable dict; if `paths` is a dict, the per-path arrays
    (see evaluate) are added to it under keys r{rep}_{name}."""
    p = sim.check(sim.Garch(**cfg["dgp"]))
    g = streams(cfg, rep)
    W, tau, H = cfg["warmup"], cfg["tau"], cfg["H"]
    out = {"dgp_var": p.var, "dgp_m4": p.m4}

    # --- training and development paths (roles 1-2)
    with timer("simulate_train_dev"):
        r_tr = sim.simulate(p, 1, cfg["n_train"], g["train"], cfg["burn"])[0][0]
        r_dev, h_dev = (a[0] for a in sim.simulate(p, 1, cfg["n_dev"] + fc.MAXLAG, g["dev"], cfg["burn"]))
    s2 = float(np.mean(r_tr**2))
    out["s2_train"] = s2
    with timer("garch_fit"):
        gp, ginfo = fc.fit_garch(r_tr)
    out["garch_fit"] = {"omega": gp.omega, "alpha": gp.alpha, "beta": gp.beta, "nu": gp.nu, **ginfo}

    x_dev, y_dev, h_dev = fc.har_features(r_dev)[fc.MAXLAG:], r_dev[fc.MAXLAG:] ** 2, h_dev[fc.MAXLAG:]
    rf_seed = int(g["rf"].integers(2**31 - 1))
    out["rf_seed"] = rf_seed
    grid = []
    with timer("rf_fit_grid"):
        for leaf in cfg["rf_leaf"]:
            for mf in cfg["rf_max_features"]:
                m = fc.fit_rf(r_tr, leaf, mf, cfg["rf_trees"], rf_seed, cfg["n_jobs"])
                f, _ = fc.predict_rf(m, x_dev, cfg["floor_c"] * s2, cfg["n_jobs"])
                grid.append({"min_samples_leaf": leaf, "max_features": mf,
                             "dev_qlike": float(fc.qlike(y_dev, f).mean()), "model": m})
    best = min(grid, key=lambda d: d["dev_qlike"])
    rf = best["model"]
    out["rf_grid"] = [{k: v for k, v in d.items() if k != "model"} | {"selected": d is best} for d in grid]
    hh_dev = fc.garch_filter(r_dev, gp)[fc.MAXLAG:]
    out["dev_qlike_ref"] = {"conventional": float(fc.qlike(y_dev, s2).mean()),
                            "garch": float(fc.qlike(y_dev, hh_dev).mean()),
                            "oracle": float(fc.qlike(y_dev, h_dev).mean())}
    rf_fingerprint = hashlib.sha256(b"".join(e.tree_.value.tobytes() for e in rf.estimators_)).hexdigest()
    garch_frozen = (gp.omega, gp.alpha, gp.beta, gp.nu)

    # --- calibration (role 3)
    with timer("simulate_cal"):
        r_cal, h_cal = sim.simulate(p, cfg["n_cal"], W + cfg["t_max"], g["cal"], cfg["burn"])
    _, u_cal, _ = scores(r_cal, s2, gp, p, rf, cfg, timer, "cal")
    del r_cal, h_cal
    hstar, out["calibration"] = {}, {}
    with timer("ewma_calibrate"):
        for lam in cfg["lams"]:
            hstar[lam], out["calibration"][str(lam)] = {}, {}
            for k in CHARTS:
                z = chart.ewma(u_cal[k], lam)
                h, arl = chart.calibrate(z, cfg["target_arl"])
                hstar[lam][k] = h
                out["calibration"][str(lam)][k] = {"h": h, "arl_cal": arl,
                                                   "censored_cal": float(chart.first_alarm(z, h)[1].mean())}
    del u_cal

    # --- independent in-control validation (role 4) and forecast diagnostics
    with timer("simulate_val"):
        r_val, h_val = sim.simulate(p, cfg["n_val"], W + cfg["t_max"], g["val"], cfg["burn"])
    d_val, u_val, binds = scores(r_val, s2, gp, p, rf, cfg, timer, "val")
    out["floor_binds"], out["floor_rows"] = binds, int(d_val["rf"].size)
    out["validation"] = {}
    with timer("ewma_validate"):
        for lam in cfg["lams"]:
            out["validation"][str(lam)] = {k: chart.validate(chart.ewma(u_val[k], lam), hstar[lam][k],
                                                             cfg["target_arl"], tau, cfg["ic_validation"]["tol"])
                                          for k in CHARTS}
    h_true, r2 = h_val[:, W:], r_val[:, W:] ** 2
    fd = {}
    for k in CHARTS:
        dk, uk = d_val[k], u_val[k]
        fd[k] = {"qlike_true": float(fc.qlike(h_true, dk).mean()), "qlike_proxy": float(fc.qlike(r2, dk).mean()),
                 "mse_true": float(fc.mse(h_true, dk).mean()),
                 "corr_h": float(np.corrcoef(dk.ravel(), h_true.ravel())[0, 1]) if k != "conventional" else None,
                 # < 1: forecast varies less than proportionally with h (cause not identified; methodology §9)
                 "slope_h": fc.slope(dk, h_true) if k != "conventional" else None,
                 "mean_u": float(uk.mean()), "u_q50": float(np.quantile(uk, 0.5)),
                 "u_q99": float(np.quantile(uk, 0.99)), "u_q999": float(np.quantile(uk, 0.999)),
                 "u_max": float(uk.max()), "acf_u": acf(uk)}
    for k in ("garch", "rf"):
        fd[k]["gap_closure"] = (fd["conventional"]["qlike_true"] - fd[k]["qlike_true"]) / (
            fd["conventional"]["qlike_true"] - fd["oracle"]["qlike_true"])
    out["forecast_diag"] = fd
    u0 = {k: fd[k]["mean_u"] for k in CHARTS}

    # Oracle input is iid eta^2: independent Markov-chain check of the calibration machinery.
    nu = p.nu

    def cdf_eta2(x):
        return 2.0 * stats.t.cdf(np.sqrt(x * nu / (nu - 2.0)), nu) - 1.0

    out["brook_evans_oracle"] = {
        str(lam): {"arl_markov": chart.brook_evans_arl(cdf_eta2, lam, hstar[lam]["oracle"]),
                   "arl_cal": out["calibration"][str(lam)]["oracle"]["arl_cal"],
                   "arl_val": out["validation"][str(lam)]["oracle"]["arl_restricted"]} for lam in cfg["lams"]}
    del r_val, h_val, d_val, u_val

    # --- out-of-control evaluation (role 5), CRN across delta and charts.
    # delta = 1 is the no-change counterfactual of the same paths: it gives the
    # false-alarm baseline, X(k) and the paired denominator of the masking ratio (eq. 19).
    M = tau - 1 + H
    deltas = [1.0, *cfg["deltas"]]
    n, nd, nl, nc = cfg["n_ooc"], len(deltas), len(cfg["lams"]), len(CHARTS)
    pp = {"T": np.empty((nd, nl, nc, n), np.int32), "occ": np.empty((nd, nl, nc, n), np.int32),
          "uS": np.empty((nd, nc, n)), "uE": np.empty((nd, nc, n))}
    with timer("simulate_ooc"):
        r0, h0 = sim.simulate(p, n, W + M, g["ooc"], cfg["burn"])
    out["profile"] = {}
    early, sus = cfg["early"], cfg["sustained"]
    for i, delta in enumerate(deltas):
        r, _ = sim.scale_shift(r0, h0, W + tau - 1, delta)
        _, u, _ = scores(r, s2, gp, p, rf, cfg, timer, "ooc")
        out["profile"][str(delta)] = {k: [round(float(v), 5) for v in u[k][:, tau - 1:].mean(axis=0)] for k in CHARTS}
        for m, k in enumerate(CHARTS):
            pp["uE"][i, m] = chart.window_mean(u[k], tau, *early)
            pp["uS"][i, m] = chart.window_mean(u[k], tau, *sus)
        with timer("ewma_ooc"):
            for j, lam in enumerate(cfg["lams"]):
                for m, k in enumerate(CHARTS):
                    z = chart.ewma(u[k], lam)
                    pp["T"][i, j, m] = chart.alarm_days(z, hstar[lam][k])
                    pp["occ"][i, j, m] = (z[:, tau - 1 + sus[0]: tau + sus[1]] > hstar[lam][k]).sum(axis=1)
    with timer("evaluate"):
        out.update(evaluate(pp, cfg, g["boot"]))
    for key, mk in out["masking"].items():
        for k in CHARTS:
            mk[k]["u0_incontrol"] = u0[k]
        for k, pk in (("garch", gp), ("oracle", p)):
            mk[k]["R_theory"], mk[k]["M_theory"] = chart.garch_masking_theory(pk, p.var, float(key))
    out["perpath_sha256"] = perpath_hash(pp)
    if paths is not None:
        paths.update({f"r{rep}_{k}": v for k, v in pp.items()})

    # Frozen-model checks: nothing was refitted during monitoring.
    out["frozen_checks"] = {
        "rf_unchanged": rf_fingerprint == hashlib.sha256(
            b"".join(e.tree_.value.tobytes() for e in rf.estimators_)).hexdigest(),
        "garch_unchanged": garch_frozen == (gp.omega, gp.alpha, gp.beta, gp.nu)}
    return out


def evaluate(pp, cfg, rng):
    """Out-of-control estimators of one replicate (C2-C3), computed only from its
    per-path arrays. Detection, occupancy and empirical masking statistics can
    therefore be recomputed from paths.npz; the bootstrap intervals additionally
    need the same config (n_boot) and the replicate's fresh bootstrap stream,
    streams(cfg, rep)["boot"]. Daily score profiles are not reconstructible (only
    their path averages are stored in results.json). Arrays:
      T[delta, lam, chart, path]   alarm day, coded as in chart.alarm_days
                                   (M = tau - 1 + H monitored days; M + 1 = censored)
      occ[delta, lam, chart, path] days in the sustained window with Z > h*
      uS, uE[delta, chart, path]   per-path mean score in the sustained / early window
    Index 0 of the delta axis is delta = 1, the no-change counterfactual of the
    same CRN paths. Paired contrasts use the paths evaluable for both charts."""
    tau, H, ks = cfg["tau"], cfg["H"], cfg["ks"]
    n_sus = cfg["sustained"][1] - cfg["sustained"][0] + 1
    res = {"ooc": {}, "paired": {}, "masking": {}}
    for i, delta in enumerate([1.0, *cfg["deltas"]]):
        key = str(delta)
        res["ooc"][key], res["paired"][key] = {}, {}
        for j, lam in enumerate(cfg["lams"]):
            summ, per = {}, {}
            for m, k in enumerate(CHARTS):
                d, c = chart.delays_from_days(pp["T"][i, j, m], tau, H)
                base = chart.delays_from_days(pp["T"][0, j, m], tau, H)
                occ, occ0 = pp["occ"][i, j, m] / n_sus, pp["occ"][0, j, m] / n_sus
                summ[k] = (chart.delay_summary(d, c, base=base, ks=ks) | chart.mean_se("occupancy_S", occ)
                           | chart.mean_se("occupancy_excess", occ - occ0))
                per[k] = {"dH": d} | {f"x_{q}": chart.detected(d, c, q) - chart.detected(*base, q) for q in ks}
            res["ooc"][key][str(lam)] = summ
            res["paired"][key][str(lam)] = {
                f"{a} - {b}": {mt: chart.paired_diff(per[a][mt], per[b][mt], rng, cfg["n_boot"]) for mt in per[a]}
                for a, b in PAIRS}
        if i:
            res["masking"][key] = {}
            for m, k in enumerate(CHARTS):
                rs, se_rs = chart.ratio_se(pp["uS"][i, m], pp["uS"][0, m])
                re, se_re = chart.ratio_se(pp["uE"][i, m], pp["uE"][0, m])
                res["masking"][key][k] = {"uS": float(pp["uS"][i, m].mean()), "uE": float(pp["uE"][i, m].mean()),
                                          "uS_ratio": rs, "se_uS_ratio": se_rs, "uE_ratio": re, "se_uE_ratio": se_re,
                                          "M": chart.masking_ratio(rs, 1.0, delta), "se_M": se_rs / (delta - 1.0)}
    return res


def perpath_hash(pp):
    return hashlib.sha256(b"".join(f"{k}{pp[k].dtype}{pp[k].shape}".encode() + np.ascontiguousarray(pp[k]).tobytes()
                                   for k in sorted(pp))).hexdigest()


def save_paths(path, paths):
    np.savez_compressed(path, **paths)


def load_paths(path, rep):
    """Per-path arrays of replicate `rep` from paths.npz, keyed as in evaluate()."""
    with np.load(path) as f:
        return {k.split("_", 1)[1]: f[k] for k in f.files if k.startswith(f"r{rep}_")}


def environment():
    import arch
    import joblib
    import matplotlib
    import pandas
    import scipy
    import sklearn

    mods = {m.__name__: m.__version__ for m in (np, scipy, pandas, sklearn, arch, joblib, matplotlib)}
    return {"python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
            "packages": mods, "argv": sys.argv}


def results_hash(res):
    core = {k: v for k, v in res.items() if k not in ("timing", "environment", "results_sha256", "started")}
    return hashlib.sha256(json.dumps(core, sort_keys=True, default=float).encode()).hexdigest()


def refuse_overwrite(out):
    found = [n for n in ARTIFACTS if (Path(out) / n).exists()]
    if found:
        raise FileExistsError(f"refusing to overwrite experiment artifacts in {out}: {', '.join(found)}")


def run(mode, cfg, out):
    out = Path(out)
    refuse_overwrite(out)
    out.mkdir(parents=True, exist_ok=True)
    timer = Timer()
    res = {"mode": mode, "config": cfg, "started": datetime.now().isoformat(timespec="seconds"),
           "seeds": {"master_seed": cfg["master_seed"],
                     "spawn_keys": {str(rep): {r: [rep, k] for r, k in ROLES.items()} for rep in range(cfg["replicates"])}}}
    (out / "config.json").write_text(json.dumps({k: res[k] for k in ("mode", "config", "seeds")}, indent=1))
    paths = {}
    with timer("total"):
        res["replicates"] = [replicate(cfg, rep, timer, paths) for rep in range(cfg["replicates"])]
    M = cfg["tau"] - 1 + cfg["H"]
    res["perpath_axes"] = {
        "file": "paths.npz", "keys": "r{replicate}_{T|occ|uS|uE}", "T": ["delta", "lam", "chart", "path"],
        "occ": ["delta", "lam", "chart", "path"], "uS": ["delta", "chart", "path"], "uE": ["delta", "chart", "path"],
        "delta": [1.0, *cfg["deltas"]], "lam": cfg["lams"], "chart": list(CHARTS),
        "T_coding": f"1-based alarm day over M = tau - 1 + H = {M} monitored days; T = {M} is the last observable "
                    f"detection (D = H); T = {M + 1} = right-censored (no alarm by day {M}); T < tau = pre-change alarm",
        "occ_coding": f"days with Z > h* in the sustained window k in {cfg['sustained']}",
        "uS_uE": f"per-path mean score u over the sustained window {cfg['sustained']} / early window {cfg['early']}"}
    res["aggregate"] = aggregate.collect(res["replicates"], aggregate.schema(cfg, CHARTS, PAIRS))
    save_paths(out / "paths.npz", paths)
    res["timing"] = timer.stages
    res["environment"] = environment()
    res["results_sha256"] = results_hash(res)
    (out / "results.json").write_text(json.dumps(res, indent=1, default=float))
    report.write(res, out)
    print(f"[{mode}] done in {timer.stages['total']['wall']:.1f} s -> {out}  sha256={res['results_sha256'][:16]}")
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=[*CONFIGS, "verify"])
    ap.add_argument("--out", default=None)
    ap.add_argument("--approved", action="store_true",
                    help=f"required for {', '.join(GUARDED)}; pass it only after the student has explicitly "
                         "authorized this specific run")
    a = ap.parse_args()
    if a.mode in GUARDED and not a.approved:
        sys.exit(f"{a.mode} refused: it requires --approved, given only after the student's explicit "
                 "authorization of this run. Nothing was run or written.")
    out = Path(a.out or f"results/runs/{a.mode}_{datetime.now():%Y%m%dT%H%M%S}")
    try:
        refuse_overwrite(out)
    except FileExistsError as e:
        sys.exit(str(e))
    if a.mode == "verify":
        h1 = run("smoke", CONFIGS["smoke"], out / "verify_a")["results_sha256"]
        h2 = run("smoke", CONFIGS["smoke"], out / "verify_b")["results_sha256"]
        ok = h1 == h2
        (out / "verify.txt").write_text(f"run_a {h1}\nrun_b {h2}\nidentical {ok}\n")
        print(f"[verify] identical results: {ok}")
        sys.exit(0 if ok else 1)
    if a.mode == "spy":
        sys.exit(run_spy(CONFIGS["spy"], out))
    run(a.mode, CONFIGS[a.mode], out)


def run_spy(cfg, out, root="."):
    """SPY application (src/application.py): config.json first, then results.json with a
    results hash. Exit status 3 if the fitted GARCH-t fails the strict fourth-moment gate
    (nothing calibrated, no monitoring return used)."""
    out = Path(out)
    refuse_overwrite(out)
    out.mkdir(parents=True, exist_ok=True)
    timer = Timer()
    res = {"mode": "spy", "config": cfg, "started": datetime.now().isoformat(timespec="seconds"),
           "seeds": {"master_seed": cfg["master_seed"], "spawn_keys": {k: [v] for k, v in application.ROLES.items()}}}
    (out / "config.json").write_text(json.dumps({k: res[k] for k in ("mode", "config", "seeds")}, indent=1))
    with timer("total"):
        res.update(application.run(cfg, out, root))
    res["timing"] = timer.stages
    res["environment"] = environment()
    res["results_sha256"] = results_hash(res)
    (out / "results.json").write_text(json.dumps(res, indent=1, default=float))
    print(f"[spy] {res['status']} in {timer.stages['total']['wall']:.1f} s -> {out}  sha256={res['results_sha256'][:16]}")
    return 0 if res["status"] == "complete" else 3


if __name__ == "__main__":
    main()
