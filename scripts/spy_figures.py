"""Regenerate the two SPY figures from the frozen SPY run with the legends moved below the
axes (src/application.py `figures`), then verify them against the stored series. Plotting
only: nothing is downloaded, fitted, calibrated or simulated, and the frozen run directory
is only read. Output: results/derived/spy_figures/.

    .venv/bin/python scripts/spy_figures.py
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

import matplotlib  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src import application as app  # noqa: E402

RUN = ROOT / "results/runs/spy_20261027T061202_150671"
OUT = ROOT / "results/derived/spy_figures"
FROZEN = {"results.json": "877b5f09696a71b3cf431bbed4d88b72a1e7e449d29a309d17e3db0b5ff7749d",
          "monitor.csv": "3ba200940c1853863139445f23fb929ac4f0ebfb6d65fedc5d8352d3b16c90c1",
          "frozen.json": "5a979745a0e50c1b877f7e14592a1e211713a05538294b9cd29e1765ab4d0c4b",
          "fig_spy_charts.png": "1ff776b95946972f2dc851c380fd971a65899457d777b5a13a973e4c0c1ab3be",
          "fig_spy_variance.png": "ac83e6369c52e2dbd16b0b04d2d6331e38530916fba9438b8c8b6c9a5397db0b"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    if OUT.exists():
        sys.exit(f"refusing to overwrite {OUT}")
    for f, h in FROZEN.items():
        assert sha(RUN / f) == h, f"{f} is not the frozen file"
    run_files = {p.name: sha(p) for p in sorted(RUN.iterdir())}
    res = json.loads((RUN / "results.json").read_text())
    cfg = res["config"]
    df = pd.read_csv(RUN / "monitor.csv", parse_dates=["date"])

    kept = []                                   # keep figures open for inspection
    close = app.plt.close
    app.plt.close = kept.append
    OUT.mkdir(parents=True)
    try:
        app.figures(df, res, cfg, OUT)
    finally:
        app.plt.close = close
    charts, var = kept
    checks = []

    def check(name, ok):
        checks.append({"check": name, "ok": bool(ok)})

    check("frozen results.json, monitor.csv, frozen.json and both original PNGs have their recorded SHA-256", True)
    lam = str(cfg["primary_lam"])
    refs = [pd.Timestamp(r["date"]) for r in cfg["reference_dates"]]
    x = matplotlib.dates.date2num(df["date"])
    for ax, k in zip(charts.axes, app.CHARTS):
        h = res["limits"]["h"][lam][k]
        y = ax.lines[0].get_ydata()
        check(f"charts/{k}: plotted series equals monitor.csv z_{k}_{lam} / stored h* exactly",
              np.array_equal(np.asarray(y), (df[f"z_{k}_{lam}"] / h).to_numpy()))
        check(f"charts/{k}: x equals the monitoring dates", np.array_equal(matplotlib.dates.date2num(ax.lines[0].get_xdata()), x))
        check(f"charts/{k}: y label names the chart and the stored h* ({h:.3f})",
              ax.get_ylabel() == f"{app.LABEL[k]}\nZ_t / h*  (h* = {h:.3f})")
        vl = [ln for ln in ax.lines if ln.get_linestyle() == ":"]
        check(f"charts/{k}: {len(refs)} reference lines at the frozen dates",
              [pd.Timestamp(ln.get_xdata()[0]).date() for ln in vl] == [t.date() for t in refs])
        check(f"charts/{k}: horizontal control limit at 1", any(ln.get_ydata()[0] == 1 and ln.get_ydata()[-1] == 1
                                                                  for ln in ax.lines if ln.get_linestyle() == "-" and len(ln.get_ydata()) == 2))
    a1, a2 = var.axes
    check("variance/returns: plotted series equals monitor.csv r exactly", np.array_equal(np.asarray(a1.lines[0].get_ydata()), df["r"].to_numpy()))
    for k in app.CHARTS:
        ln = [ln for ln in a2.lines if ln.get_label() == f"{app.LABEL[k]} denominator d_t"]
        check(f"variance/{k}: denominator equals monitor.csv d_{k} exactly",
              len(ln) == 1 and np.array_equal(np.asarray(ln[0].get_ydata()), df[f"d_{k}"].to_numpy()))
    for name, fig in (("charts", charts), ("variance", var)):
        fig.canvas.draw()
        rend = fig.canvas.get_renderer()
        check(f"{name}: no axes-level legend", all(ax.get_legend() is None for ax in fig.axes))
        check(f"{name}: one figure legend", len(fig.legends) == 1)
        box = fig.legends[0].get_window_extent(rend)
        check(f"{name}: legend overlaps no axes", not any(box.overlaps(ax.get_window_extent(rend)) for ax in fig.axes))
        fb = fig.bbox
        check(f"{name}: no text inside any plotting area (only above the top axis edge)",
              all(t.get_window_extent(rend).y0 >= ax.get_window_extent(rend).y1 - 1 for ax in fig.axes for t in ax.texts))
        check(f"{name}: legend inside the figure", box.x0 >= fb.x0 and box.x1 <= fb.x1 and box.y0 >= fb.y0)
        check(f"{name}: x label inside the figure, above the legend",
              fig.axes[-1].xaxis.label.get_window_extent(rend).y0 > box.y1)
    for f in ("fig_spy_charts.png", "fig_spy_variance.png"):
        check(f"original {f} unchanged", sha(RUN / f) == FROZEN[f])
    check("every frozen run file unchanged", {p.name: sha(p) for p in sorted(RUN.iterdir())} == run_files)

    figs = {f: sha(OUT / f) for f in ("fig_spy_charts.png", "fig_spy_variance.png")}
    ok = all(c["ok"] for c in checks)
    summary = {"run": str(RUN.relative_to(ROOT)), "inputs_sha256": FROZEN, "outputs_sha256": figs,
               "checks": checks, "n_checks": len(checks), "n_passed": sum(c["ok"] for c in checks), "all_passed": ok}
    (OUT / "spy_figure_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    (OUT / "provenance.txt").write_text(
        f"run_at: {datetime.now(timezone.utc).isoformat()}\ngit_head: {head}\npython: {platform.python_version()}  "
        f"matplotlib: {matplotlib.__version__}\nscript_sha256: {sha(__file__)}\n"
        f"application_sha256: {sha(ROOT / 'src/application.py')}\ninput: {RUN.relative_to(ROOT)}\n"
        + "".join(f"output_sha256 {f}: {h}\n" for f, h in figs.items()))
    for c in checks:
        print(("PASS " if c["ok"] else "FAIL ") + c["check"])
    print(f"{summary['n_passed']}/{summary['n_checks']} checks passed -> {OUT}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
