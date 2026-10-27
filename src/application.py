"""SPY real-data application (methodology §11). Illustrative and descriptive only.

The pipeline runs in this order, and the monitoring returns are first used in step 5:
  1. snapshot  load the frozen adjusted-price file (SHA-256 checked); S1 integrity checks
  2. returns   percent log returns, chronological split, training-only demeaning
  3. fit       s^2; GARCH(1,1)-t; RF grid fitted on 1993-2003 and selected by QLIKE on
               2004-2006 (all training), the selected cell refitted on 1993-2006; all frozen
  4. limits    strict fourth-moment gate (sim.constraint_violations, unchanged); then h* by
               simulation from the fitted GARCH-t with the frozen SPY forecasters, and an
               independent validation (eq. 29); written to frozen.json
  5. monitor   continuous EWMA over 2007-2026 (Z_0 = 1, no resets); denominators update
               sequentially from past returns only; parameters, trees, s^2 and h* fixed
"""

import hashlib
import json
from fractions import Fraction
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import chart, sim, spy  # noqa: E402
from . import forecast as fc  # noqa: E402

CHARTS = ("conventional", "garch", "rf")
LABEL = {"conventional": "Conventional EWMA", "garch": "GARCH–EWMA", "rf": "RF–EWMA"}
ROLES = {"rf": 0, "cal": 1, "val": 2}


def streams(cfg):
    """Independent generators per role from the SPY master seed."""
    return {k: np.random.default_rng(np.random.SeedSequence(cfg["master_seed"], spawn_key=(v,))) for k, v in ROLES.items()}


def fingerprint(rf):
    return hashlib.sha256(b"".join(e.tree_.value.tobytes() for e in rf.estimators_)).hexdigest()


def returns(close, cfg):
    """Training and monitoring returns with the agreed boundaries (stops if they do not hold)."""
    r = spy.log_returns(close)
    train, monitor, mu = spy.split(r[r.index >= pd.Timestamp(cfg["train_start"])], cfg["train_end"], cfg["monitor_start"])
    monitor = monitor[monitor.index <= pd.Timestamp(cfg["monitor_end"])]
    between = r[(r.index > pd.Timestamp(cfg["train_end"])) & (r.index < pd.Timestamp(cfg["monitor_start"]))]
    problems = [m for m, ok in [
        (f"first training return {train.index[0].date()} != {cfg['train_start']}", train.index[0] == pd.Timestamp(cfg["train_start"])),
        (f"last training return {train.index[-1].date()} != {cfg['train_end']}", train.index[-1] == pd.Timestamp(cfg["train_end"])),
        (f"first monitoring return {monitor.index[0].date()} != {cfg['monitor_start']}",
         monitor.index[0] == pd.Timestamp(cfg["monitor_start"])),
        (f"returns between training and monitoring: {list(map(str, between.index.date))}", between.empty)] if not ok]
    if problems:
        raise ValueError(f"SPY window boundaries do not hold: {problems}")
    return train, monitor, mu


def fit(train, cfg, rf_seed):
    """Training-only fits (step 3)."""
    r = train.to_numpy()
    s2 = float(np.mean(r**2))
    # The variance-targeted fit (post-stop refinement, methodology §11) only when explicitly selected.
    if cfg.get("garch_estimator", "mle") == "variance_targeted":
        gp, ginfo = fc.fit_garch_vt(r, s2)
    else:
        gp, ginfo = fc.fit_garch(r)
        ginfo = {"estimator": "mle", **ginfo}
    dev = (train.index >= pd.Timestamp(cfg["dev_start"])).nonzero()[0]
    x, floor = fc.har_features(r), cfg["floor_c"] * s2
    grid = []
    for leaf in cfg["rf_leaf"]:
        for mf in cfg["rf_max_features"]:
            m = fc.fit_rf(r[: dev[0]], leaf, mf, cfg["rf_trees"], rf_seed, cfg["n_jobs"])
            f, _ = fc.predict_rf(m, x[dev], floor, cfg["n_jobs"])
            grid.append({"min_samples_leaf": leaf, "max_features": mf, "dev_qlike": float(fc.qlike(r[dev] ** 2, f).mean())})
    best = min(grid, key=lambda d: d["dev_qlike"])
    for d in grid:
        d["selected"] = d is best
    rf = fc.fit_rf(r, best["min_samples_leaf"], best["max_features"], cfg["rf_trees"], rf_seed, cfg["n_jobs"])
    return {"s2": s2, "gp": gp, "garch_info": ginfo, "rf": rf, "rf_grid": grid, "rf_seed": rf_seed,
            "n_fit_rf_selection": int(dev[0]), "n_dev": int(len(dev)), "dev_first": str(train.index[dev[0]].date())}


def scores(r, s2, gp, rf, cfg):
    """Denominators and scores u = r^2/d over the last columns after a W-day history (eq. 12)."""
    W = cfg["warmup"]
    r = np.atleast_2d(r)
    d = {"conventional": np.full(r[:, W:].shape, s2), "garch": fc.garch_filter(r, gp)[:, W:]}
    d["rf"], binds = fc.predict_rf(rf, fc.har_features(r)[:, W:], cfg["floor_c"] * s2, cfg["n_jobs"])
    u = {k: r[:, W:] ** 2 / v for k, v in d.items()}
    if not all(np.isfinite(v).all() for v in u.values()):
        raise FloatingPointError("non-finite score")
    return d, u, binds


class CalibrationError(Exception):
    """Numerical bracketing or bisection of h* failed (diagnostic e, hard stop)."""


def limits(f, cfg, g):
    """h* by bisection on simulated in-control paths from the fitted GARCH-t, then an
    independent validation with h* fixed (eqs. 15, 16, 29). Calibration and validation use
    their own streams. The target is the restricted mean run length E[min(T, t_max)]
    (horizon t_max = 5000; a path without an alarm counts t_max), not E[T]. Also returns
    the inputs of diagnostics c-i; nothing here is recalibrated on any diagnostic."""
    W, T, A0 = cfg["warmup"], cfg["t_max"], cfg["target_arl"]
    need_m4 = not cfg.get("finite_variance_simulation", False)
    r_cal, h_cal = sim.simulate(f["gp"], cfg["n_cal"], W + T, g["cal"], cfg["burn"], need_m4=need_m4)
    _, u, _ = scores(r_cal, f["s2"], f["gp"], f["rf"], cfg)
    num = {"cal_max_h": float(h_cal.max()), "cal_max_u": {k: float(v.max()) for k, v in u.items()}}
    del r_cal, h_cal
    hstar, cal = {}, {}
    for lam in cfg["lams"]:
        hstar[str(lam)], cal[str(lam)] = {}, {}
        for k in CHARTS:
            z = chart.ewma(u[k], lam)
            try:
                h, arl = chart.calibrate(z, A0)
            except (ValueError, ArithmeticError) as e:
                raise CalibrationError(f"bisection failed for {k}, lambda {lam}: {e}") from e
            t, cens = chart.first_alarm(z, h)            # min(T, t_max) per path; censored paths count t_max
            below = chart.first_alarm(z, h * (1 - 1e-6))[0].mean()
            m = len(t) // 2
            hstar[str(lam)][k] = h
            cal[str(lam)][k] = {"h": h, "arl_cal": arl, "restricted_mean_check": float(t.mean()),
                                "censored_cal": float(cens.mean()), "overshoot_rel": arl / A0 - 1,
                                "target_deviation": arl - A0,
                                "arl_just_below_h": float(below),
                                "split_half_arl": [float(t[:m].mean()), float(t[m:].mean())]}
    del u
    r_val, h_val = sim.simulate(f["gp"], cfg["n_val"], W + T, g["val"], cfg["burn"], need_m4=need_m4)
    _, u, binds = scores(r_val, f["s2"], f["gp"], f["rf"], cfg)
    num["val_max_h"] = float(h_val.max())
    del r_val, h_val
    qs = cfg.get("diagnostics", {}).get("u_quantiles", [0.5, 0.99, 0.999])
    val, tails = {}, {k: {"u_quantiles": dict(zip(map(str, qs), map(float, np.quantile(u[k], qs)))),
                          "u_max": float(u[k].max())} for k in CHARTS}
    for lam in cfg["lams"]:
        val[str(lam)] = {}
        for k in CHARTS:
            v = chart.validate(chart.ewma(u[k], lam), hstar[str(lam)][k], A0, cfg["tau"], cfg["ic_validation"]["tol"])
            v["rel_se"] = v["se_arl_restricted"] / v["arl_restricted"]
            v["cv_run_length"] = v["se_arl_restricted"] * np.sqrt(v["n_paths"]) / v["arl_restricted"]
            val[str(lam)][k] = v
    return hstar, cal, val, binds, num, tails


def diagnose(cal, val, num, cfg):
    """Diagnostics d-i on the calibration and validation outputs, with the thresholds and
    actions fixed in cfg['diagnostics'] before any calibration. 'stop' ends the run before
    monitoring; 'warn' and 'report' are recorded and change nothing (no recalibration,
    no selective rerun)."""
    D, A0, out = cfg["diagnostics"], cfg["target_arl"], []

    def add(i, name, scope, value, threshold, ok, action):
        out.append({"id": i, "name": name, "scope": scope, "value": value, "threshold": threshold,
                    "passed": bool(ok), "action": action})
    finite = all(np.isfinite(x) for x in [num["cal_max_h"], num["val_max_h"], *num["cal_max_u"].values()])
    add("c", "numerical: simulated variances and scores finite", "all", finite, "finite", finite, "stop")
    tol = Fraction(str(D["split_half_tol"]))             # exact bounds, as in chart.ic_equivalence
    lo, hi = float(Fraction(A0) * (1 - tol)), float(Fraction(A0) * (1 + tol))
    for lam, row in cal.items():
        for k, c in row.items():
            sc = f"{k}, lambda {lam}"
            add("d", "calibration censoring fraction", sc, c["censored_cal"], f"<= {D['cal_censoring_max']}",
                c["censored_cal"] <= D["cal_censoring_max"], "stop")
            ok = (bool(np.isfinite(c["h"])) and c["h"] > 0 and c["arl_cal"] >= A0 and c["arl_just_below_h"] < A0
                  and c["arl_cal"] == c["restricted_mean_check"])
            add("e", "control limit: finite and positive h*, minimal h* with restricted ARL >= target "
                "(ARL just below h* < target), consistent restricted-mean computation", sc, c["h"],
                "finite, > 0, minimal", ok, "stop")
            # Overshoot is a recorded warning (user decision, 27 Oct 2026, before any SPY calibration): in the
            # frozen production run 24/160 calibrations exceeded 1e-3 through the discreteness of the empirical ARL.
            add("e_overshoot", "calibration overshoot |restricted ARL(h*) / target - 1|", sc,
                {"overshoot_rel": c["overshoot_rel"], "achieved_restricted_arl": c["arl_cal"],
                 "target_deviation": c["arl_cal"] - A0}, f"<= {D['bisection_rel_tol']}",
                abs(c["overshoot_rel"]) <= D["bisection_rel_tol"], D["overshoot_action"])
            add("f", "split-half restricted ARL at the full-sample h*", sc, c["split_half_arl"], [lo, hi],
                all(lo <= x <= hi for x in c["split_half_arl"]), "warn")
    for lam, row in val.items():
        for k, v in row.items():
            sc = f"{k}, lambda {lam}"
            add("g", "independent validation, eq. 29 (conditional on h*)", sc, v["ci95"], v["accept"], v["passed"], "report")
            add("h", "validation precision SE / restricted ARL", sc, v["rel_se"], f"<= {D['val_rel_se_max']}",
                v["rel_se"] <= D["val_rel_se_max"], "warn")
    stop = next((c["id"] for c in out if c["action"] == "stop" and not c["passed"]), None)
    return out, stop


def monitor_series(train, monitor, f, cfg):
    """Monitoring-period denominators and scores (step 5): the last W training returns are the
    pre-monitoring history, exactly as in the simulation, and every forecast for day t uses
    returns up to t - 1 only."""
    W = cfg["warmup"]
    r = np.concatenate([train.to_numpy()[-W:], monitor.to_numpy()])
    d, u, binds = scores(r, f["s2"], f["gp"], f["rf"], cfg)
    return {k: v[0] for k, v in d.items()}, {k: v[0] for k, v in u.items()}, binds


def reference_states(dates, z, h, cfg):
    """Chart state on each pre-registered reference date and threshold crossings within the
    following window of trading days (inclusive of the date). Descriptive only: these are not
    detection delays and the events are not verified change points."""
    ex, eps = chart.episodes(z, h)
    starts = np.array([s for s, _ in eps], int)
    out, w = [], cfg["event_window"]
    for ref in cfg["reference_dates"]:
        t = dates.get_indexer([pd.Timestamp(ref["date"])])[0]
        if t < 0:
            raise ValueError(f"reference date {ref['date']} is not a monitoring day; dates are never moved")
        sl = slice(t, min(t + w, len(z)))
        first = np.flatnonzero(ex[sl])
        out.append({"date": ref["date"], "z_over_h": float(z[t] / h), "active_on_date": bool(ex[t]),
                    "first_exceedance_offset": int(first[0]) if first.size else None,
                    "exceedance_days_in_window": int(ex[sl].sum()), "window_days": sl.stop - sl.start,
                    "crossings_in_window": int(((starts >= sl.start) & (starts < sl.stop)).sum()),
                    "max_z_over_h_in_window": float(z[sl].max() / h)})
    return out


def acf1(x):
    x = np.asarray(x) - np.mean(x)
    return float((x[1:] * x[:-1]).mean() / (x**2).mean())


def run(cfg, out, root="."):
    """Steps 1-5; writes frozen.json, monitor.csv, tables.md and two figures into `out`.
    Returns the results dict, with status 'stopped_at_fourth_moment_gate' if the fitted
    GARCH-t fails the strict simulator check (no limits are calibrated and no monitoring
    return is used)."""
    out, res = Path(out), {}
    snap = Path(root) / cfg["snapshot"]
    if not snap.exists():
        spy.download_snapshot(snap.parent, cfg["first_price"], cfg["download_end_exclusive"], cfg["ticker"])
    meta = json.loads(snap.with_suffix(".meta.json").read_text())
    close = spy.load_snapshot(snap)
    integ = spy.integrity(close, cfg["first_price"], cfg["monitor_end"], tuple(cfg["expected_rows"]))
    res["data"] = {"snapshot": str(cfg["snapshot"]), "meta": meta, "integrity": integ}
    if integ["errors"]:
        raise ValueError(f"snapshot integrity failed: {integ['errors']}")
    train, monitor, mu = returns(close, cfg)
    r_all = spy.log_returns(close)
    top = r_all.abs().sort_values(ascending=False).head(10)
    res["data"] |= {"train_mean": mu, "n_train": len(train), "n_monitor": len(monitor),
                    "train_first": str(train.index[0].date()), "train_last": str(train.index[-1].date()),
                    "monitor_first": str(monitor.index[0].date()), "monitor_last": str(monitor.index[-1].date()),
                    "train_sd": float(train.std(ddof=1)),
                    "extreme_returns": [{"date": str(d.date()), "r": float(r_all[d])} for d in top.index]}

    g = streams(cfg)
    f = fit(train, cfg, int(g["rf"].integers(2**31 - 1)))
    gp, fp = f["gp"], fingerprint(f["rf"])
    strict = sim.constraint_violations(gp)
    fv = cfg.get("finite_variance_simulation", False)
    D = cfg.get("diagnostics", {})
    res["fit"] = {"s2": f["s2"], "garch": {"omega": gp.omega, "alpha": gp.alpha, "beta": gp.beta, "nu": gp.nu,
                                           "unconditional_var": gp.var, **f["garch_info"]},
                  "strict_simulator_check": {"violations": strict, "passed": not strict, "m4": gp.m4, "kappa": gp.kappa},
                  "moments": sim.moments(gp),
                  "rf_grid": f["rf_grid"], "rf_seed": f["rf_seed"], "rf_fingerprint": fp,
                  "rf_selection": {"fit_rows": f["n_fit_rf_selection"], "dev_rows": f["n_dev"], "dev_first": f["dev_first"]}}
    if not fv:                                            # original design: strict gate (first SPY run)
        if strict:
            res["status"] = "stopped_at_fourth_moment_gate"
            return res
        checks = []
    else:                                                 # post-stop refinement: finite-variance simulation, a-i
        adm = sim.constraint_violations(gp, need_m4=False)
        mem = float((gp.alpha + gp.beta) ** cfg["burn"])
        checks = [{"id": "a", "name": "admissibility: omega > 0, alpha, beta >= 0, alpha + beta < 1, nu > 2",
                   "scope": "fit", "value": adm, "threshold": "no violations", "passed": not adm, "action": "stop"},
                  {"id": "b", "name": "burn-in memory (alpha + beta)^burn", "scope": "fit", "value": mem,
                   "threshold": f"<= {D['burn_memory_max']}", "passed": mem <= D["burn_memory_max"], "action": "stop"}]
        res["diagnostics"] = {"criteria": D, "checks": checks}
        bad = next((c["id"] for c in checks if not c["passed"]), None)
        if bad:
            res["status"] = f"stopped_at_diagnostic_{bad}"
            return res
    try:
        hstar, cal, val, vbinds, num, tails = limits(f, cfg, g)
    except CalibrationError as e:                         # diagnostic e: bracketing or bisection failed
        checks.append({"id": "e", "name": "bracketing / bisection", "scope": "calibration", "value": str(e),
                       "threshold": "converged", "passed": False, "action": "stop"})
        res["diagnostics"] = {"criteria": D, "checks": checks}
        res["status"] = "stopped_at_diagnostic_e"
        return res
    except FloatingPointError as e:                       # diagnostic c: non-finite simulation or scores
        checks.append({"id": "c", "name": "numerical", "scope": "simulation", "value": str(e), "threshold": "finite",
                       "passed": False, "action": "stop"})
        res["diagnostics"] = {"criteria": D, "checks": checks}
        res["status"] = "stopped_at_diagnostic_c"
        return res
    res["limits"] = {"h": hstar, "calibration": cal, "validation": val, "validation_floor_binds": vbinds,
                     "numerical": num, "tails": tails,
                     "target_definition": f"restricted mean run length E[min(T, {cfg['t_max']})], not E[T]",
                     "passed": {lam: {k: val[lam][k]["passed"] for k in CHARTS} for lam in val}}
    if fv:
        more, stop = diagnose(cal, val, num, cfg)
        checks += more
        res["diagnostics"] = {"criteria": D, "checks": checks,
                              "warnings": [c for c in checks if not c["passed"] and c["action"] in ("warn", "report")]}
        if stop:
            res["status"] = f"stopped_at_diagnostic_{stop}"
            return res
    frozen = {"train_mean": mu, "fit": res["fit"], "h": hstar}
    (out / "frozen.json").write_text(json.dumps(frozen, indent=1, default=float))
    res["frozen_sha256"] = hashlib.sha256((out / "frozen.json").read_bytes()).hexdigest()

    # --- step 5: monitoring returns are used from here on, with everything above frozen
    d, u, mbinds = monitor_series(train, monitor, f, cfg)
    dates, r2 = monitor.index, monitor.to_numpy() ** 2
    series = {"date": dates.date, "r": monitor.to_numpy()}
    mon = {}
    for lam in map(str, cfg["lams"]):
        mon[lam] = {}
        for k in CHARTS:
            z = chart.ewma(u[k], float(lam))[0]
            h = hstar[lam][k]
            ex, eps = chart.episodes(z, h)
            series[f"z_{k}_{lam}"] = z
            yr = pd.Series(ex, index=dates).groupby(dates.year).sum()
            mon[lam][k] = {"h": h, "exceedance_days": int(ex.sum()), "exceedance_fraction": float(ex.mean()),
                           "episodes": len(eps), "longest_episode_days": max((b - a + 1 for a, b in eps), default=0),
                           "episode_list": [{"start": str(dates[a].date()), "end": str(dates[b].date()), "days": b - a + 1,
                                             "peak_z_over_h": float(z[a:b + 1].max() / h)} for a, b in eps],
                           "exceedance_days_by_year": {str(y): int(n) for y, n in yr.items()}}
            if lam == str(cfg["primary_lam"]):
                mon[lam][k]["reference_dates"] = reference_states(dates, z, h, cfg)
    for k in CHARTS:
        series[f"d_{k}"], series[f"u_{k}"] = d[k], u[k]
    res["monitoring"] = mon
    res["forecast_diag"] = {k: {"qlike_proxy": float(fc.qlike(r2, d[k]).mean()), "mse_proxy": float(fc.mse(r2, d[k]).mean()),
                                "mean_u": float(u[k].mean()), "median_u": float(np.median(u[k])), "acf1_u": acf1(u[k]),
                                "max_d": float(d[k].max()), "min_d": float(d[k].min())} for k in CHARTS}
    res["forecast_diag"]["rf"]["floor_binds"] = mbinds
    w = cfg["event_window"]
    res["window_mean_u"] = {ref["date"]: {k: float(u[k][dates.get_loc(pd.Timestamp(ref["date"])):][:w].mean())
                                          for k in CHARTS} for ref in cfg["reference_dates"]}
    saved = json.loads((out / "frozen.json").read_text())["fit"]["garch"]
    res["frozen_checks"] = {"rf_unchanged": fingerprint(f["rf"]) == fp,
                            "garch_unchanged": all(saved[p] == getattr(f["gp"], p) for p in ("omega", "alpha", "beta", "nu")),
                            "frozen_json_unchanged": hashlib.sha256((out / "frozen.json").read_bytes()).hexdigest()
                            == res["frozen_sha256"]}
    pd.DataFrame(series).to_csv(out / "monitor.csv", index=False)
    res["monitor_csv_sha256"] = hashlib.sha256((out / "monitor.csv").read_bytes()).hexdigest()
    res["status"] = "complete"
    (out / "tables.md").write_text(tables(res, cfg))
    figures(pd.read_csv(out / "monitor.csv", parse_dates=["date"]), res, cfg, out)
    return res


# ---------------------------------------------------------------- reporting

def tables(res, cfg):
    D, F, L, lam0 = res["data"], res["fit"], res["limits"], str(cfg["primary_lam"])
    g = F["garch"]
    s = ["# SPY application", "", cfg["label"] + ".", "",
         "Descriptive only: alarms are not verified changes, and alarm counts do not rank the methods. "
         "Control limits come from simulation under the fitted 1993–2006 GARCH(1,1)-t, which favours GARCH.", "",
         "## Table S1. Data and training fits", "", "| Quantity | Value |", "|---|---|",
         f"| Snapshot | `{D['snapshot']}` SHA-256 `{D['meta']['sha256'][:16]}…`, accessed {D['meta'].get('accessed_utc')} |",
         f"| Price rows / range | {D['integrity']['n_rows']} / {D['integrity']['first']} to {D['integrity']['last']} |",
         f"| Training returns | {D['n_train']} ({D['train_first']} to {D['train_last']}); mean {D['train_mean']:.4f}%, "
         f"SD {D['train_sd']:.3f}% |",
         f"| Monitoring returns | {D['n_monitor']} ({D['monitor_first']} to {D['monitor_last']}) |",
         f"| Conventional s² | {F['s2']:.4f} |",
         f"| GARCH(1,1)-t | ω {g['omega']:.4f}, α {g['alpha']:.4f}, β {g['beta']:.4f}, ν {g['nu']:.2f}; "
         f"persistence {g['persistence']:.4f}; fourth-moment coefficient {F['strict_simulator_check']['m4']:.4f} |",
         f"| RF grid: development QLIKE, 2004–2006 | " + ", ".join(f"leaf {c['min_samples_leaf']}/mf {c['max_features']}: {c['dev_qlike']:.4f}"
                                            + (" **(selected)**" if c["selected"] else "") for c in F["rf_grid"]) + " |",
         "", f"## Table S2. Control limits and independent validation (target: restricted mean run length "
             f"E[min(T, {cfg['t_max']})] = {cfg['target_arl']}, simulated from the fitted GARCH-t; not E[T])", "",
         "| λ | Chart | h* | Calibration overshoot | Calibration censoring | Split-half restricted ARL | "
         "Validated restricted ARL [95% CI] | Rel. SE | CV of run length | Eq. 29 |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for lam, v in L["validation"].items():
        for k in CHARTS:
            x, c = v[k], L["calibration"][lam][k]
            sh = c.get("split_half_arl")
            s.append(f"| {lam} | {LABEL[k]} | {L['h'][lam][k]:.4f} | {c.get('overshoot_rel', float('nan')):+.2e} | "
                     f"{c['censored_cal']:.4f} | " + (f"{sh[0]:.1f} / {sh[1]:.1f}" if sh else "–") +
                     f" | {x['arl_restricted']:.1f} [{x['ci95'][0]:.1f}, {x['ci95'][1]:.1f}] | {x.get('rel_se', float('nan')):.3f} | "
                     f"{x.get('cv_run_length', float('nan')):.3f} | {'pass' if x['passed'] else 'FAIL'} |")
    if "diagnostics" in res:
        s += ["", "## Table S2b. Pre-specified calibration diagnostics (thresholds fixed before calibration)", "",
              "| ID | Diagnostic | Scope | Value | Threshold | Result | Action on failure |", "|---|---|---|---|---|---|---|"]
        for c in res["diagnostics"]["checks"]:
            val = c["value"]
            if isinstance(val, dict):
                val = ", ".join(f"{k} {v:.4g}" for k, v in val.items())
            val = f"{val:.4g}" if isinstance(val, float) else (", ".join(f"{x:.4g}" for x in val) if isinstance(val, list)
                                                               and val and isinstance(val[0], float) else str(val))
            s.append(f"| {c['id']} | {c['name']} | {c['scope']} | {val} | {c['threshold']} | "
                     f"{'pass' if c['passed'] else 'FAIL'} | {c['action']} |")
    M = res["monitoring"]
    s += ["", "## Table S3. Continuous monitoring 2007–2026 (no resets)", "",
          "| Chart | Exceedance days (λ = 0.1) | Share of days | Episodes (λ = 0.1) | Longest episode | "
          "Exceedance days / episodes (λ = 0.2) |", "|---|---|---|---|---|---|"]
    for k in CHARTS:
        a = M[lam0][k]
        b = M[[x for x in M if x != lam0][0]][k] if len(M) > 1 else None
        s.append(f"| {LABEL[k]} | {a['exceedance_days']} | {100 * a['exceedance_fraction']:.1f}% | {a['episodes']} | "
                 f"{a['longest_episode_days']} days | " + (f"{b['exceedance_days']} / {b['episodes']}" if b else "–") + " |")
    s += ["", f"## Table S4. Chart state on the pre-registered reference dates (λ = {lam0}; window of "
              f"{cfg['event_window']} trading days from the date)", "",
          "| Date | Event | " + " | ".join(f"{LABEL[k]}: Z/h on date, active, first exceedance (days), crossings"
                                          for k in CHARTS) + " |", "|---|---|" + "---|" * len(CHARTS)]
    for i, ref in enumerate(cfg["reference_dates"]):
        cells = []
        for k in CHARTS:
            x = M[lam0][k]["reference_dates"][i]
            fe = "–" if x["first_exceedance_offset"] is None else x["first_exceedance_offset"]
            cells.append(f"{x['z_over_h']:.2f}, {'yes' if x['active_on_date'] else 'no'}, {fe}, {x['crossings_in_window']}")
        s.append(f"| {ref['date']} | {ref['event']} | " + " | ".join(cells) + " |")
    s += ["", "## Table S5. Forecast diagnostics over the monitoring period (proxy r²) and mean score in the event windows",
          "", "| Chart | QLIKE | MSE | Mean u | Median u | ACF₁ of u | " +
          " | ".join(f"mean u, {r['date']}" for r in cfg["reference_dates"]) + " |",
          "|---|---|---|---|---|---|" + "---|" * len(cfg["reference_dates"])]
    for k in CHARTS:
        x = res["forecast_diag"][k]
        s.append(f"| {LABEL[k]} | {x['qlike_proxy']:.4f} | {x['mse_proxy']:.2f} | {x['mean_u']:.3f} | {x['median_u']:.3f} | "
                 f"{x['acf1_u']:.3f} | " + " | ".join(f"{res['window_mean_u'][r['date']][k]:.2f}"
                                                      for r in cfg["reference_dates"]) + " |")
    s += ["", f"RF floor binds in monitoring: {res['forecast_diag']['rf']['floor_binds']}. "
              f"Frozen checks: {res['frozen_checks']}.", "",
          "Extreme absolute returns (for independent checking): " +
          ", ".join(f"{e['date']} {e['r']:+.2f}%" for e in D["extreme_returns"]) + ".",
          "", "Calendar gaps over 4 days (single multi-day returns, not filled): " +
          (", ".join(f"{a}→{b}" for a, b, _ in D["integrity"]["calendar_gaps_over_4_days"]) or "none") + "."]
    return "\n".join(s) + "\n"


def _plain_log(ax):
    """Log axis with plain 1-2-5 tick labels (0.5, 1, 2) instead of powers of ten."""
    ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 5.0)))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.yaxis.set_minor_formatter(NullFormatter())


def figures(df, res, cfg, out):
    lam = str(cfg["primary_lam"])
    refs = [pd.Timestamp(r["date"]) for r in cfg["reference_dates"]]
    fig, axes = plt.subplots(3, 1, figsize=(11, 7.5), sharex=True)
    for ax, k in zip(axes, CHARTS):
        h = res["limits"]["h"][lam][k]
        ratio = df[f"z_{k}_{lam}"] / h
        ax.plot(df["date"], ratio, lw=0.7, color="C0")
        ax.fill_between(df["date"], 0, 1, where=ratio > 1, color="C3", alpha=0.25, lw=0,
                        transform=ax.get_xaxis_transform(), label="Z above its limit")
        ax.axhline(1, color="C3", lw=0.9, label="control limit h*")
        for i, t in enumerate(refs):
            ax.axvline(t, color="grey", ls=":", lw=0.8)
            if ax is axes[0]:
                ax.annotate(str(i + 1), (t, 1.0), xycoords=("data", "axes fraction"), ha="center", va="bottom", fontsize=7)
        ax.set_yscale("log")
        _plain_log(ax)
        ax.set_ylabel("Z_t / h*")
        ax.text(0.005, 0.96, f"{LABEL[k]} (λ = {lam}, h* = {h:.3f})", transform=ax.transAxes, fontsize=8,
                va="top", bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 1.5})
        ax.grid(alpha=0.3)
    axes[0].legend(fontsize=7, loc="upper right", framealpha=0.9)
    axes[-1].set_xlabel("Trading date")
    fig.suptitle("SPY daily returns, continuous one-sided EWMA monitoring 2007–2026 (no resets; dotted lines: "
                 "pre-registered reference dates 1–" f"{len(refs)})", fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(out / "fig_spy_charts.png", dpi=150)
    plt.close(fig)

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True, gridspec_kw={"height_ratios": [1, 1.6]})
    a1.plot(df["date"], df["r"], lw=0.5, color="k")
    a1.set_ylabel("Return r_t (%, demeaned)")
    a2.plot(df["date"], (df["r"] ** 2).rolling(22).mean(), color="grey", lw=0.8, label="22-day trailing mean of r_t²")
    for k, c in zip(CHARTS, ("C0", "C1", "C2")):
        a2.plot(df["date"], df[f"d_{k}"], color=c, lw=0.9, label=f"{LABEL[k]} denominator d_t")
    a2.set_yscale("log")
    _plain_log(a2)
    a2.set_ylabel("Variance (%², log scale)")
    a2.set_xlabel("Trading date")
    a2.legend(fontsize=7, loc="upper left")
    for ax in (a1, a2):
        ax.grid(alpha=0.3)
        for t in refs:
            ax.axvline(t, color="grey", ls=":", lw=0.8)
    fig.suptitle("SPY 2007–2026: returns and the frozen forecasters' variance denominators "
                 "(one-step-ahead, past returns only)", fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(out / "fig_spy_variance.png", dpi=150)
    plt.close(fig)
