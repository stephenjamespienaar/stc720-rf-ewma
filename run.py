"""Experiment driver.

    python run.py smoke  [--out DIR]   tiny end-to-end run (< 1 min)
    python run.py pilot  [--out DIR]   reduced feasibility pilot (Phase 1)
    python run.py production           refuses until a configuration is approved
    python run.py verify [--out DIR]   runs smoke twice and compares result hashes

Normally launched through scripts/run_simulation.sh, which records wall/CPU
time, peak memory, logs and provenance. Refuses to write into a directory that
already holds experiment artifacts (the wrapper's provenance and log files are fine).
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

from src import chart, report, sim
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
}

CONFIGS = {
    "smoke": {**BASE, "n_train": 1000, "n_dev": 1000, "n_cal": 60, "n_val": 60, "n_ooc": 60, "t_max": 600,
              "target_arl": 50, "tau": 20, "H": 100, "deltas": [2.0], "lams": [0.1], "rf_trees": 20,
              "rf_leaf": [50, 200], "rf_max_features": [1], "sustained": [40, 99], "n_jobs": 4, "n_boot": 200},
    "pilot": {**BASE, "n_train": 3500, "n_dev": 3500, "n_cal": 300, "n_val": 300, "n_ooc": 300, "t_max": 3000,
              "target_arl": 500, "tau": 50, "H": 500, "deltas": [1.5, 2.0, 3.0], "lams": [0.1, 0.2],
              "sustained": [100, 499]},
    # Sized from measured pilot timings; requires the student's approval.
    "production": None,
}

# Files and directories run.py writes into an output directory; existing ones are never overwritten.
ARTIFACTS = ("config.json", "results.json", "tables.md", "fig_delay.png", "fig_profile.png",
             "verify.txt", "verify_a", "verify_b")
ROLES = {"train": 0, "dev": 1, "cal": 2, "val": 3, "ooc": 4, "rf": 5, "boot": 6}
CHARTS = ("conventional", "garch", "rf", "oracle")


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
    return [float(((x[:, L:] * x[:, :-L]).mean(axis=1) / v).mean()) for L in lags]


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


def replicate(cfg, rep, timer):
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
                                                             cfg["target_arl"], tau) for k in CHARTS}
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
    # false-alarm baseline and the paired denominator of the masking ratio (eq. 19).
    M = tau - 1 + H
    with timer("simulate_ooc"):
        r0, h0 = sim.simulate(p, cfg["n_ooc"], W + M, g["ooc"], cfg["burn"])
    out.update({"ooc": {}, "masking": {}, "profile": {}, "paired": {}})
    early, sus = cfg["early"], cfg["sustained"]
    base = {}
    for delta in [1.0, *cfg["deltas"]]:
        key = str(delta)
        r, _ = sim.scale_shift(r0, h0, W + tau - 1, delta)
        _, u, _ = scores(r, s2, gp, p, rf, cfg, timer, "ooc")
        out["profile"][key] = {k: [round(float(v), 5) for v in u[k][:, tau - 1:].mean(axis=0)] for k in CHARTS}
        uE = {k: chart.window_mean(u[k], tau, *early) for k in CHARTS}
        uS = {k: chart.window_mean(u[k], tau, *sus) for k in CHARTS}
        if delta == 1.0:
            base = {"uE": uE, "uS": uS}
        else:
            out["masking"][key] = {k: {"u0_incontrol": u0[k], "uE": uE[k], "uS": uS[k],
                                       "uE_ratio": uE[k] / base["uE"][k], "uS_ratio": uS[k] / base["uS"][k],
                                       "M": chart.masking_ratio(uS[k], base["uS"][k], delta)} for k in CHARTS}
            for k, pp in (("garch", gp), ("oracle", p)):
                out["masking"][key][k]["R_theory"], out["masking"][key][k]["M_theory"] = \
                    chart.garch_masking_theory(pp, p.var, delta)
        out["ooc"][key], out["paired"][key] = {}, {}
        with timer("ewma_ooc"):
            for lam in cfg["lams"]:
                res, dly = {}, {}
                for k in CHARTS:
                    z = chart.ewma(u[k], lam)
                    dly[k], cens = chart.delays(z, hstar[lam][k], tau, H)
                    res[k] = chart.delay_summary(dly[k], cens) | {
                        "occupancy_S": float((z[:, tau - 1 + sus[0]: tau + sus[1]] > hstar[lam][k]).mean())}
                out["ooc"][key][str(lam)] = res
                out["paired"][key][str(lam)] = {
                    f"{a} - {b}": chart.paired_diff(dly[a], dly[b], g["boot"], cfg["n_boot"])
                    for a, b in (("rf", "garch"), ("rf", "conventional"), ("garch", "conventional"))}

    # Frozen-model checks: nothing was refitted during monitoring.
    out["frozen_checks"] = {
        "rf_unchanged": rf_fingerprint == hashlib.sha256(
            b"".join(e.tree_.value.tobytes() for e in rf.estimators_)).hexdigest(),
        "garch_unchanged": garch_frozen == (gp.omega, gp.alpha, gp.beta, gp.nu)}
    return out


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
           "seeds": {"master_seed": cfg["master_seed"], "spawn_keys": {r: [rep, k] for rep in range(cfg["replicates"])
                                                                       for r, k in ROLES.items()}}}
    (out / "config.json").write_text(json.dumps({k: res[k] for k in ("mode", "config", "seeds")}, indent=1))
    with timer("total"):
        res["replicates"] = [replicate(cfg, rep, timer) for rep in range(cfg["replicates"])]
    res["timing"] = timer.stages
    res["environment"] = environment()
    res["results_sha256"] = results_hash(res)
    (out / "results.json").write_text(json.dumps(res, indent=1, default=float))
    report.write(res, out)
    print(f"[{mode}] done in {timer.stages['total']['wall']:.1f} s -> {out}  sha256={res['results_sha256'][:16]}")
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["smoke", "pilot", "production", "verify"])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = Path(a.out or f"results/runs/{a.mode}_{datetime.now():%Y%m%dT%H%M%S}")

    if a.mode == "production" and CONFIGS["production"] is None:
        sys.exit("Production configuration not yet approved: size it from the pilot report first.")
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
    run(a.mode, CONFIGS[a.mode], out)


if __name__ == "__main__":
    main()
