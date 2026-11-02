"""Check the manuscript's key in-text numbers against the frozen outputs (verification only).

Each check builds the expected text from a hash-checked frozen source and requires it to appear in
report/main.tex (whitespace-normalised), so a change to either the text or the evidence fails the
check. Nothing is simulated, refitted or downloaded. Re-run after every edit of the manuscript.

    .venv/bin/python scripts/manuscript_checks.py
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = {"prod": ("results/runs/production_20261014T060921_145897/results.json", "716862ab41d08c581d2bd65c63979c046a9d9cb5930c111381b3eeb6506b708b"),
       "holm": ("results/derived/p2_holm/holm_summary.json", "d38db5a14b1fe96a28c74d1b33a05b41133f1802b5ea6e70c5154b52915dd09a"),
       "p45": ("results/derived/p45_diagnostics/p45_summary.json", "70e5282bf2b5bd89cf6484bff6b24af3aff198f8bedc9c2f4ab5f76d7b024837"),
       "spy": ("results/runs/spy_20261027T061202_150671/results.json", "877b5f09696a71b3cf431bbed4d88b72a1e7e449d29a309d17e3db0b5ff7749d"),
       "stop": ("results/runs/spy_20261027T045319_117125/results.json", "decf1d00937a400e5a7d9947ba627d1c02c23fe8fcc50158e8e877db20135622"),
       "vt": ("results/derived/spy_vt_review/vt_review.json", "0f1fad167053a86048428dc9ace294a89e8e89f9be2e6eba114141a5ec50cc68")}
MONITOR = ("results/runs/spy_20261027T061202_150671/monitor.csv", "3ba200940c1853863139445f23fb929ac4f0ebfb6d65fedc5d8352d3b16c90c1")
D = ("1.5", "2.0", "3.0")


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def trio(xs, d):
    a, b, c = (f"{x:.{d}f}" for x in xs)
    return f"{a}, {b} and {c}"


def main():
    for p, h in [*SRC.values(), MONITOR]:
        assert sha(p) == h, f"{p} is not the frozen file"
    J = {k: json.loads((ROOT / p).read_text()) for k, (p, _) in SRC.items()}
    df = pd.read_csv(ROOT / MONITOR[0], parse_dates=["date"])
    tex = " ".join((ROOT / "report/main.tex").read_text().split())
    prod, spy, cfg = J["prod"], J["spy"], J["prod"]["config"]
    E, reps = prod["aggregate"]["estimands"], prod["replicates"]
    checks = []

    def has(label, snippet, ok=True):
        checks.append({"check": label, "ok": bool(ok) and snippet in tex, "expected_text": snippet})

    def m(k):
        return E[k]["mean"]

    rmd = {c: [m(f"ooc/{d}/0.1/{c}/rmd") for d in D] for c in ("conventional", "garch", "rf", "oracle")}
    pair = {(p, k): [m(f"paired/{d}/0.1/{p}/{k}/mean") for d in D] for p in ("rf - garch", "rf - conventional") for k in ("dH", "x_20")}
    holm = {r["contrast"]: r for r in J["holm"]["rows"]}

    # ---- simulation: headline delays (abstract, Section 4.1, conclusion)
    has("abstract: conventional RMD", f"restricted mean delays of {trio(rmd['conventional'], 0)} days")
    has("abstract: RF and GARCH RMD", f"against {trio(rmd['rf'], 0)} for RF--EWMA and {trio(rmd['garch'], 0)} for GARCH--EWMA")
    rg = [abs(x) for x in pair[("rf - garch", "dH")]]
    has("abstract: RF-GARCH range", f"on average {min(rg):.0f}--{max(rg):.0f} days faster than GARCH--EWMA")
    has("4.1: RMD ranges", f"fell from {rmd['conventional'][0]:.1f} to {rmd['conventional'][2]:.1f} days for the conventional chart, "
        f"from {rmd['rf'][0]:.1f} to {rmd['rf'][2]:.1f} for RF--EWMA and from {rmd['garch'][0]:.1f} to {rmd['garch'][2]:.1f} for GARCH--EWMA")
    rc = pair[("rf - conventional", "dH")]
    has("conclusion: RF-conventional range", f"{min(rc):.0f}--{max(rc):.0f} days sooner on average than RF--EWMA and in every fitted system")
    has("conclusion: RF-GARCH range", f"them {min(rg):.0f}--{max(rg):.0f} days sooner than GARCH--EWMA on average")
    # ---- forecasts
    q = {c: m(f"forecast_diag/{c}/qlike_true") for c in ("rf", "garch", "oracle", "conventional")}
    has("4.1: QLIKE vs true h", f"mean QLIKE against the true variance was {q['rf']:.3f}, against {q['garch']:.3f} for GARCH, "
        f"{q['oracle']:.3f} for the oracle and {q['conventional']:.3f} for the constant")
    G, ci = m("forecast_diag/rf/gap_closure"), E["forecast_diag/rf/gap_closure"]["ci95"]
    has("4.1: gap closed G", f"closed {100 * G:.0f}\\% of the gap \\eqref{{eq:gap}} ($G={G:.3f}$ [{ci[0]:.3f}, {ci[1]:.3f}]), "
        f"against {100 * m('forecast_diag/garch/gap_closure'):.1f}\\% for GARCH")
    has("conclusion: 85% of the gap", f"closed {100 * G:.0f}\\% of the accuracy gap")
    has("4.1: slope and correlation", f"slope \\eqref{{eq:slope}} {m('forecast_diag/rf/slope_h'):.2f}, against "
        f"{m('forecast_diag/garch/slope_h'):.2f} for GARCH; correlation with $h_t$ {m('forecast_diag/rf/corr_h'):.2f}")
    has("4.1: ACF1 of u", f"(lag-1 autocorrelation {m('forecast_diag/rf/acf_u/lag1'):.3f}, against "
        f"{m('forecast_diag/conventional/acf_u/lag1'):.3f} for the constant)")
    rows, binds = sum(r["floor_rows"] for r in reps), sum(r["floor_binds"] for r in reps)
    has("4.1: floor never bound in 2e8 forecasts", "never bound in $2\\times10^8$ forecasts", rows == 2 * 10**8 and binds == 0)
    # ---- in-control calibration
    val = [r["validation"][lam][c] for r in reps for lam in r["validation"] for c in r["validation"][lam]]
    has("4.1: 160/160 validations", "All 160 validations", len(val) == 160 and all(v["passed"] for v in val))
    a0 = [m(f"validation/0.1/{c}/arl_restricted") for c in ("conventional", "garch", "rf", "oracle")]
    has("4.1: validated ARL0 range", f"mean validated ARL$_0$ of {min(a0):.1f}--{max(a0):.1f} at $\\lambda=0.1$")
    be = np.mean([r["brook_evans_oracle"]["0.1"]["arl_markov"] for r in reps])
    has("4.1: Brook-Evans oracle ARL", f"gave a mean ARL$_0$ of {be:.1f} at the calibrated limits")
    pt = {c: m(f"validation/0.1/{c}/p_lt_tau") for c in ("conventional", "garch", "rf", "oracle")}
    oth = [pt[c] for c in ("garch", "rf", "oracle")]
    geo = 1 - (1 - 1 / 500) ** 49
    has("4.1: P(T<tau)", f"{100 * pt['conventional']:.1f}\\% of the conventional chart's paths signalled before day 50, against "
        f"{100 * min(oth):.1f}--{100 * max(oth):.1f}\\% for the other charts and {100 * geo:.1f}\\% under a geometric run length")
    has("4.1: run-length CV (P5)", f"(coefficient of variation {J['p45']['P5']['validation_summaries']['conventional']['cv']['mean']:.2f})")
    cen = {c: m(f"ooc/1.5/0.1/{c}/censored") for c in ("garch", "rf", "conventional")}
    has("4.1: censoring at delta 1.5", f"{100 * cen['garch']:.0f}\\% of the surviving GARCH paths and {100 * cen['rf']:.0f}\\% of the RF "
        f"paths had no alarm within 500 days, against {100 * cen['conventional']:.0f}\\% for the conventional chart")
    x = {c: [m(f"ooc/{d}/0.1/{c}/x_20") for d in D] for c in ("conventional", "rf", "garch")}
    has("4.1: per-chart X(20)", f"$X(20)$ was {trio(x['conventional'], 3)} for the conventional chart and about {trio(x['rf'], 3)} "
        "for both RF and GARCH", max(abs(a - b) for a, b in zip(x["rf"], x["garch"])) < 0.003)
    M = {c: [m(f"masking/{d}/{c}/M") for d in D] for c in ("rf", "garch", "oracle")}
    has("4.1: masking ratios", f"was {trio(M['rf'], 3)} for RF--EWMA at $\\delta=1.5$, 2 and 3, against {trio(M['garch'], 3)} "
        f"for GARCH--EWMA and {trio(M['oracle'], 3)} for the oracle")
    mt = [m(f"masking/{d}/garch/M_theory") for d in D]
    gap = [a - b for a, b in zip(M["garch"], mt)]
    has("4.1: first-order masking theory", f"predicted {trio(mt, 3)} for the fitted GARCH filters, {min(gap):.2f}--{max(gap):.2f} below")
    # ---- primary contrasts (Section 4.2)
    has("4.2: RF-conventional RMD", f"took {trio(rc, 1)} days longer to detect the change", all(E[f"paired/{d}/0.1/rf - conventional/dH/mean"]["n_pos"] == 20 for d in D))
    has("4.2: RF-conventional X(20)", f"lower by {trio([abs(v) for v in pair[('rf - conventional', 'x_20')]], 3)}")
    ph = max(holm[f"{d}/0.1/rf - conventional/{k}"]["p_holm"] for d in D for k in ("dH", "x_20"))
    mant, ex = f"{ph:.1e}".split("e")
    has("4.2: Holm RF-conventional", f"(adjusted $p\\le{mant}\\times10^{{{int(ex)}}}$)",
        all(holm[f"{d}/0.1/rf - conventional/{k}"]["reject_fwer_0.05"] for d in D for k in ("dH", "x_20")))
    e1 = E["paired/1.0/0.1/rf - conventional/dH/mean"]
    has("4.2: delta=1 RF-conventional baseline", f"${e1['mean']:.2f}$ days [${e1['ci95'][0]:.2f}$, ${e1['ci95'][1]:.2f}$]")
    has("4.2: RF-GARCH RMD", f"faster on average by {trio(rg, 2)} days, with unadjusted intervals that exclude zero",
        all(E[f"paired/{d}/0.1/rf - garch/dH/mean"]["ci95"][1] < 0 for d in D))
    hg = {round(holm[f"{d}/0.1/rf - garch/dH"]["p_holm"], 3) for d in D}
    has("4.2: Holm RF-GARCH RMD", f"(adjusted $p={hg.pop():.3f}$ at each $\\delta$)", len(hg) == 0)
    neg = sorted({E[f"paired/{d}/0.1/rf - garch/dH/mean"]["n_neg"] for d in D})
    has("4.2: systems favouring RF", "only 14 or 15 of the 20 systems favoured RF", neg == [14, 15])
    sd = [E[f"paired/{d}/0.1/rf - garch/dH/mean"]["sd_between"] for d in D]
    mc = np.mean([E[f"paired/{d}/0.1/rf - garch/dH/mean"]["rms_mc_se"] for d in D])
    has("4.2: between-system SD vs MC SE", f"{trio(sd, 1)} days, far exceeds the within-system Monte Carlo standard error of about {mc:.1f} days")
    e3 = E["paired/3.0/0.1/rf - garch/dH/mean"]
    has("4.2: delta=3 replicate range", f"from ${e3['min']:.1f}$ to $+{e3['max']:.1f}$ days")
    has("4.2: RF-GARCH X(20) Holm p = 1", "(Holm $p=1$)", all(holm[f"{d}/0.1/rf - garch/x_20"]["p_holm"] == 1 for d in D))
    st = J["p45"]["P4"]["stability_spearman"].values()
    ga = [J["p45"]["P4"]["associations_spearman"]["Masking gap M_RF − M_GARCH (same δ)"][d] for d in D]
    has("4.2: P4 stability and masking-gap association", f"(rank correlations {min(st):.2f}--{max(st):.2f}) and tracked its RF$-$GARCH "
        f"difference in masking ratio (rank correlations ${max(ga):.2f}$ to ${min(ga):.2f}$)")
    # ---- design (Section 3.4)
    g = cfg["dgp"]
    kap = 3 * (g["nu"] - 2) / (g["nu"] - 4)
    m4 = g["beta"] ** 2 + 2 * g["alpha"] * g["beta"] + kap * g["alpha"] ** 2
    s2 = g["omega"] / (1 - g["alpha"] - g["beta"])
    eh2 = (g["omega"] ** 2 + 2 * g["omega"] * (g["alpha"] + g["beta"]) * s2) / (1 - m4)
    has("3.4: DGP persistence, m4, kurtosis", f"persistence {g['alpha'] + g['beta']:.2f} and fourth-moment coefficient {m4:.3f}, so that "
        f"$\\E r_t^4$ is finite although the returns are strongly leptokurtic (kurtosis about {kap * eh2 / s2 ** 2:.1f})")
    has("3.4: R, n, tau, H", f"Each of $R={len(reps)}$ independent replicates", cfg["n_train"] == 3500 and cfg["tau"] == 50 and cfg["H"] == 500)
    has("2.2: CV of r^2 for nu = 6", f"\\sqrt{{\\kappa_\\eta-1}}\\approx{np.sqrt(3 * (6 - 2) / (6 - 4) - 1):.1f}$ for $\\nu=6$")
    # ---- SPY (Section 5)
    dat, fit, lim, mon = spy["data"], spy["fit"], spy["limits"], spy["monitoring"]["0.1"]
    has("5: training mean", f"demeaned by the training mean ({dat['train_mean']:.3f}\\% per day)")
    has("5: sample sizes and dates", f"the {dat['n_train']:,} returns from 1 February 1993 to 29 December 2006 and frozen, and the "
        f"{dat['n_monitor']:,} returns from 3 January 2007 to 30 September 2026",
        (dat["train_first"], dat["train_last"], dat["monitor_first"], dat["monitor_last"]) == ("1993-02-01", "2006-12-29", "2007-01-03", "2026-09-30"))
    u = J["stop"]["fit"]["garch"]
    has("5: unrestricted fit (stopped run)", f"persistence {u['persistence']:.4f}, an implied unconditional variance of {u['unconditional_var']:.2f} "
        f"against $s^2={fit['s2']:.3f}$ and a fourth-moment coefficient \\eqref{{eq:m4}} of {u['m4']:.3f}",
        J["stop"]["status"] == "stopped_at_fourth_moment_gate")
    ll = {f["name"][:2]: f["loglik_project_h1_s2"] for f in J["vt"]["fits"]}
    has("5: variance-targeting likelihood cost", f"at a cost of {ll[chr(65) + chr(39)] - ll['B:']:.2f} log-likelihood units")
    vg = fit["garch"]
    has("5: VT persistence and m4", f"($\\alpha+\\beta={vg['persistence']:.4f}$) but an infinite fourth moment (coefficient {vg['m4']:.4f})",
        vg["persistence"] < 1 <= vg["m4"])
    v = lim["validation"]["0.1"]["rf"]
    has("5: RF validation interval", f"RF at $\\lambda=0.1$: {v['arl_restricted']:.1f} [{v['ci95'][0]:.1f}, {v['ci95'][1]:.1f}]")
    w = spy["diagnostics"]["warnings"]
    has("5: two overshoot warnings at lambda 0.2", "two calibrations at $\\lambda=0.2$ overshot the target by slightly more than a pre-set 0.1\\% warning threshold",
        len(w) == 2 and all(x["id"] == "e_overshoot" and x["scope"].endswith("lambda 0.2") and x["value"]["overshoot_rel"] > 1e-3 for x in w))
    has("5: 6/6 validations", "All six limits passed", all(lim["passed"][lam][c] for lam in ("0.1", "0.2") for c in ("conventional", "garch", "rf")))

    def longest(c):
        return max(mon[c]["episode_list"], key=lambda e: e["days"])
    c_, g_, r_ = mon["conventional"], mon["garch"], mon["rf"]
    has("5: conventional exceedances", f"on {c_['exceedance_days']} days ({100 * c_['exceedance_fraction']:.1f}\\%) in {c_['episodes']} episodes, "
        f"including {c_['longest_episode_days']} consecutive days from 15 September 2008", longest("conventional")["start"] == "2008-09-15")
    has("5: GARCH exceedances", f"on {g_['exceedance_days']} days ({100 * g_['exceedance_fraction']:.1f}\\%) in {g_['episodes']} episodes of at most "
        f"{g_['longest_episode_days']} days")
    has("5: RF exceedances", f"with {r_['exceedance_days']} days ({100 * r_['exceedance_fraction']:.1f}\\%) in {r_['episodes']} episodes, the longest "
        f"of {r_['longest_episode_days']} days from 29 September 2008", longest("rf")["start"] == "2008-09-29")
    above = {c: sum(s["z_over_h"] > 1 for s in mon[c]["reference_dates"]) for c in ("conventional", "garch", "rf")}
    has("5: reference dates above the limit", "the conventional and GARCH statistics were above their limits on seven dates and the RF statistic on four",
        above == {"conventional": 7, "garch": 7, "rf": 4})
    lb = {c: mon[c]["reference_dates"][1] for c in ("conventional", "garch", "rf")}
    has("5: 15 September 2008 states", f"stood at {lb['conventional']['z_over_h']:.2f} times its limit while the GARCH and RF charts crossed "
        f"{lb['garch']['first_exceedance_offset']} and {lb['rf']['first_exceedance_offset']} trading days later", lb["garch"]["date"] == "2008-09-15")
    cv = {c: mon[c]["reference_dates"][6] for c in ("conventional", "garch", "rf")}
    has("5: 24 February 2020 states", f"on 24 February 2020 the GARCH statistic was above its limit and the conventional and RF statistics "
        f"crossed {cv['conventional']['first_exceedance_offset']} and {cv['rf']['first_exceedance_offset']} days later",
        cv["garch"]["date"] == "2020-02-24" and cv["garch"]["z_over_h"] > 1)
    yc = {c: mon[c]["reference_dates"][7] for c in ("conventional", "garch", "rf")}
    has("5: 5 August 2024 states", "after 5 August 2024 only the GARCH and RF charts crossed within 63 trading days",
        yc["garch"]["date"] == "2024-08-05" and yc["conventional"]["first_exceedance_offset"] is None
        and yc["garch"]["first_exceedance_offset"] is not None and yc["rf"]["first_exceedance_offset"] is not None
        and spy["config"]["event_window"] == 63)
    fd = spy["forecast_diag"]
    has("5: QLIKE against the proxy", f"QLIKE against $r_t^2$ ({fd['garch']['qlike_proxy']:.3f} for GARCH, {fd['rf']['qlike_proxy']:.3f} for RF and "
        f"{fd['conventional']['qlike_proxy']:.3f} for the constant)")
    drf, dg = df["d_rf"], df["d_garch"]
    has("5: RF saturation and GARCH peak", f"never exceeded {drf.max():.2f}, a value it reached on {int((drf == drf.max()).sum())} days, whereas the GARCH "
        f"denominator peaked at {dg.max():.1f} on 29 October 2008", str(df.loc[dg.idxmax(), "date"].date()) == "2008-10-29")

    for c in checks:
        print(("PASS " if c["ok"] else "FAIL ") + c["check"] + ("" if c["ok"] else f"\n     expected: {c['expected_text']}"))
    n = sum(c["ok"] for c in checks)
    print(f"{n}/{len(checks)} manuscript checks passed")
    return 0 if n == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
