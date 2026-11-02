"""Publication-size report figures, drawn from frozen results only (plotting only).

The Stage 1 figures were rendered 10-15 in wide and printed about 6 in wide, so their text
printed at 3.4-5.7 pt. This script draws the three report figures at their printed width
(6.3 in = the A4 text width with 2.5 cm margins) with 8-9 pt text, and checks every plotted
series against the frozen inputs and against the series drawn by the original plotting code
(src/report.py, src/application.py). Nothing is simulated, fitted, calibrated or downloaded,
and the frozen run directories are only read. The SPY figure shows the three chart statistics; the
variance denominators are summarised in the report's Table 4 (maximum d_t).
Output: results/derived/paper_figures/ (never overwritten).

    .venv/bin/python scripts/paper_figures.py
"""

import hashlib
import json
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter  # noqa: E402

from src import application as app  # noqa: E402
from src import report  # noqa: E402

PROD = ROOT / "results/runs/production_20261014T060921_145897"
SPY = ROOT / "results/runs/spy_20261027T061202_150671"
OUT = ROOT / "results/derived/paper_figures"
FROZEN = {PROD / "results.json": "716862ab41d08c581d2bd65c63979c046a9d9cb5930c111381b3eeb6506b708b",
          SPY / "results.json": "877b5f09696a71b3cf431bbed4d88b72a1e7e449d29a309d17e3db0b5ff7749d",
          SPY / "monitor.csv": "3ba200940c1853863139445f23fb929ac4f0ebfb6d65fedc5d8352d3b16c90c1"}
WIDTH, MIN_PT = 6.3, 8.0
CH = ("conventional", "garch", "rf", "oracle")
COL = {"conventional": "#0072B2", "garch": "#D55E00", "rf": "#009E73", "oracle": "k"}  # Okabe-Ito; CVD-validated
NAME = {"conventional": "Conventional EWMA", "garch": "GARCH–EWMA", "rf": "RF–EWMA", "oracle": "Oracle (diagnostic)"}
MARK = {"conventional": "o", "garch": "s", "rf": "^", "oracle": None}
plt.rcParams.update({"font.size": 8, "axes.labelsize": 8.5, "axes.titlesize": 9, "xtick.labelsize": 8,
                     "ytick.labelsize": 8, "legend.fontsize": 8, "axes.linewidth": 0.6, "grid.linewidth": 0.4,
                     "pdf.fonttype": 42})


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def thick_legend(leg, lw=1.8):
    """Thicker line samples in the legend only (the plotted lines are unchanged)."""
    for h in leg.legend_handles:
        if isinstance(h, matplotlib.lines.Line2D):
            h.set_linewidth(lw)


def log_ticks(ax, ticks):
    """Log axis labelled with plain numbers at the candidate ticks inside the data limits."""
    ax.set_yscale("log")
    lo, hi = ax.get_ylim()
    ax.yaxis.set_major_locator(FixedLocator([t for t in ticks if lo <= t <= hi]))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.yaxis.set_minor_formatter(NullFormatter())


def fig_delay(res):
    cfg, xs = res["config"], [1.0, *res["config"]["deltas"]]
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH, 2.35), sharey=True)
    for ax, lam in zip(axes, cfg["lams"]):
        for k in CH:
            pts = report.series(xs, [report.agg(res, "ooc", d, lam, k, "rmd") for d in xs], [None] * len(xs))
            x, y, e = zip(*pts)
            ax.errorbar(x, y, yerr=list(e), color=COL[k], marker=MARK[k], ms=3.5, lw=1, capsize=2.5,
                        ls=":" if k == "oracle" else "-", label=NAME[k])
        log_ticks(ax, [50, 75, 100, 150, 200, 300])
        ax.set_xticks(xs)
        ax.set_xlabel("Variance multiplier δ (δ = 1: no change)")
        ax.set_title(f"λ = {lam} ({'primary' if lam == cfg['primary']['lam'] else 'secondary'})")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("RMD$_{500}$ (days, log scale)")
    fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=4, frameon=False)
    fig.tight_layout(rect=(0, 0.095, 1, 1))
    return fig


def profiles(res):
    reps = res["replicates"]
    return {(d, k): np.mean([np.divide(r["profile"][str(d)][k], r["profile"]["1.0"][k]) for r in reps], axis=0)
            for d in res["config"]["deltas"] for k in CH}


def fig_profile(res, prof):
    cfg = res["config"]
    fig, axes = plt.subplots(1, 3, figsize=(WIDTH, 2.2))
    for ax, d in zip(axes, cfg["deltas"]):
        for k0, k1 in (cfg["early"], cfg["sustained"]):
            ax.axvspan(k0, k1, color="0.5", alpha=0.12, lw=0)
        ax.axhline(d, color="0.4", ls="--", lw=0.7)
        ax.axhline(1, color="0.4", lw=0.7)
        for k in CH:
            p = prof[(d, k)]
            ax.plot(range(len(p)), p, color=COL[k], ls=":" if k == "oracle" else "-", lw=1, label=NAME[k])
        ax.set_title(f"δ = {d:g}")
        ax.set_xlabel("Days since the change, k")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("Score ratio $\\bar u_k(\\delta)/\\bar u_k(1)$")
    thick_legend(fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=4, frameon=False))
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    return fig


def fig_spy(df, res):
    cfg, lam = res["config"], str(res["config"]["primary_lam"])
    refs = [pd.Timestamp(r["date"]) for r in cfg["reference_dates"]]
    fig, axes = plt.subplots(3, 1, figsize=(WIDTH, 3.5), sharex=True)
    for ax, k in zip(axes, app.CHARTS):
        ratio = df[f"z_{k}_{lam}"] / res["limits"]["h"][lam][k]
        ax.plot(df["date"], ratio, color=COL[k], lw=0.6)
        ax.fill_between(df["date"], 0, 1, where=ratio > 1, color="0.45", alpha=0.3, lw=0,
                        transform=ax.get_xaxis_transform(), label="Exceedance day ($Z_t > h^*$)")
        ax.axhline(1, color="k", lw=0.8, label="Control limit")
        log_ticks(ax, [0.1, 1, 10])
        ax.set_ylabel(f"{NAME[k].split('–')[0].replace(' EWMA', '')}\n$Z_t/h^*$")
    for ax in axes:
        ax.grid(alpha=0.3)
        for t in refs:
            ax.axvline(t, color="0.35", ls=":", lw=0.7)
    for i, t in enumerate(refs):
        axes[0].annotate(str(i + 1), (t, 1.0), xycoords=("data", "axes fraction"), ha="center", va="bottom", fontsize=MIN_PT)
    axes[-1].xaxis.set_major_locator(mdates.YearLocator(2))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axes[-1].set_xlabel("Trading date")
    thick_legend(fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=2, frameon=False))
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    return fig


def originals(res, spy, df):
    """Figures drawn in memory by the original plotting code, for series-equality checks."""
    kept, close = [], plt.close
    with tempfile.TemporaryDirectory() as tmp:
        report.plt.close = app.plt.close = kept.append
        try:
            report.figures(res, Path(tmp))
            app.figures(df, spy, spy["config"], Path(tmp))
        finally:
            report.plt.close = app.plt.close = close
    return kept  # delay, profile, replicates, spy charts, spy variance


def main():
    if OUT.exists():
        sys.exit(f"refusing to overwrite {OUT}")
    for p, h in FROZEN.items():
        assert sha(p) == h, f"{p} is not the frozen file"
    before = {p: sha(p) for d in (PROD, SPY) for p in sorted(d.iterdir()) if p.is_file()}
    res = json.loads((PROD / "results.json").read_text())
    spy = json.loads((SPY / "results.json").read_text())
    df = pd.read_csv(SPY / "monitor.csv", parse_dates=["date"])
    checks = []

    def check(name, ok):
        checks.append({"check": name, "ok": bool(ok)})

    check("inputs: production results.json, SPY results.json and monitor.csv have their frozen SHA-256", True)
    o_delay, o_prof, _, o_charts, _ = originals(res, spy, df)
    prof = profiles(res)
    figs = {"fig_delay.pdf": fig_delay(res), "fig_profile.pdf": fig_profile(res, prof), "fig_spy.pdf": fig_spy(df, spy)}

    # Figure 1: every RMD point and interval equals the frozen aggregate and the original figure
    E, xs = res["aggregate"]["estimands"], [1.0, *res["config"]["deltas"]]
    for ax, oax, lam in zip(figs["fig_delay.pdf"].axes, o_delay.axes, res["config"]["lams"]):
        for cont, ocont, k in zip(ax.containers, oax.containers, CH):
            a = [E[f"ooc/{d}/{lam}/{k}/rmd"] for d in xs]
            x, y = cont.lines[0].get_xdata(), cont.lines[0].get_ydata()
            seg = np.sort(np.array([s[:, 1] for s in cont.lines[2][0].get_segments()]), axis=1)
            check(f"delay λ={lam} {k}: points equal the frozen RMD means at δ = 1, 1.5, 2, 3",
                  np.array_equal(x, xs) and np.array_equal(y, [e["mean"] for e in a]))
            check(f"delay λ={lam} {k}: error bars equal the frozen 95% t intervals (1e-9)",
                  np.allclose(seg, [e["ci95"] for e in a], rtol=0, atol=1e-9))
            check(f"delay λ={lam} {k}: same points as the original figure",
                  np.array_equal(y, ocont.lines[0].get_ydata()) and np.array_equal(x, ocont.lines[0].get_xdata()))
    # Figure 2: every profile equals the frozen per-replicate profiles and the original figure
    for ax, oax, d in zip(figs["fig_profile.pdf"].axes, o_prof.axes, res["config"]["deltas"]):
        lines = [ln for ln in ax.lines if ln.get_label() in NAME.values()]
        olines = [ln for ln in oax.lines if len(ln.get_ydata()) > 2]
        for ln, oln, k in zip(lines, olines, CH):
            check(f"profile δ={d} {k}: equals the replicate mean of ū_k(δ)/ū_k(1) from the frozen profiles",
                  np.array_equal(ln.get_ydata(), prof[(d, k)]) and len(ln.get_ydata()) == res["config"]["H"])
            check(f"profile δ={d} {k}: same series as the original figure", np.array_equal(ln.get_ydata(), oln.get_ydata()))
        check(f"profile δ={d}: conventional ratio equals δ (by construction) up to the 5-decimal rounding of "
              "the stored profiles (rtol 1e-4)", np.allclose(prof[(d, "conventional")], d, rtol=1e-4, atol=0))
    # Figure 3: SPY series equal monitor.csv / stored h*, exceedance counts equal the frozen counts
    lam = str(spy["config"]["primary_lam"])
    refs = [pd.Timestamp(r["date"]).date() for r in spy["config"]["reference_dates"]]
    for ax, oax, k in zip(figs["fig_spy.pdf"].axes, o_charts.axes, app.CHARTS):
        h, y = spy["limits"]["h"][lam][k], np.asarray(ax.lines[0].get_ydata())
        check(f"spy {k}: Z/h* equals monitor.csv z_{k}_{lam} / stored h* = {h:.3f} and the original figure",
              np.array_equal(y, (df[f"z_{k}_{lam}"] / h).to_numpy()) and np.array_equal(y, oax.lines[0].get_ydata()))
        check(f"spy {k}: x equals the {len(df)} monitoring dates",
              np.array_equal(mdates.date2num(ax.lines[0].get_xdata()), mdates.date2num(df["date"])))
        check(f"spy {k}: {int((y > 1).sum())} days above the limit = frozen exceedance_days",
              int((y > 1).sum()) == spy["monitoring"][lam][k]["exceedance_days"])
    for i, ax in enumerate(figs["fig_spy.pdf"].axes):
        vl = [pd.Timestamp(ln.get_xdata()[0]).date() for ln in ax.lines if ln.get_linestyle() == ":"]
        check(f"spy panel {i}: reference lines at the 9 frozen dates", vl == refs)
    # Printed-size legibility and layout
    for name, fig in figs.items():
        fig.canvas.draw()
        rend, fb = fig.canvas.get_renderer(), fig.bbox
        hidden = set()  # tick labels the locator made but the axis does not draw (outside the view)
        for ax in fig.axes:
            for axis in (ax.xaxis, ax.yaxis):
                lo, hi = sorted(axis.get_view_interval())
                for t in axis.get_major_ticks() + axis.get_minor_ticks():
                    if not lo - 1e-9 <= t.get_loc() <= hi + 1e-9:
                        hidden.update((id(t.label1), id(t.label2)))
        texts = [t for t in fig.findobj(matplotlib.text.Text)
                 if t.get_visible() and t.get_text().strip() and id(t) not in hidden]
        check(f"{name}: printed width {WIDTH} in", abs(fig.get_figwidth() - WIDTH) < 1e-9)
        check(f"{name}: all {len(texts)} text items >= {MIN_PT} pt at printed size", all(t.get_fontsize() >= MIN_PT for t in texts))
        check(f"{name}: all text inside the figure", all(fb.contains(*t.get_window_extent(rend).p0) and
                                                         fb.contains(*t.get_window_extent(rend).p1) for t in texts))
        box = fig.legends[0].get_window_extent(rend)
        check(f"{name}: one figure legend, overlapping no axes",
              len(fig.legends) == 1 and not any(box.overlaps(ax.get_window_extent(rend)) for ax in fig.axes))
        check(f"{name}: no axes-level legend", all(ax.get_legend() is None for ax in fig.axes))

    OUT.mkdir(parents=True)
    for name, fig in figs.items():
        fig.savefig(OUT / name, metadata={"CreationDate": None})
        plt.close(fig)
    after = {p: sha(p) for d in (PROD, SPY) for p in sorted(d.iterdir()) if p.is_file()}
    check(f"all {len(before)} files of the frozen production and SPY runs unchanged", after == before)
    ok = all(c["ok"] for c in checks)
    outs = {n: sha(OUT / n) for n in figs}
    (OUT / "paper_figures_summary.json").write_text(json.dumps(
        {"verdict": "PASS" if ok else "FAIL", "inputs_sha256": {str(p.relative_to(ROOT)): h for p, h in FROZEN.items()},
         "outputs_sha256": outs, "printed_width_in": WIDTH, "min_font_pt": MIN_PT, "n_checks": len(checks),
         "n_passed": sum(c["ok"] for c in checks), "checks": checks}, indent=1) + "\n")
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    (OUT / "provenance.txt").write_text(
        f"run_at: {datetime.now(timezone.utc).isoformat()}\ngit_head: {head} (plus uncommitted working-tree changes)\n"
        f"python: {platform.python_version()}  numpy: {np.__version__}  matplotlib: {matplotlib.__version__}\n"
        f"script_sha256: {sha(__file__)}\n" + "".join(f"input_sha256 {p.relative_to(ROOT)}: {h}\n" for p, h in FROZEN.items())
        + "".join(f"output_sha256 {n}: {h}\n" for n, h in outs.items()))
    for c in checks:
        if not c["ok"]:
            print("FAIL", c["check"])
    print(f"{sum(c['ok'] for c in checks)}/{len(checks)} checks passed -> {OUT}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
