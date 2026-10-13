"""Markdown tables and figures from a results dictionary produced by run.py."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

CHARTS = ("conventional", "garch", "rf")
LABEL = {"conventional": "Conventional EWMA", "garch": "GARCH-EWMA", "rf": "RF-EWMA", "oracle": "GARCH, true params (diagnostic)"}
STYLE = {"conventional": "C0-o", "garch": "C1-s", "rf": "C2-^", "oracle": "k:"}


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


def tables(res):
    rep = res["replicates"][0]
    cfg = res["config"]
    s = [f"# Results — mode `{res['mode']}`\n", f"Results SHA-256 (excluding timing): `{res['results_sha256']}`\n"]

    g = rep["garch_fit"]
    s.append("## Table 1. Fitted forecasters (training path)\n")
    s.append(md_table(["", "omega", "alpha", "beta", "nu", "alpha+beta", "m4", "near boundary"],
                      [["true DGP", *[cfg["dgp"][k] for k in ("omega", "alpha", "beta", "nu")],
                        cfg["dgp"]["alpha"] + cfg["dgp"]["beta"], rep["dgp_m4"], "–"],
                       ["GARCH-t fit", g["omega"], g["alpha"], g["beta"], g["nu"], g["persistence"], g["m4"], g["near_boundary"]]]))
    s.append(f"\nTraining s² = {rep['s2_train']:.4f} (true σ² = {rep['dgp_var']:.4f}).\n")
    s.append("RF grid (development-path QLIKE vs r², lower is better):\n")
    s.append(md_table(["min_samples_leaf", "max_features", "dev QLIKE", "selected"],
                      [[d["min_samples_leaf"], d["max_features"], d["dev_qlike"], d["selected"]] for d in rep["rf_grid"]]))
    s.append(f"\nReference dev QLIKE: constant {rep['dev_qlike_ref']['conventional']:.4f}, "
             f"GARCH {rep['dev_qlike_ref']['garch']:.4f}, oracle {rep['dev_qlike_ref']['oracle']:.4f}.\n")

    s.append("## Table 2. Forecast diagnostics on independent in-control validation paths\n")
    fd = rep["forecast_diag"]
    rows = []
    for k in (*CHARTS, "oracle"):
        f = fd[k]
        rows.append([LABEL[k], f["qlike_true"], f["qlike_proxy"], f["mse_true"], f.get("gap_closure"), f["corr_h"], f["slope_h"],
                     f["mean_u"], f["u_q99"], f["u_max"], f["acf_u"][0], f["acf_u"][1], f["acf_u"][2]])
    s.append(md_table(["forecaster", "QLIKE vs h", "QLIKE vs r²", "MSE vs h", "gap closed G", "corr(d,h)", "slope d on h", "mean u",
                       "u q99", "u max", "ACF1 u", "ACF5 u", "ACF22 u"], rows))
    s.append(f"\nRF floor binds: {rep['floor_binds']} of {rep['floor_rows']} forecasts.\n")

    s.append("## Table 3. Calibration (h*) and independent validation of in-control run length\n")
    rows = []
    for lam in cfg["lams"]:
        for k in (*CHARTS, "oracle"):
            c = rep["calibration"][str(lam)][k]
            v = rep["validation"][str(lam)][k]
            rows.append([lam, LABEL[k], c["h"], c["arl_cal"], c["censored_cal"], v["arl_restricted"],
                         f"[{v['ci95'][0]:.1f}, {v['ci95'][1]:.1f}]", v["censored"], v["q10"], v["q50"], v["q90"],
                         v["p_lt_tau"], v["passed"]])
    s.append(md_table(["λ", "chart", "h*", "ARL cal", "cens. cal", "ARL val (restricted)", "95% CI", "cens. val",
                       "RL q10", "RL q50", "RL q90", "P(T<τ)", "pass"], rows))
    be = rep.get("brook_evans_oracle")
    if be:
        s.append("\nOracle chart (iid input) — Markov-chain ARL at the calibrated h* vs simulation:\n")
        s.append(md_table(["λ", "Brook–Evans ARL", "calibration ARL", "validation ARL"],
                          [[lam, b["arl_markov"], b["arl_cal"], b["arl_val"]] for lam, b in be.items()]))

    s.append(f"\n## Table 4. Out-of-control detection (change at day τ = {cfg['tau']}; delays restricted to H = {cfg['H']}; "
             "δ = 1 is the no-change counterfactual of the same paths). Delay columns are over each chart's own "
             "evaluable paths E_k = {T ≥ τ} (size n eval), which differ between charts; paired contrasts (Table 6) "
             "use pairwise intersections\n")
    rows = []
    for delta in [1.0, *cfg["deltas"]]:
        for lam in cfg["lams"]:
            for k in (*CHARTS, "oracle"):
                o = rep["ooc"][str(delta)][str(lam)][k]
                rows.append([delta, lam, LABEL[k], *(o.get(c) for c in (
                    "p_prechange_fa", "n_eval", "mean_dH", "se_dH", "median_d", "p_d_le_5", "p_d_le_20", "p_d_le_60",
                    "p_late_given_gt20", "censored", "occupancy_S"))])
    s.append(md_table(["δ", "λ", "chart", "P(FA before τ)", "n eval", "mean D_H", "SE", "median D", "P(D≤5)", "P(D≤20)",
                       "P(D≤60)", "P(late | D>20)", "censored", "occupancy S"], rows))

    s.append("\n## Table 5. Adaptation masking: post-change mean score relative to the no-change counterfactual "
             f"(early k ∈ {cfg['early']}, sustained k ∈ {cfg['sustained']}; independent of λ)\n")
    rows = []
    for delta in cfg["deltas"]:
        for k in (*CHARTS, "oracle"):
            m = rep["masking"][str(delta)][k]
            rows.append([delta, LABEL[k], m["u0_incontrol"], m["uE_ratio"], m["uS_ratio"], m["M"], m.get("M_theory")])
    s.append(md_table(["δ", "chart", "in-control mean u", "ū_E(δ)/ū_E(1)", "ū_S(δ)/ū_S(1)", "M", "M first-order theory"],
                      rows))

    s.append("\n## Table 6. Paired contrasts in restricted mean delay: mean of D_H(a) − D_H(b) over the paths where "
             "neither chart alarmed before τ (E_a ∩ E_b; CRN), with percentile-bootstrap 95% CI over paths. "
             "δ = 1 rows are the no-change baseline of each contrast. Monte Carlo intervals conditional on this "
             "replicate's fitted forecasters and calibrated h*; not adjusted for multiple comparisons\n")
    rows = []
    for delta in [1.0, *cfg["deltas"]]:
        for lam in cfg["lams"]:
            for name, pdiff in rep["paired"][str(delta)][str(lam)].items():
                rows.append([delta, lam, name, pdiff["mean"], f"[{_fmt(pdiff['ci95'][0], 2)}, {_fmt(pdiff['ci95'][1], 2)}]", pdiff["n"]])
    s.append(md_table(["δ", "λ", "comparison (a − b)", "mean paired diff", "95% CI", "n paths (E_a ∩ E_b)"], rows))

    s.append("\n## Table 7. Measured runtime by stage (in-process)\n")
    s.append(md_table(["stage", "wall s", "CPU s", "CPU/wall", "peak RSS MiB (cumulative)"],
                      [[k, t["wall"], t["cpu"], t["cpu"] / t["wall"] if t["wall"] > 0 else None, t["peak_rss_mb"]]
                       for k, t in res["timing"].items()]))
    return "\n".join(s) + "\n"


def figures(res, out):
    rep = res["replicates"][0]
    cfg = res["config"]
    deltas = cfg["deltas"]
    xs = [1.0, *deltas]

    fig, axes = plt.subplots(1, len(cfg["lams"]), figsize=(5.5 * len(cfg["lams"]), 4.2), squeeze=False)
    for ax, lam in zip(axes[0], cfg["lams"]):
        for k in (*CHARTS, "oracle"):
            o = [rep["ooc"][str(d)][str(lam)][k] for d in xs]
            ax.errorbar(xs, [x["mean_dH"] for x in o], yerr=[1.96 * x["se_dH"] for x in o], fmt=STYLE[k],
                        label=LABEL[k], capsize=3)
        ax.set_yscale("log")
        ax.set_xlabel("Variance multiplier δ (δ = 1: no change)")
        ax.set_ylabel(f"Mean detection delay, restricted to H = {cfg['H']} (days)")
        ax.set_title(f"λ = {lam}, ARL₀ = {cfg['target_arl']}")
        ax.grid(alpha=0.3)
    axes[0][0].legend(fontsize=8)
    fig.suptitle("Restricted mean detection delay vs size of a persistent volatility-scale change", fontsize=10)
    fig.tight_layout()
    fig.savefig(out / "fig_delay.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(1, len(deltas), figsize=(5.0 * len(deltas), 4.0), squeeze=False, sharey=False)
    for ax, d in zip(axes[0], deltas):
        for k in (*CHARTS, "oracle"):
            prof = [v / b for v, b in zip(rep["profile"][str(d)][k], rep["profile"]["1.0"][k])]
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
    fig.suptitle("Post-change score profiles (shaded: early and sustained windows; dashed: δ)", fontsize=10)
    fig.tight_layout()
    fig.savefig(out / "fig_profile.png", dpi=150)
    plt.close(fig)


def write(res, out):
    out = Path(out)
    (out / "tables.md").write_text(tables(res))
    figures(res, out)
