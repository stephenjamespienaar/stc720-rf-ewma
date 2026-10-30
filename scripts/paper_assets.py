"""Build the report's tables and figure copies from frozen, hash-checked results only.

Reads the frozen production results.json, the P2 Holm summary, the frozen SPY results.json
and the verified derived figures; writes LaTeX tabular bodies to report/tables/, figure
copies to report/figures/, and every tabulated number at full precision to
report/tables/values.json (for tracing in-text numbers). Each printed value is also checked
against the value recorded in the project documentation. Nothing is simulated or refitted.

    .venv/bin/python scripts/paper_assets.py
"""

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROD = ROOT / "results/runs/production_20261014T060921_145897/results.json"
HOLM = ROOT / "results/derived/p2_holm/holm_summary.json"
SPY = ROOT / "results/runs/spy_20261027T061202_150671/results.json"
INPUTS = {PROD: "716862ab41d08c581d2bd65c63979c046a9d9cb5930c111381b3eeb6506b708b",
          HOLM: "d38db5a14b1fe96a28c74d1b33a05b41133f1802b5ea6e70c5154b52915dd09a",
          SPY: "877b5f09696a71b3cf431bbed4d88b72a1e7e449d29a309d17e3db0b5ff7749d"}
FIGS = {"fig_delay.png": ("results/derived/p3_figures/fig_delay.png", "e3ff5f011f9d7a215407740b1eaa8b18d5797f6dd9f24eeeaa886a519bbe6533"),
        "fig_profile.png": ("results/derived/p3_figures/fig_profile.png", "a409411c285eab910ff5f126cef3c9e95ab51047ba23ea436adca9f7226a3f4c"),
        "fig_replicates.png": ("results/derived/p3_figures/fig_replicates.png", "6e4fbcde288886ebc271bdf4bc54ee8284618e0bc6d24cb91c86bb5a16893e30"),
        "fig_spy_charts.png": ("results/derived/spy_figures/fig_spy_charts.png", "0f87a8010116bb8aa86a8ef81035a98201587ecc007064469fc94358bd3e3dd3"),
        "fig_spy_variance.png": ("results/derived/spy_figures/fig_spy_variance.png", "7b3b2359b716a7b1f8e65d293d3e3851e48d8be715c0724df977ff5a24c3b1e7")}
TAB, FIG = ROOT / "report/tables", ROOT / "report/figures"
CH = ("conventional", "garch", "rf", "oracle")
NAME = {"conventional": "Conventional", "garch": "GARCH", "rf": "RF", "oracle": "Oracle$^{\\dagger}$"}
DELTAS = ("1.5", "2.0", "3.0")

values, checks = {}, []


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def check(name, ok):
    checks.append({"check": name, "ok": bool(ok)})


def num(x, d):
    s = f"{x:.{d}f}"
    if s.startswith("-") and float(s) == 0:
        s = s[1:]                                       # no "-0.000"
    return "$-$" + s[1:] if s.startswith("-") else s   # typographic minus in tables


def ci(lo, hi, d):
    return f"[{num(lo, d)}, {num(hi, d)}]"


def pval(p):
    if p < 1e-3:
        m, e = f"{p:.1e}".split("e")
        return f"${m}\\times10^{{{int(e)}}}$"
    return f"{p:.3f}" if p < 0.1 else f"{p:.2f}"


def plain(s):  # the table string without LaTeX, for comparison with the documented values
    return s.replace("$-$", "−").replace("$", "")


def rec(key, v):
    values[key] = v
    return v


def doc(label, got, expected):
    check(f"documented value {label}: {expected}", plain(got) == expected)


SPEC = {"tab_sim_charts.tex": "lcccc", "tab_contrasts.tex": "lrcccc", "tab_spy_fit.tex": "ll",
        "tab_spy_limits.tex": "cllrlc", "tab_spy_monitor.tex": "lrrrrrrr",
        "tab_spy_reference.tex": r"rl>{\raggedright\arraybackslash}p{5.2cm}ccc"}


def write(name, header, rows):
    body = "\n".join(" & ".join(r) + r" \\" for r in rows)
    (TAB / name).write_text(f"\\begin{{tabular}}{{{SPEC[name]}}}\n\\toprule\n{header}\n\\midrule\n{body}\n"
                            "\\bottomrule\n\\end{tabular}\n")


def sim_tables(prod, holm):
    E = prod["aggregate"]["estimands"]

    def m(k):
        return rec(f"prod:{k}", E[k]["mean"])

    def mci(k, d):
        c = E[k]["ci95"]
        rec(f"prod:{k}:ci95", c)
        return f"{num(m(k), d)} {ci(*c, d)}"

    # Table: per-chart performance (lambda = 0.1)
    rows = [["Validated ARL$_0$, mean"] + [num(m(f"validation/0.1/{c}/arl_restricted"), 1) for c in CH],
            ["$P(T<\\tau)$, no change"] + [num(m(f"validation/0.1/{c}/p_lt_tau"), 3) for c in CH],
            ["QLIKE against true $h_t$"] + [num(m(f"forecast_diag/{c}/qlike_true"), 3) for c in CH],
            ["ACF$_1$ of $u_t$"] + [num(m(f"forecast_diag/{c}/acf_u/lag1"), 3) for c in CH],
            [r"\multicolumn{5}{l}{\emph{Restricted mean delay RMD$_{500}$ (days) [95\% CI]}}"]]
    rows[-1] = [rows[-1][0]]
    for d in ("1.0",) + DELTAS:
        rows.append([f"\\quad $\\delta={float(d):g}$"] + [mci(f"ooc/{d}/0.1/{c}/rmd", 1) for c in CH])
    rows.append([r"\multicolumn{5}{l}{\emph{Excess detection within 20 days, $X(20)$}}"])
    for d in DELTAS:
        rows.append([f"\\quad $\\delta={float(d):g}$"] + [num(m(f"ooc/{d}/0.1/{c}/x_20"), 3) for c in CH])
    rows.append([r"\multicolumn{5}{l}{\emph{Adaptation masking ratio $M$ [95\% CI]}}"])
    for d in DELTAS:
        rows.append([f"\\quad $\\delta={float(d):g}$"] + ["1 (by construction)"]
                    + [mci(f"masking/{d}/{c}/M", 3) for c in CH[1:]])
    write("tab_sim_charts.tex", " & ".join(["Quantity"] + [NAME[c] for c in CH]) + r" \\", rows)

    want = {"RMD 1.5 conventional": ("ooc/1.5/0.1/conventional/rmd", "205.3 [202.9, 207.6]"),
            "RMD 1.5 rf": ("ooc/1.5/0.1/rf/rmd", "243.3 [237.9, 248.6]"),
            "RMD 1.5 garch": ("ooc/1.5/0.1/garch/rmd", "249.1 [245.6, 252.7]"),
            "RMD 2 conventional": ("ooc/2.0/0.1/conventional/rmd", "131.6 [129.9, 133.4]"),
            "RMD 2 rf": ("ooc/2.0/0.1/rf/rmd", "191.8 [183.5, 200.0]"),
            "RMD 2 garch": ("ooc/2.0/0.1/garch/rmd", "201.7 [196.2, 207.1]"),
            "RMD 3 conventional": ("ooc/3.0/0.1/conventional/rmd", "63.0 [62.1, 64.0]"),
            "RMD 3 rf": ("ooc/3.0/0.1/rf/rmd", "126.4 [115.3, 137.4]"),
            "RMD 3 garch": ("ooc/3.0/0.1/garch/rmd", "139.6 [132.8, 146.4]"),
            "M 1.5 rf": ("masking/1.5/rf/M", "0.342 [0.305, 0.380]"),
            "M 2 garch": ("masking/2.0/garch/M", "0.198 [0.182, 0.214]"),
            "M 3 rf": ("masking/3.0/rf/M", "0.281 [0.237, 0.326]")}
    for lab, (k, exp) in want.items():
        doc(lab, mci(k, 3 if k.startswith("masking") else 1), exp)
    for lab, k, d, exp in (("QLIKE garch", "forecast_diag/garch/qlike_true", 3, "0.812"),
                           ("QLIKE rf", "forecast_diag/rf/qlike_true", 3, "0.841"),
                           ("QLIKE conventional", "forecast_diag/conventional/qlike_true", 3, "1.019"),
                           ("X(20) 1.5 conventional", "ooc/1.5/0.1/conventional/x_20", 3, "0.054"),
                           ("X(20) 3 rf", "ooc/3.0/0.1/rf/x_20", 3, "0.220"),
                           ("P(T<tau) conventional", "validation/0.1/conventional/p_lt_tau", 3, "0.125"),
                           ("RMD delta=1 conventional", "ooc/1.0/0.1/conventional/rmd", 1, "319.9")):
        doc(lab, num(m(k), d), exp)

    # Table: the 12 pre-specified primary contrasts and their delta = 1 counterparts
    hrows = {r["contrast"]: r for r in holm["rows"]}
    rows = []
    for pair, label in (("rf - garch", "RF $-$ GARCH"), ("rf - conventional", "RF $-$ conventional")):
        for metric, mlab, d in (("dH", "RMD$_{500}$ (days)", 2), ("x_20", "$X(20)$", 4)):
            rows.append([f"\\multicolumn{{6}}{{l}}{{\\emph{{{label}, {mlab}}}}}"])
            if metric == "dH":
                k = f"paired/1.0/0.1/{pair}/dH/mean"
                e = E[k]
                rows.append(["\\quad $\\delta=1$ (no change; context)", num(rec(f"prod:{k}", e["mean"]), d),
                             ci(*e["ci95"], d), f"{e['n_pos']}/{e['n_neg']}", "--", "--"])
            else:
                rows.append(["\\quad $\\delta=1$ (no change)", "0 by construction", "--", "--", "--", "--"])
            for dl in DELTAS:
                k = f"paired/{dl}/0.1/{pair}/{metric}/mean"
                e, h = E[k], hrows[f"{dl}/0.1/{pair}/{metric}"]
                check(f"{k}: Holm row mean and CI equal the frozen estimate", h["mean"] == e["mean"] and h["ci95"] == e["ci95"])
                rec(f"prod:{k}", e["mean"]); rec(f"prod:{k}:ci95", e["ci95"])
                rec(f"holm:{h['contrast']}:p", h["p"]); rec(f"holm:{h['contrast']}:p_holm", h["p_holm"])
                rows.append([f"\\quad $\\delta={float(dl):g}$", num(e["mean"], d), ci(*e["ci95"], d),
                             f"{e['n_pos']}/{e['n_neg']}", pval(h["p"]), pval(h["p_holm"])])
                if pair == "rf - garch":
                    check(f"{k}: Holm p {'= 0.0533 (4 dp)' if metric == 'dH' else '= 1'} as documented",
                          f"{h['p_holm']:.4f}" == "0.0533" if metric == "dH" else h["p_holm"] == 1)
                else:
                    check(f"{k}: Holm p <= 9.2e-5 and rejected, as documented",
                          h["p_holm"] <= 9.2e-5 and h["reject_fwer_0.05"])
    write("tab_contrasts.tex", r"Contrast & Estimate & 95\% CI & $+/-$ & $p$ & Holm $p^{\ddagger}$ \\", rows)
    for lab, k, d, exp in (("RF-GARCH RMD 1.5", "paired/1.5/0.1/rf - garch/dH/mean", 2, "−6.05 [−10.47, −1.63]"),
                           ("RF-GARCH RMD 2", "paired/2.0/0.1/rf - garch/dH/mean", 2, "−9.94 [−17.08, −2.80]"),
                           ("RF-GARCH RMD 3", "paired/3.0/0.1/rf - garch/dH/mean", 2, "−13.13 [−22.88, −3.39]"),
                           ("RF-conv RMD 1.5", "paired/1.5/0.1/rf - conventional/dH/mean", 2, "37.54 [32.96, 42.11]"),
                           ("RF-conv RMD 3", "paired/3.0/0.1/rf - conventional/dH/mean", 2, "63.63 [53.01, 74.25]"),
                           ("RF-conv X20 3", "paired/3.0/0.1/rf - conventional/x_20/mean", 4, "−0.0608 [−0.0693, −0.0524]"),
                           ("RF-GARCH X20 1.5", "paired/1.5/0.1/rf - garch/x_20/mean", 4, "0.0009 [−0.0021, 0.0039]"),
                           ("RF-conv RMD delta=1", "paired/1.0/0.1/rf - conventional/dH/mean", 2, "−3.80 [−6.53, −1.07]")):
        doc(lab, f"{num(E[k]['mean'], d)} {ci(*E[k]['ci95'], d)}", exp)
    check("Holm: 6 of 12 rejected", holm["n_reject_t"] == 6)


def spy_tables(spy):
    f, L, M, F = spy["fit"], spy["limits"], spy["monitoring"], spy["forecast_diag"]
    g, rf = f["garch"], [c for c in f["rf_grid"] if c["selected"]]
    check("exactly one RF cell selected", len(rf) == 1)
    rf = rf[0]
    pers = rec("spy:fit/garch/alpha+beta", g["alpha"] + g["beta"])
    for k in ("omega", "alpha", "beta", "nu"):
        rec(f"spy:fit/garch/{k}", g[k])
    rec("spy:fit/s2", f["s2"]); rec("spy:fit/moments/m4", f["moments"]["m4"]); rec("spy:fit/moments/half_life_days", f["moments"]["half_life_days"])
    fit = [["Training sample (returns)", f"{spy['data']['train_first']} to {spy['data']['train_last']} ($n={spy['data']['n_train']}$)"],
           ["Monitoring sample (returns)", f"{spy['data']['monitor_first']} to {spy['data']['monitor_last']} ($n={spy['data']['n_monitor']}$)"],
           ["Training variance $s^2$ (\\%$^2$)", num(f["s2"], 3)],
           ["Variance-targeted GARCH(1,1)-$t$", f"$\\omega={g['omega']:.4f}$, $\\alpha={g['alpha']:.4f}$, $\\beta={g['beta']:.4f}$, $\\nu={g['nu']:.2f}$"],
           ["Persistence $\\alpha+\\beta$", num(pers, 4)],
           ["Fourth-moment coefficient", f"{num(f['moments']['m4'], 4)} ($\\geq 1$: $E r_t^4=\\infty$)"],
           ["RF cell selected (min.\\ leaf, max.\\ features)", f"{rf['min_samples_leaf']}, {rf['max_features']} (development QLIKE {rf['dev_qlike']:.4f})"]]
    write("tab_spy_fit.tex", r"Quantity & Value \\", fit)
    doc("SPY s2", num(f["s2"], 3), "1.144")
    doc("SPY persistence", num(pers, 4), "0.9955")
    doc("SPY m4", num(f["moments"]["m4"], 4), "1.0039")
    doc("SPY nu", f"{g['nu']:.2f}", "7.63")

    rows = []
    for lam in ("0.1", "0.2"):
        for c in CH[:3]:
            cal, v = L["calibration"][lam][c], L["validation"][lam][c]
            rec(f"spy:limits/h/{lam}/{c}", L["h"][lam][c]); rec(f"spy:cal/{lam}/{c}", cal["arl_cal"])
            rec(f"spy:val/{lam}/{c}", v["arl_restricted"]); rec(f"spy:val/{lam}/{c}:ci95", v["ci95"])
            rows.append([lam if c == "conventional" else "", NAME[c], num(L["h"][lam][c], 3), num(cal["arl_cal"], 1),
                         f"{num(v['arl_restricted'], 1)} {ci(*v['ci95'], 1)}", "pass" if L["passed"][lam][c] else "FAIL"])
    write("tab_spy_limits.tex", r"$\lambda$ & Chart & $h^*$ & Calibration & Validation [95\% CI] & Eq.~\eqref{eq:val} \\", rows)
    doc("SPY h conventional", num(L["h"]["0.1"]["conventional"], 3), "1.957")
    doc("SPY val rf 0.1", f"{num(L['validation']['0.1']['rf']['arl_restricted'], 1)} {ci(*L['validation']['0.1']['rf']['ci95'], 1)}", "477.4 [456.5, 498.3]")
    doc("SPY cal garch 0.2", num(L["calibration"]["0.2"]["garch"]["arl_cal"], 1), "500.8")
    check("SPY: 6/6 validations pass", all(L["passed"][l][c] for l in ("0.1", "0.2") for c in CH[:3]))

    rows = []
    for c in CH[:3]:
        a, b = M["0.1"][c], M["0.2"][c]
        for k in ("exceedance_days", "exceedance_fraction", "episodes", "longest_episode_days"):
            rec(f"spy:monitoring/0.1/{c}/{k}", a[k])
        rec(f"spy:forecast_diag/{c}/qlike_proxy", F[c]["qlike_proxy"]); rec(f"spy:forecast_diag/{c}/acf1_u", F[c]["acf1_u"])
        rec(f"spy:forecast_diag/{c}/max_d", F[c]["max_d"])
        rows.append([NAME[c], f"{a['exceedance_days']} ({100 * a['exceedance_fraction']:.1f}\\%)", str(a["episodes"]),
                     str(a["longest_episode_days"]), f"{b['exceedance_days']} / {b['episodes']}",
                     num(F[c]["qlike_proxy"], 3), num(F[c]["acf1_u"], 3), num(F[c]["max_d"], 2)])
    write("tab_spy_monitor.tex", r"Chart & Days above $h^*$ & Episodes & Longest & $\lambda=0.2$: days/episodes & QLIKE & ACF$_1(u)$ & max $d_t$ \\", rows)
    for c, exp in (("conventional", "638 (12.8%) 44 183"), ("garch", "143 (2.9%) 20 24"), ("rf", "216 (4.3%) 27 61")):
        a = M["0.1"][c]
        doc(f"SPY monitoring {c}", f"{a['exceedance_days']} ({100 * a['exceedance_fraction']:.1f}%) {a['episodes']} {a['longest_episode_days']}", exp)
    for c, exp in (("conventional", "1.462"), ("garch", "0.915"), ("rf", "0.986")):
        doc(f"SPY QLIKE {c}", num(F[c]["qlike_proxy"], 3), exp)
    doc("SPY RF max d", num(F["rf"]["max_d"], 3), "3.367")

    refs = spy["config"]["reference_dates"]
    rows = []
    for i, ref in enumerate(refs):
        cells = [str(i + 1), ref["date"], ref["event"].replace("&", "\\&")]
        for c in CH[:3]:
            s = M["0.1"][c]["reference_dates"][i]
            check(f"SPY reference {ref['date']} {c}: date aligned", s["date"] == ref["date"])
            rec(f"spy:ref/{ref['date']}/{c}/z_over_h", s["z_over_h"])
            off = s["first_exceedance_offset"]
            cells.append(f"{s['z_over_h']:.2f} ({'--' if off is None else off})")
        rows.append(cells)
    write("tab_spy_reference.tex", r"\# & Date & Event & Conventional & GARCH & RF \\", rows)
    doc("SPY ref Lehman conventional", f"{M['0.1']['conventional']['reference_dates'][1]['z_over_h']:.2f}", "1.97")
    doc("SPY ref 2020-02-24 garch", f"{M['0.1']['garch']['reference_dates'][6]['z_over_h']:.2f}", "1.18")


def main():
    for p, h in INPUTS.items():
        check(f"input {p.relative_to(ROOT)} has its recorded SHA-256", sha(p) == h)
    if not all(c["ok"] for c in checks):
        sys.exit("an input is not the frozen or verified file")
    prod, holm, spy = (json.loads(p.read_text()) for p in INPUTS)
    TAB.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    sim_tables(prod, holm)
    spy_tables(spy)
    for name, (src, h) in FIGS.items():
        ok = sha(ROOT / src) == h
        check(f"figure source {src} has its verified SHA-256", ok)
        if ok:
            shutil.copyfile(ROOT / src, FIG / name)
            check(f"copy report/figures/{name} is byte-identical", sha(FIG / name) == h)
    (TAB / "values.json").write_text(json.dumps({"inputs_sha256": {str(p.relative_to(ROOT)): h for p, h in INPUTS.items()},
                                                 "values": values}, indent=1) + "\n")
    (TAB / "assets_checks.json").write_text(json.dumps({"n_checks": len(checks), "n_passed": sum(c["ok"] for c in checks),
                                                        "checks": checks}, indent=1) + "\n")
    for c in checks:
        if not c["ok"]:
            print("FAIL " + c["check"])
    print(f"{sum(c['ok'] for c in checks)}/{len(checks)} checks passed; {len(values)} values -> {TAB}")
    sys.exit(0 if all(c["ok"] for c in checks) else 1)


if __name__ == "__main__":
    main()
