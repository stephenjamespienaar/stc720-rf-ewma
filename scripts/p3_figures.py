"""P3: regenerate the production figures from the frozen results.json with the repaired
replicate jitter (src/report.py `jitter`), then verify the replicate figure against the
stored values. Plotting only: nothing is simulated or re-estimated, and the frozen run
directory is only read. Output: results/derived/p3_figures/.

    .venv/bin/python scripts/p3_figures.py
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

from src import report  # noqa: E402

RUN = ROOT / "results/runs/production_20261014T060921_145897"
OUT = ROOT / "results/derived/p3_figures"
RESULTS_SHA = "716862ab41d08c581d2bd65c63979c046a9d9cb5930c111381b3eeb6506b708b"
FIGS = ("fig_delay.png", "fig_profile.png", "fig_replicates.png")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    if OUT.exists():
        sys.exit(f"refusing to overwrite {OUT}")
    raw = (RUN / "results.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == RESULTS_SHA, "results.json is not the frozen file"
    res = json.loads(raw)
    before = {f: sha(RUN / f) for f in FIGS}

    kept = []                                   # keep figures open for inspection
    close = report.plt.close
    report.plt.close = kept.append
    OUT.mkdir(parents=True)
    try:
        report.figures(res, OUT)
    finally:
        report.plt.close = close
    fig = kept[2]                               # fig_replicates (order of report.figures)

    cfg, reps = res["config"], res["replicates"]
    pr, xs, lam = cfg["primary"], [1.0, *cfg["deltas"]], str(cfg["primary"]["lam"])
    offs, gap = report.jitter(xs, len(reps))
    checks = []

    def check(name, ok):
        checks.append({"check": name, "ok": bool(ok)})

    check("results.json SHA-256 is the frozen file", True)
    check("legend present on the first panel", fig.axes[0].get_legend() is not None)
    check("4 panels (metrics x pairs)", len(fig.axes) == len(pr["metrics"]) * len(pr["pairs"]))
    n_points = 0
    for ax, (m, p) in zip(fig.axes, [(m, p) for m in pr["metrics"] for p in pr["pairs"]]):
        ds = xs if m == "dH" else cfg["deltas"]
        tag = f"{p} {m}"
        check(f"{tag}: title and labels", ax.get_title() == f"{p}, λ = {cfg['primary']['lam']}"
              and ax.get_ylabel() == report.METRIC[m] and ax.get_xlabel() == "δ (δ = 1: no change)")
        dots = [ln for ln in ax.lines if ln.get_marker() == "."]
        check(f"{tag}: one point series per replicate (R = {len(reps)})", len(dots) == len(reps))
        X, Y = np.array([ln.get_xdata() for ln in dots]), np.array([ln.get_ydata() for ln in dots])
        stored = np.array([[rep["paired"][str(d)][lam][p][m]["mean"] for d in ds] for rep in reps])
        check(f"{tag}: every replicate value equals the stored per-replicate mean exactly",
              X.shape == stored.shape and np.array_equal(Y, stored))
        check(f"{tag}: x = delta + jitter offset of its replicate", np.allclose(X, np.add.outer(offs, ds), atol=1e-12))
        (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
        check(f"{tag}: all points inside the axis limits (no clipping)",
              (X > x0).all() and (X < x1).all() and (Y > y0).all() and (Y < y1).all())
        check(f"{tag}: x limits contain every delta", x0 < min(ds) and x1 > max(ds))
        check(f"{tag}: clouds of neighbouring delta disjoint", (X.max(axis=0)[:-1] < X.min(axis=0)[1:]).all())
        eb = ax.containers[0]
        mx, my = eb.lines[0].get_xdata(), eb.lines[0].get_ydata()
        a = [res["aggregate"]["estimands"][f"paired/{d}/{lam}/{p}/{m}/mean"] for d in ds]
        check(f"{tag}: mean markers at delta, equal to the stored aggregate means",
              np.array_equal(mx, ds) and np.array_equal(my, [e["mean"] for e in a]))
        seg = np.array([s[:, 1] for s in eb.lines[2][0].get_segments()])
        check(f"{tag}: error bars equal the stored t19 CIs (1e-12)",
              np.allclose(np.sort(seg, axis=1), [e["ci95"] for e in a], rtol=0, atol=1e-12))
        n_points += Y.size
    check("all 280 replicate points drawn (20 x (4 + 3) x 2 pairs)", n_points == 280)

    after = {f: sha(RUN / f) for f in FIGS}
    new = {f: sha(OUT / f) for f in FIGS}
    check("original production figures unchanged", after == before)
    ok = all(c["ok"] for c in checks)
    summary = {"verdict": "PASS" if ok else "FAIL", "source_results_sha256": RESULTS_SHA,
               "results_sha256_field": res["results_sha256"],
               "plotting_change": "src/report.py: replicate jitter = 0.6 * min gap * (r/(R-1) - 1/2) "
                                  "(report.jitter) instead of 0.03 * (r - (R-1)/2); x limits from the gap",
               "jitter_offsets": offs.tolist(), "gap": gap,
               "original_sha256": before, "regenerated_sha256": new, "checks": checks}
    (OUT / "p3_summary.json").write_text(json.dumps(summary, indent=1))
    git = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    (OUT / "p3_provenance.txt").write_text("\n".join([
        f"run_at: {datetime.now(timezone.utc).isoformat()}", f"git_head: {git} (plus the uncommitted P3 plotting change)",
        f"python: {platform.python_version()}  numpy: {np.__version__}  matplotlib: {matplotlib.__version__}",
        f"script_sha256: {sha(__file__)}", f"src/report.py sha256: {sha(ROOT / 'src/report.py')}",
        f"input_sha256 results.json: {RESULTS_SHA}", ""]))
    for c in checks:
        if not c["ok"]:
            print("FAILED:", c["check"])
    print(f"checks: {len(checks)} run, {sum(not c['ok'] for c in checks)} failed")
    for f in FIGS:
        print(f"{f}: original {before[f][:16]}…  regenerated {new[f][:16]}…  {'identical' if before[f] == new[f] else 'differs'}")
    print("VERDICT:", summary["verdict"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
