"""Markdown tables and figures from a results dictionary produced by run.py.

Every number is read from results.json. Method-level cells aggregate R
independently trained replicates with equal weights (src/aggregate.py); the
known-parameter GARCH chart is a diagnostic and is reported in its own section.

Cell conventions: "n/i" = a meaningful estimand or uncertainty quantity that
cannot be identified from the available data (no or too few eligible paths, a
replicate without it, or R = 1 for between-replicate quantities); "–" = not
applicable; "0 (by constr.)" = a valid zero that holds by construction. Figures
omit unidentified points and never draw a zero-width interval for a missing SE.
Headings state the run's inferential status: only `production` has primary
endpoints.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

PRIMARY = ("conventional", "garch", "rf")
LABEL = {"conventional": "Conventional EWMA", "garch": "GARCH-EWMA", "rf": "RF-EWMA", "oracle": "GARCH, true params (diagnostic)"}
STYLE = {"conventional": "C0-o", "garch": "C1-s", "rf": "C2-^", "oracle": "k:"}
RESID = "σ̂_sys (resid.)"
STATUS = {  # mode -> (Table 7a tag, inferential-status banner)
    "production": ("PRIMARY ENDPOINTS", "Primary production simulation. The contrasts in Table 7a are the "
                   "pre-registered primary endpoints; every other result is secondary or descriptive."),
    "sensitivity_arl100": ("SECONDARY: ARL₀ = 100 sensitivity run", "Secondary ARL₀ = 100 sensitivity run, matched to "
                           "production (same paths, separately calibrated limits). **All findings in this report are "
                           "secondary**, including the contrasts that are primary endpoints of the production run."),
    "benchmark": ("PERFORMANCE BENCHMARK ONLY", "Production-scale performance benchmark. **Performance evidence only**: "
                  "excluded from the primary production inference and from the ARL₀ = 100 sensitivity results."),
}
METRIC = {"dH": "RMD_H (days)", "x_5": "X(5)", "x_20": "X(20)", "x_60": "X(60)"}


def _fmt(v, nd=3):
    if v is None:
        return "–"
    if isinstance(v, bool):
        return "yes" if v else "NO"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(_fmt(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def agg(res, *path):
    return res["aggregate"]["estimands"].get("/".join(str(p) for p in path))


def ci(a, nd=3):
    """Replicate mean [95% t interval] (mean only if R = 1); n/i = not identifiable in every replicate."""
    if a is None:
        return "–"
    if "mean" not in a:
        return "n/i"
    m = f"{a['mean']:.{nd}f}"
    return f"{m} [{a['ci95'][0]:.{nd}f}, {a['ci95'][1]:.{nd}f}]" if "ci95" in a else m


def ms(a, nd=3):
    """Replicate mean (between-replicate SD s_b)."""
    if a is None:
        return "–"
    if "mean" not in a:
        return "n/i"
    m = f"{a['mean']:.{nd}f}"
    return f"{m} ({a['sd_between']:.{nd}f})" if "sd_between" in a else m


def stat(a, key, nd=3):
    """A statistic of an aggregate entry: '–' if the estimand does not apply; 'n/i' if it applies but the
    statistic is not identifiable (estimand unidentified, R = 1, a replicate without a Monte Carlo SE, or no
    non-zero sign for the sign test)."""
    if a is None:
        return "–"
    v = a.get(key) if "mean" in a else None
    return "n/i" if v is None else _fmt(float(v), nd)


def span(values):
    return str(min(values)) if min(values) == max(values) else f"{min(values)}–{max(values)}"


def zero_cell(values):
    """A delta = 1 excess quantity, exactly 0 by construction when its population is non-empty: read from the
    stored per-replicate values; 'n/i' if any replicate has no eligible path (stored None)."""
    if any(v is None for v in values):
        return "n/i"
    return "0 (by constr.)" if all(v == 0.0 for v in values) else _fmt(float(np.mean(values)))


def status(res):
    mode = res["mode"]
    return STATUS.get(mode, (f"NOT INFERENTIAL: `{mode}` run", f"`{mode}` run: pipeline check or exploratory; not "
                             "production evidence, and no result here is an endpoint of the study."))


def rng_count(res, *path):
    return span(res["aggregate"]["counts"]["/".join(str(p) for p in path)]["values"])


def flag(res, *path):
    f = res["aggregate"]["flags"]["/".join(str(p) for p in path)]
    return f"{f['n_true']}/{f['R']}"


def validation_failures(res, lams=None, charts=PRIMARY):
    """'chart λ = lam: replicates [...]' for every configuration whose stored IC validation failed; [] if none."""
    reps = res["replicates"]
    out = []
    for lam in lams or res["config"]["lams"]:
        for k in charts:
            bad = [r for r, rep in enumerate(reps) if not rep["validation"][str(lam)][k]["passed"]]
            if bad:
                out.append(f"{LABEL[k]} λ = {lam}: replicate(s) {bad} of {len(reps)}")
    return out


def tables(res):
    cfg, reps = res["config"], res["replicates"]
    R, lams, deltas, pr = len(reps), cfg["lams"], cfg["deltas"], cfg["primary"]
    all_d = [1.0, *deltas]
    s = [f"# Results — mode `{res['mode']}`\n"]
    if cfg.get("label"):
        s.append(f"**{cfg['label']}.**\n")
    tag, banner = status(res)
    production = res["mode"] == "production"
    s.append(f"**Inferential status:** {banner}\n")
    s.append(f"Results SHA-256 (excluding timing): `{res['results_sha256']}`. Per-path outputs: `paths.npz` "
             "(layout and alarm-day coding: `results.json` → `perpath_axes`).\n")
    s.append(f"**R = {R}** independently trained replicate(s), master seed {cfg['master_seed']}. Aggregate cells are "
             "equal-weight means over replicates: `mean [95% CI]` with mean ± t_{R−1,0.975}·s_b/√R, or `mean (s_b)` "
             "with s_b the between-replicate SD. MC SE = √(mean of the squared within-replicate Monte Carlo SEs). "
             "σ̂_sys = √max(0, s_b² − MC SE²) is the residual between-system variability (training, model selection, "
             "forest randomness and calibration) after subtracting the estimated evaluation Monte Carlo variance; a "
             "descriptive method-of-moments approximation, not an identified decomposition of training uncertainty. "
             "Paths are never pooled across replicates. n/i = not identifiable (in every replicate); – = not applicable."
             + (" With R = 1 there is no between-replicate interval; Monte Carlo SEs are in the per-replicate rows."
                if R == 1 else "") + "\n")

    s.append("## Table 1. Fitted forecasters per training replicate\n")
    rows = []
    for r, rep in enumerate(reps):
        g, sel = rep["garch_fit"], next(d for d in rep["rf_grid"] if d["selected"])
        rows.append([r, g["omega"], g["alpha"], g["beta"], g["nu"], g["persistence"], g["near_boundary"], rep["s2_train"],
                     sel["min_samples_leaf"], sel["max_features"], sel["dev_qlike"], rep["floor_binds"],
                     rep["frozen_checks"]["rf_unchanged"] and rep["frozen_checks"]["garch_unchanged"]])
    s.append(md_table(["rep", "ω̂", "α̂", "β̂", "ν̂", "α̂+β̂", "near boundary", "s²", "RF min leaf", "RF max feat.",
                       "RF dev QLIKE", "floor binds", "frozen"], rows))
    d = cfg["dgp"]
    s.append(f"\nTrue DGP: ω = {d['omega']}, α = {d['alpha']}, β = {d['beta']}, ν = {d['nu']}; σ² = "
             f"{reps[0]['dgp_var']:.4f}; 4th-moment coefficient {reps[0]['dgp_m4']:.4f}. Floor binds out of "
             f"{reps[0]['floor_rows']} validation forecasts per replicate.\n")

    s.append("## Table 2. Forecast diagnostics on independent in-control validation paths — mean (s_b) over replicates\n")
    keys = ("qlike_true", "qlike_proxy", "gap_closure", "corr_h", "slope_h", "mean_u", "u_q99")
    rows = [[LABEL[k], *[ms(agg(res, "forecast_diag", k, x)) for x in keys],
             *[ms(agg(res, "forecast_diag", k, "acf_u", f"lag{L}")) for L in (1, 5, 22)]] for k in PRIMARY]
    s.append(md_table(["forecaster", "QLIKE vs h", "QLIKE vs r²", "gap closed G", "corr(d,h)", "slope d on h", "mean u",
                       "u q99", "ACF1 u", "ACF5 u", "ACF22 u"], rows))

    s.append(f"\n## Table 3. Calibrated h* and independent in-control validation (target ARL₀ = {cfg['target_arl']})\n")
    s.append("Per replicate:\n")
    rows = []
    for lam in lams:
        for r, rep in enumerate(reps):
            for k in PRIMARY:
                c, v = rep["calibration"][str(lam)][k], rep["validation"][str(lam)][k]
                rows.append([lam, r, LABEL[k], c["h"], c["arl_cal"], c["censored_cal"], v["arl_restricted"],
                             f"[{v['ci95'][0]:.1f}, {v['ci95'][1]:.1f}]", f"{100 * v['rel_dev']:+.1f}%", v["n_paths"],
                             v["censored"], v["p_lt_tau"], v["passed"]])
    s.append(md_table(["λ", "rep", "chart", "h*", "ARL cal", "cens. cal", "ARL val (restricted)", "95% CI", "rel. dev.",
                       "N val", "cens. val", "P(T<τ)", "pass"], rows))
    s.append("\nAcross replicates:\n")
    rows = []
    for lam in lams:
        for k in PRIMARY:
            a = agg(res, "validation", lam, k, "arl_restricted")
            rows.append([lam, LABEL[k], ms(agg(res, "calibration", lam, k, "h")), ci(a, 1), stat(a, "rms_mc_se", 1),
                         stat(a, "sd_between_resid", 1), ms(agg(res, "validation", lam, k, "p_lt_tau")),
                         flag(res, "validation", lam, k, "passed")])
    s.append(md_table(["λ", "chart", "h* mean (s_b)", "ARL val [95% CI]", "MC SE", RESID, "P(T<τ)", "passed"], rows))
    fl = [f for key, f in res["aggregate"]["flags"].items() if key.startswith("validation/") and "/oracle/" not in key]
    n_ok, n_all = sum(f["n_true"] for f in fl), sum(f["R"] for f in fl)
    iv = cfg["ic_validation"]
    acc = reps[0]["validation"][str(lams[0])]["conventional"]["accept"]
    fails = validation_failures(res)
    s.append(f"\n**Independent ARL₀ validation passed in {n_ok} of {n_all}** primary chart × λ × replicate "
             f"configurations. Rule: {iv['rule']} = [{acc[0]:g}, {acc[1]:g}] (tol = {iv['tol']}); {iv['label']}. Each "
             "CI is conditional on the replicate's calibrated h* and excludes the calibration uncertainty of h*, so the "
             "rule operationalizes practical adequacy and is not a complete formal equivalence test; the individual 95% "
             "CIs give no simultaneous (family-wise) coverage over the configurations checked. Thresholds are never "
             "recalibrated on validation paths. A run that completes is not thereby validated; failures are reported, "
             "never dropped.\n")
    s.append("**Validation failures:** " + ("none.\n" if not fails else "; ".join(fails) + ". These configurations "
             "remain in every table; nominal ARL₀ control is not established for them.\n"))

    s.append(f"\n## Table 4. Out-of-control detection (change at day τ = {cfg['tau']}; delays restricted to H = "
             f"{cfg['H']}; δ = 1 is the no-change counterfactual of the same paths) — mean (s_b) or mean [95% CI] "
             "over replicates\n")
    s.append("Populations: columns marked **[all]** use all N out-of-control paths; columns marked **[E]** are "
             "conditional on no alarm before τ, over each chart's own evaluable set E_k (size n eval, identical across δ "
             "by CRN). X(k) = P(D(δ) ≤ k) − P(D(1) ≤ k), paired on the same paths. Quantiles of D: inverted empirical "
             "CDF, censored paths never counted as detections, n/i when fewer than the required fraction alarmed "
             "within H. Occupancy has no reset. At δ = 1, X(k) is 0 by construction when E_k is non-empty and n/i "
             "otherwise. " + ("Per-chart X(k) levels here are secondary; the primary endpoints are the paired contrasts "
                              "in Table 7a.\n" if production else "No result of this run is a primary endpoint.\n"))
    rows = []
    for dl in all_d:
        for lam in lams:
            for k in PRIMARY:
                a = lambda x: agg(res, "ooc", dl, lam, k, x)  # noqa: E731
                xs = ([zero_cell([rep["ooc"]["1.0"][str(lam)][k][f"x_{q}"] for rep in reps]) for q in cfg["ks"]]
                      if dl == 1.0 else [ci(a(f"x_{q}")) if q == 20 else ms(a(f"x_{q}")) for q in cfg["ks"]])
                rows.append([dl, lam, LABEL[k], rng_count(res, "ooc", dl, lam, k, "n_eval"), ms(a("p_prechange_fa")),
                             ci(a("rmd"), 1), ms(a("q25_d"), 1), ms(a("median_d"), 1), ms(a("q75_d"), 1),
                             *[ms(a(f"p_d_le_{q}")) for q in cfg["ks"]], *xs, ms(a("censored")),
                             ms(a("p_late_given_gt20")), ms(a("occupancy_S")),
                             ms(a("occupancy_excess")) if dl != 1.0 else "0 (by constr.)"])
    s.append(md_table(["δ", "λ", "chart", "n eval", "P(T<τ) [all]", "RMD_H [95% CI] [E]", "q25 D [E]", "median D [E]",
                       "q75 D [E]", *[f"P(D≤{q}) [E]" for q in cfg["ks"]], *[f"X({q}) [E]" for q in cfg["ks"]],
                       "censored [E]", "P(late ∣ D>20) [E]", "occupancy S [all]", "occupancy excess [all]"], rows))

    s.append("\n## Table 5. Pre-change false alarms: out-of-control paths against independent validation paths (A9)\n")
    rows = []
    for lam in lams:
        for k in PRIMARY:
            a, b = agg(res, "ooc", 1.0, lam, k, "p_prechange_fa"), agg(res, "validation", lam, k, "p_lt_tau")
            diff = a["mean"] - b["mean"] if a and b and "mean" in a and "mean" in b else "n/i"
            rows.append([lam, LABEL[k], ci(a), stat(a, "rms_mc_se"), ci(b), stat(b, "rms_mc_se"), diff])
    s.append(md_table(["λ", "chart", "OOC P(T<τ) [all]", "MC SE", "validation P(T<τ) [all]", "MC SE", "difference"], rows))
    s.append("\nIdentical across δ by CRN. The two estimates use independent path sets of the same replicate.\n")

    s.append("\n## Table 6. Adaptation masking (sustained window k ∈ "
             f"{cfg['sustained']}, early k ∈ {cfg['early']}; independent of λ; ratios paired with the no-change "
             "counterfactual of the same paths; delta-method SEs; all N out-of-control paths)\n")
    rows = []
    for dl in deltas:
        for k in PRIMARY:
            m = agg(res, "masking", dl, k, "M")
            name = LABEL[k] + (" — M = 1 by construction (exactness check)" if k == "conventional" else "")
            rows.append([dl, name, ms(agg(res, "masking", dl, k, "uE_ratio")), ms(agg(res, "masking", dl, k, "uS_ratio")),
                         ci(m), stat(m, "sd_between"), stat(m, "rms_mc_se"), stat(m, "sd_between_resid"),
                         ms(agg(res, "masking", dl, k, "M_theory"))])
    s.append(md_table(["δ", "chart", "ū_E(δ)/ū_E(1)", "ū_S(δ)/ū_S(1)", "M [95% CI]", "s_b", "MC SE", RESID,
                       "M first-order theory"], rows))

    def contrast_row(dl, lam, pair, mt):
        if dl == 1.0 and mt != "dH":  # X(k) contrast without a change: 0 by construction if E_a ∩ E_b is non-empty
            c = [rep["paired"]["1.0"][str(lam)][pair][mt] for rep in reps]
            z = zero_cell([x["mean"] for x in c])
            na = "–" if z == "0 (by constr.)" else "n/i"  # a constant has no sampling uncertainty to report
            return [pair, METRIC[mt], dl, lam, z, na, na, na, na, na, span([x["n"] for x in c])]
        a = agg(res, "paired", dl, lam, pair, mt, "mean")
        nd = 2 if mt == "dH" else 4
        signs = "–" if a is None else (f"{a['n_pos']}/{a['n_neg']}" if "mean" in a else "n/i")
        return [pair, METRIC[mt], dl, lam, ci(a, nd), stat(a, "sd_between", nd), stat(a, "rms_mc_se", nd),
                stat(a, "sd_between_resid", nd), signs, stat(a, "sign_p", 4),
                rng_count(res, "paired", dl, lam, pair, mt, "n")]

    hdr = ["contrast (a − b)", "metric", "δ", "λ", "mean [95% CI]", "s_b", "MC SE", RESID, "signs +/−", "sign-test p",
           "paths (E_a ∩ E_b)"]
    n_prim = len(pr["pairs"]) * len(pr["metrics"]) * len(deltas)
    what = (f"{n_prim} contrasts: {', '.join(pr['pairs'])} × {', '.join(METRIC[m] for m in pr['metrics'])} × "
            f"δ ∈ {deltas} at λ = {pr['lam']}, each shown with its δ = 1 counterpart. Each replicate's contrast is a "
            "mean over the paths with no pre-change alarm for either chart (E_a ∩ E_b, common random numbers); X(20) "
            "contrasts compare per-path excess indicators 1{D(δ) ≤ 20} − 1{D(1) ≤ 20}. Not adjusted for multiplicity.")
    if production:
        s.append("\n## Table 7a. PRIMARY ENDPOINTS — paired contrasts, " + pr["label"] + "\n")
        s.append(what + " **Only these RMD₅₀₀ and X(20) paired contrasts are primary**; X(5), X(60), λ = 0.2, "
                 "GARCH − conventional, per-chart levels and every result of the ARL₀ = 100 sensitivity run are "
                 "secondary.\n")
    else:
        s.append(f"\n## Table 7a. Contrasts pre-registered for the production run — {tag}\n")
        s.append(what + f" They are the production run's pre-registered endpoints; in this `{res['mode']}` run they "
                 "carry no primary status.\n")
    pf = validation_failures(res, lams=[pr["lam"]])
    s.append(f"**IC-validation flag for the charts in these contrasts (λ = {pr['lam']}):** " + (
        f"all {R} replicate(s) passed for every chart.\n" if not pf else "; ".join(pf) + ". The contrasts are "
        "reported unchanged, over every replicate; their comparability and nominal ARL₀ control are limited for the "
        "failed configurations.\n"))
    prim = [(dl, pr["lam"], p, m) for p in pr["pairs"] for m in pr["metrics"] for dl in all_d]
    s.append(md_table(hdr, [contrast_row(*x) for x in prim]))
    s.append(f"\n## Table 7b. {'Secondary' if production else 'Other'} paired contrasts (over E_a ∩ E_b)\n")
    allc = [(dl, lam, p, m) for lam in lams for p in res["replicates"][0]["paired"]["1.0"][str(lam)]
            for m in METRIC for dl in all_d if not (dl == 1.0 and m != "dH")]
    s.append(md_table(hdr, [contrast_row(*x) for x in allc if x not in prim]))

    s.append(f"\n## Table 8. {'Primary contrasts' if production else f'Pre-registered production contrasts ({tag})'} "
             f"per replicate (λ = {pr['lam']}): estimate, normal paired 95% CI (Monte Carlo, conditional on the "
             "replicate's trained system and h*) and percentile-bootstrap check\n")
    rows = []
    for r, rep in enumerate(reps):
        for p in pr["pairs"]:
            for m in pr["metrics"]:
                for dl in (all_d if m == "dH" else deltas):
                    c = rep["paired"][str(dl)][str(pr["lam"])][p][m]
                    nd = 2 if m == "dH" else 4
                    v = lambda x: "n/i" if x is None else _fmt(x, nd)  # noqa: E731
                    ci95 = "n/i" if c["ci95"][0] is None else f"[{v(c['ci95'][0])}, {v(c['ci95'][1])}]"
                    boot = f"[{v(c['boot_ci95'][0])}, {v(c['boot_ci95'][1])}]" if "boot_ci95" in c else \
                        ("n/i" if c["ci95"][0] is None and cfg["n_boot"] else "–")
                    rows.append([r, p, METRIC[m], dl, v(c["mean"]), v(c["se_mean"]), ci95, boot, c["n"]])
    s.append(md_table(["rep", "contrast", "metric", "δ", "estimate", "SE", "normal 95% CI", "bootstrap 95% CI",
                       "n (E_a ∩ E_b)"], rows))

    s.append("\n## Diagnostic (not a competitor): GARCH filter with the true in-control parameters\n")
    s.append("Equals h_t in control, so its score is iid and the Brook–Evans Markov-chain ARL applies.\n")
    rows = []
    for lam in lams:
        for r, rep in enumerate(reps):
            c, v, b = rep["calibration"][str(lam)]["oracle"], rep["validation"][str(lam)]["oracle"], \
                rep["brook_evans_oracle"][str(lam)]
            rows.append([lam, r, c["h"], c["arl_cal"], b["arl_markov"], v["arl_restricted"],
                         f"[{v['ci95'][0]:.1f}, {v['ci95'][1]:.1f}]", v["passed"]])
    s.append(md_table(["λ", "rep", "h*", "ARL cal", "Brook–Evans ARL", "ARL val", "95% CI", "pass"], rows))
    rows = [[dl, lam, ms(agg(res, "ooc", dl, lam, "oracle", "p_prechange_fa")), ci(agg(res, "ooc", dl, lam, "oracle", "rmd"), 1),
             ms(agg(res, "ooc", dl, lam, "oracle", "median_d"), 1),
             ci(agg(res, "ooc", dl, lam, "oracle", "x_20")) if dl != 1.0 else
             zero_cell([rep["ooc"]["1.0"][str(lam)]["oracle"]["x_20"] for rep in reps]),
             ms(agg(res, "ooc", dl, lam, "oracle", "occupancy_S"))] for dl in all_d for lam in lams]
    s.append("\n" + md_table(["δ", "λ", "P(T<τ)", "RMD_H [95% CI]", "median D", "X(20)", "occupancy S"], rows))
    rows = [[dl, ci(agg(res, "masking", dl, "oracle", "M")), ms(agg(res, "masking", dl, "oracle", "M_theory"))]
            for dl in deltas]
    s.append("\n" + md_table(["δ", "M [95% CI]", "M first-order theory"], rows))

    s.append("\n## Table 9. Measured runtime by stage (in-process, summed over replicates)\n")
    s.append(md_table(["stage", "wall s", "CPU s", "CPU/wall", "peak RSS MiB (cumulative)"],
                      [[k, t["wall"], t["cpu"], t["cpu"] / t["wall"] if t["wall"] > 0 else None, t["peak_rss_mb"]]
                       for k, t in res["timing"].items()]))
    return "\n".join(s) + "\n"


def series(xs, entries, ses_r1):
    """Plottable (x, mean, half-width) triples from aggregate entries. Unidentified
    entries (no "mean") are omitted, so valid points at other x still appear. The
    half-width is that of the replicate t interval, or 1.96 Monte Carlo SEs when
    R = 1; NaN (no error bar drawn) when no interval exists, never 0."""
    out = []
    for x, a, se in zip(xs, entries, ses_r1):
        if a is None or a.get("mean") is None:
            continue
        hw = a["ci95"][1] - a["mean"] if "ci95" in a else (1.96 * se if se is not None else np.nan)
        out.append((x, a["mean"], hw))
    return out


def _plot(ax, pts, fmt, **kw):
    if pts:
        x, y, e = zip(*pts)
        ax.errorbar(x, y, yerr=list(e), fmt=fmt, capsize=3, **kw)


def figures(res, out):
    cfg, reps = res["config"], res["replicates"]
    deltas, pr = cfg["deltas"], cfg["primary"]
    xs = [1.0, *deltas]
    note = f"R = {len(reps)}; error bars: 95% t interval over replicates" if len(reps) > 1 else \
        "R = 1; error bars: 1.96 Monte Carlo SE (conditional on the trained system)"

    omitted = 0
    fig, axes = plt.subplots(1, len(cfg["lams"]), figsize=(5.5 * len(cfg["lams"]), 4.2), squeeze=False)
    for ax, lam in zip(axes[0], cfg["lams"]):
        for k in (*PRIMARY, "oracle"):
            pts = series(xs, [agg(res, "ooc", d, lam, k, "rmd") for d in xs],
                         [reps[0]["ooc"][str(d)][str(lam)][k]["se_rmd"] for d in xs])
            omitted += len(xs) - len(pts)
            _plot(ax, pts, STYLE[k], label=LABEL[k])
        ax.set_yscale("log")
        ax.set_xlabel("Variance multiplier δ (δ = 1: no change)")
        ax.set_ylabel(f"Mean detection delay, restricted to H = {cfg['H']} (days)")
        ax.set_title(f"λ = {lam}, ARL₀ = {cfg['target_arl']}")
        ax.grid(alpha=0.3)
    axes[0][0].legend(fontsize=8)
    fig.suptitle(f"Restricted mean detection delay vs size of a persistent volatility-scale change ({note})"
                 + (f"; {omitted} unidentified point(s) omitted" if omitted else ""), fontsize=9)
    fig.tight_layout()
    fig.savefig(out / "fig_delay.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(1, len(deltas), figsize=(5.0 * len(deltas), 4.0), squeeze=False, sharey=False)
    for ax, d in zip(axes[0], deltas):
        for k in (*PRIMARY, "oracle"):
            prof = np.mean([np.divide(rep["profile"][str(d)][k], rep["profile"]["1.0"][k]) for rep in reps], axis=0)
            ax.plot(range(len(prof)), prof, STYLE[k].replace("o", "").replace("s", "").replace("^", ""),
                    lw=1, label=LABEL[k])
        ax.axhline(d, color="grey", ls="--", lw=0.8)
        ax.axhline(1, color="grey", lw=0.8)
        for k0, k1 in (cfg["early"], cfg["sustained"]):
            ax.axvspan(k0, k1, color="grey", alpha=0.08)
        ax.set_xlabel("Days since change, k")
        ax.set_ylabel("Mean score ū_k(δ) / no-change ū_k(1)")
        ax.set_title(f"δ = {d}")
        ax.grid(alpha=0.3)
    axes[0][0].legend(fontsize=8)
    fig.suptitle(f"Post-change score profiles, mean over {len(reps)} replicate(s) "
                 "(shaded: early and sustained windows; dashed: δ)", fontsize=10)
    fig.tight_layout()
    fig.savefig(out / "fig_profile.png", dpi=150)
    plt.close(fig)

    lam, omitted = pr["lam"], 0
    fig, axes = plt.subplots(len(pr["metrics"]), len(pr["pairs"]), figsize=(5.0 * len(pr["pairs"]), 3.8 * len(pr["metrics"])),
                             squeeze=False)
    for row, m in zip(axes, pr["metrics"]):
        for ax, p in zip(row, pr["pairs"]):
            ds = xs if m == "dH" else deltas
            label = "replicate"
            for r, rep in enumerate(reps):
                off = 0.03 * (r - (len(reps) - 1) / 2)
                v = [(d + off, rep["paired"][str(d)][str(lam)][p][m]["mean"]) for d in ds]
                v = [(x, y) for x, y in v if y is not None]
                omitted += len(ds) - len(v)
                if v:
                    ax.plot(*zip(*v), ".", color="C7", alpha=0.8, label=label)
                    label = None
            pts = series(ds, [agg(res, "paired", d, lam, p, m, "mean") for d in ds],
                         [reps[0]["paired"][str(d)][str(lam)][p][m]["se_mean"] for d in ds])
            omitted += len(ds) - len(pts)
            _plot(ax, pts, "ks", label="mean over replicates")
            ax.axhline(0, color="grey", lw=0.8)
            ax.set_xlim(0.75, max(xs) + 0.25)
            ax.set_xlabel("δ (δ = 1: no change)")
            ax.set_ylabel(METRIC[m])
            ax.set_title(f"{p}, λ = {lam}")
            ax.grid(alpha=0.3)
    axes[0][0].legend(fontsize=8)
    head = ("Primary paired contrasts" if res["mode"] == "production"
            else f"Pre-registered production contrasts, {status(res)[0]}")
    fig.suptitle(f"{head}\nEach grey point is one training replicate ({note})"
                 + (f"; {omitted} unidentified point(s) omitted" if omitted else ""), fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out / "fig_replicates.png", dpi=150)
    plt.close(fig)


def write(res, out):
    out = Path(out)
    (out / "tables.md").write_text(tables(res))
    figures(res, out)
