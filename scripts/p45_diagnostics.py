"""P4/P5: exploratory, post hoc diagnostics of the frozen production run (27 Oct 2026).

P4  RF - GARCH between-system heterogeneity of the paired RMD_500 contrast (lambda = 0.1):
    descriptive heterogeneity summaries (s_b vs Monte Carlo SE, Cochran's Q and I^2 as
    descriptive indices only), stability across delta and lambda, and Spearman
    associations with a predictor set fixed in advance; selected RF cells as categories.
    No p-values, no significance flags, no causal claims, no retuning.
P5  In-control run-length shape: (a) independent-validation summaries as stored (per-path
    validation run lengths were not stored and are not reconstructed); (b) the separately
    generated delta = 1 out-of-control-stream paths in paths.npz (truncated at day 549),
    against an analytic geometric benchmark using the production indexing.

Reads the frozen results.json and paths.npz only; imports neither `run` nor `src`; writes
only to results/derived/p45_diagnostics/.

    .venv/bin/python -I scripts/p45_diagnostics.py --selftest
    .venv/bin/python -I scripts/p45_diagnostics.py
"""

import hashlib
import json
import math
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import scipy  # noqa: E402
from scipy import stats  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "results/runs/production_20261014T060921_145897"
OUT = ROOT / "results/derived/p45_diagnostics"
SHA = {"results.json": "716862ab41d08c581d2bd65c63979c046a9d9cb5930c111381b3eeb6506b708b",
       "paths.npz": "0055f1e115e6cd676d88dcc0875dfee19c44018afc8154658b40be9a2ab8cdf3"}
P1 = ROOT / "results/derived/p1_audit/audit_summary.json"
TAU, H, TMAX, A0, R = 50, 500, 5000, 500, 20
M = TAU - 1 + H                                   # 549 monitored days; 550 = censored
CHARTS = ["conventional", "garch", "rf", "oracle"]
DELTAS = ["1.5", "2.0", "3.0"]
LAM = "0.1"


# ---------------------------------------------------------------- helpers

def tci(x):
    """Equal-weight replicate mean with its 95% t interval (eq. 27)."""
    x = np.asarray(x, float)
    half = stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / math.sqrt(len(x))
    return {"mean": float(x.mean()), "ci95": [float(x.mean() - half), float(x.mean() + half)]}


def cochran(y, w):
    """Cochran's Q about the inverse-variance weighted mean and I^2 = max(0, (Q - df)/Q).
    Descriptive heterogeneity indices only (w are conditional Monte Carlo SEs)."""
    y, v = np.asarray(y, float), np.asarray(w, float) ** 2
    yw = np.sum(y / v) / np.sum(1 / v)
    q = float(np.sum((y - yw) ** 2 / v))
    return q, max(0.0, (q - (len(y) - 1)) / q) if q > 0 else 0.0


def rho(x, y):
    """Spearman rank correlation (descriptive; no p-value)."""
    return float(stats.spearmanr(x, y).statistic)


def geom(A):
    """Analytic geometric benchmark with per-day alarm probability p = 1/A, in the production
    indexing: T in {1, 2, ...}; pre-change alarm T < tau (= T <= 49); among survivors
    (T >= tau, conditional) D = T - tau + 1 is again geometric (memoryless), D_H = min(D, H),
    and censoring at the OOC horizon is D > H (T >= 550). Validation run length min(T, TMAX)."""
    q = 1 - 1 / A
    t = np.arange(1, TMAX)
    pmf = (1 / A) * q ** (t - 1)
    tail = q ** (TMAX - 1)                          # P(T >= TMAX): recorded as TMAX
    mean_v = float(np.sum(t * pmf) + TMAX * tail)
    sd_v = math.sqrt(float(np.sum(t**2 * pmf) + TMAX**2 * tail) - mean_v**2)
    cdf = 1 - q**t

    def quant(a):
        return float(t[np.searchsorted(cdf, a)])
    return {"p_lt_tau": 1 - q ** (TAU - 1), "p_le_250": 1 - q**250,
            "rmd_given_survive": (1 - q**H) * A, "censored_given_survive": q**H,
            "validation_mean": mean_v, "validation_cv": sd_v / mean_v,
            "q10": quant(0.1), "q50": quant(0.5), "q90": quant(0.9)}


def surv(T):
    """S(t) = P(T > t), t = 0..M, from alarm days coded 1..M+1 (M+1 = no alarm by day M)."""
    return np.array([(T > t).mean() for t in range(M + 1)])


def selftest():
    # Geometric benchmark against brute-force sums over the exact pmf in production indexing.
    A = 500.0
    p, t = 1 / A, np.arange(1, 400001)
    pmf = p * (1 - p) ** (t - 1)
    g = geom(A)
    assert math.isclose(g["p_lt_tau"], pmf[t < TAU].sum(), rel_tol=1e-12)
    surv_ = t >= TAU
    dh = np.minimum(t - TAU + 1, H)
    assert math.isclose(g["rmd_given_survive"], (pmf[surv_] * dh[surv_]).sum() / pmf[surv_].sum(), rel_tol=1e-9)
    assert math.isclose(g["censored_given_survive"], pmf[t > M].sum() / pmf[surv_].sum(), rel_tol=1e-9)
    assert math.isclose(g["p_lt_tau"], 1 - 0.998**49) and round(g["p_lt_tau"], 4) == 0.0934
    assert round(g["rmd_given_survive"], 1) == 316.2 and abs(g["validation_cv"] - math.sqrt(1 - p)) < 1e-3
    # Restricted mean of a small case by hand: p = 0.2, H = 3 -> 1 + 0.8 + 0.64 = 2.44.
    assert math.isclose((1 - 0.8**3) / 0.2, 2.44)
    # Cochran: y = (0, 1, 2), w = 1 -> Q = 2, I2 = 0; y = (0, 2, 4) -> Q = 8, I2 = 0.75.
    assert cochran([0, 1, 2], [1, 1, 1]) == (2.0, 0.0) and cochran([0, 2, 4], [1, 1, 1]) == (8.0, 0.75)
    # Spearman with ties: ranks x (1, 2.5, 2.5, 4), y (1, 3, 2, 4) -> 4.5 / sqrt(4.5 * 5) = sqrt(0.9).
    assert math.isclose(rho([1, 2, 2, 3], [1, 3, 2, 4]), math.sqrt(0.9))
    # Survival from coded alarm days: T = (1, 50, 550) -> S(0) = 1, S(49) = 2/3, S(549) = 1/3.
    s = surv(np.array([1, 50, 550]))
    assert s[0] == 1 and math.isclose(s[49], 2 / 3) and math.isclose(s[M], 1 / 3)
    # Restricted-geometric moments of min(T, TMAX) against a large synthetic sample (not production data).
    x = np.minimum(np.random.default_rng(1).geometric(1 / 500, 400000), TMAX)
    assert abs(x.mean() / g["validation_mean"] - 1) < 0.01 and abs(x.std() / x.mean() - g["validation_cv"]) < 0.01
    print("selftest: all hand-computed checks passed")


# ---------------------------------------------------------------- analysis

def main():
    selftest()
    if OUT.exists():
        sys.exit(f"refusing to overwrite {OUT}")
    checks, lines = [], []

    def check(name, ok):
        checks.append({"check": name, "ok": bool(ok)})

    def out(s=""):
        lines.append(s)

    for f, h in SHA.items():
        check(f"sha256 {f}", hashlib.sha256((RUN / f).read_bytes()).hexdigest() == h)
    check("P1 verdict PASS", json.loads(P1.read_text())["verdict"] == "PASS")
    res = json.loads((RUN / "results.json").read_text())
    reps, est = res["replicates"], res["aggregate"]["estimands"]
    npz = np.load(RUN / "paths.npz")
    T = [npz[f"r{r}_T"][:, 0] for r in range(R)]     # [delta, chart, path] at lambda = 0.1
    T2 = [npz[f"r{r}_T"][:, 1] for r in range(R)]    # lambda = 0.2
    check("R = 20 replicates", len(reps) == R and res["config"]["lams"][0] == 0.1)

    def pair_dh(Tr, i, a="rf", b="garch"):
        ta, tb = Tr[i, CHARTS.index(a)], Tr[i, CHARTS.index(b)]
        e = (ta >= TAU) & (tb >= TAU)
        return float((np.minimum(ta - TAU + 1, H) - np.minimum(tb - TAU + 1, H))[e].mean())

    # ---------------- P4
    y = {d: np.array([reps[r]["paired"][d][LAM]["rf - garch"]["dH"]["mean"] for r in range(R)]) for d in ["1.0", *DELTAS]}
    w = {d: np.array([reps[r]["paired"][d][LAM]["rf - garch"]["dH"]["se_mean"] for r in range(R)]) for d in y}
    y2 = {d: np.array([reps[r]["paired"][d]["0.2"]["rf - garch"]["dH"]["mean"] for r in range(R)]) for d in DELTAS}
    for i, d in enumerate(["1.0", *DELTAS]):
        check(f"P4 y_r(delta {d}) recomputed from paths.npz equals stored",
              all(pair_dh(T[r], i) == y[d][r] for r in range(R)))
    het = {}
    for d in ["1.0", *DELTAS]:
        q, i2 = cochran(y[d], w[d])
        a = est[f"paired/{d}/{LAM}/rf - garch/dH/mean"]
        het[d] = {"mean": float(y[d].mean()), "s_b": float(y[d].std(ddof=1)), "rms_mc_se": float(np.sqrt(np.mean(w[d] ** 2))),
                  "sd_between_resid_stored": a["sd_between_resid"], "Q": q, "I2": i2,
                  "n_pos": int((y[d] > 0).sum()), "n_neg": int((y[d] < 0).sum())}
        het[d]["ratio_sb_mcse"] = het[d]["s_b"] / het[d]["rms_mc_se"]
        check(f"P4 s_b(delta {d}) equals stored sd_between", math.isclose(het[d]["s_b"], a["sd_between"], rel_tol=1e-12))
    stab = {"delta 1.5 vs 2": rho(y["1.5"], y["2.0"]), "delta 2 vs 3": rho(y["2.0"], y["3.0"]),
            "delta 1.5 vs 3": rho(y["1.5"], y["3.0"]),
            **{f"lambda 0.1 vs 0.2 at delta {float(d):g}": rho(y[d], y2[d]) for d in DELTAS}}

    def per(f):
        return np.array([f(rep) for rep in reps], float)
    fd = lambda rep, c, k: rep["forecast_diag"][c][k]  # noqa: E731
    val = lambda rep, c, k: rep["validation"][LAM][c][k]  # noqa: E731
    preds = {
        "QLIKE_true(RF) − QLIKE_true(GARCH)": per(lambda rep: fd(rep, "rf", "qlike_true") - fd(rep, "garch", "qlike_true")),
        "RF responsiveness slope_h": per(lambda rep: fd(rep, "rf", "slope_h")),
        "Validated ARL₀ rel. deviation, RF − GARCH": per(lambda rep: val(rep, "rf", "rel_dev") - val(rep, "garch", "rel_dev")),
        "Validation P(T < τ), RF − GARCH": per(lambda rep: val(rep, "rf", "p_lt_tau") - val(rep, "garch", "p_lt_tau")),
        "GARCH persistence α̂ + β̂": per(lambda rep: rep["garch_fit"]["persistence"]),
    }
    mgap = {d: per(lambda rep, d=d: rep["masking"][d]["rf"]["M"] - rep["masking"][d]["garch"]["M"]) for d in DELTAS}
    assoc = {k: {d: rho(v, y[d]) for d in DELTAS} | {"range": [float(v.min()), float(v.max())]} for k, v in preds.items()}
    assoc["Masking gap M_RF − M_GARCH (same δ)"] = {d: rho(mgap[d], y[d]) for d in DELTAS} | {
        "range": [float(min(m.min() for m in mgap.values())), float(max(m.max() for m in mgap.values()))]}
    cell = [next(f"leaf {g['min_samples_leaf']}, max_features {g['max_features']}" for g in rep["rf_grid"] if g["selected"])
            for rep in reps]
    check("exactly one selected RF cell per replicate", all(sum(g["selected"] for g in rep["rf_grid"]) == 1 for rep in reps))
    groups = {c: {"n": cell.count(c), **{d: float(np.mean([y[d][r] for r in range(R) if cell[r] == c])) for d in DELTAS}}
              for c in sorted(set(cell), key=lambda c: -cell.count(c))}

    # ---------------- P5a: independent validation summaries (stored; lambda = 0.1)
    g500 = geom(A0)
    p5a = {}
    for c in CHARTS:
        v = [rep["validation"][LAM][c] for rep in reps]
        check(f"P5a {c}: N = 2000 and rel_dev = A/500 - 1",
              all(x["n_paths"] == 2000 and math.isclose(x["rel_dev"], x["arl_restricted"] / A0 - 1, abs_tol=1e-12) for x in v))
        A = np.array([x["arl_restricted"] for x in v])
        cv = np.array([x["se_arl_restricted"] * math.sqrt(x["n_paths"]) for x in v]) / A
        p5a[c] = {"A_val": tci(A), "cv": tci(cv), **{k + "/A": tci([x[k] for x in v] / A) for k in ("q10", "q50", "q90")},
                  "p_le_250": tci([x["p_le_250"] for x in v]), "p_lt_tau": tci([x["p_lt_tau"] for x in v])}
    p5a["geometric (A = 500)"] = {"A_val": g500["validation_mean"], "cv": g500["validation_cv"],
                                  "q10/A": g500["q10"] / A0, "q50/A": g500["q50"] / A0, "q90/A": g500["q90"] / A0,
                                  "p_le_250": g500["p_le_250"], "p_lt_tau": g500["p_lt_tau"]}

    # ---------------- P5b: delta = 1 OOC-stream paths (truncated at day 549; lambda = 0.1)
    p5b, S = {}, {}
    for m, c in enumerate(CHARTS):
        t1 = [T[r][0, m] for r in range(R)]
        ooc = [rep["ooc"]["1.0"][LAM][c] for rep in reps]
        pre = np.array([(x < TAU).mean() for x in t1])
        rmd = np.array([np.minimum(x[x >= TAU] - TAU + 1, H).mean() for x in t1])
        cen = np.array([(x[x >= TAU] == M + 1).mean() for x in t1])
        check(f"P5b {c}: P(T < tau), RMD and censoring among survivors recomputed equal stored ooc",
              all(math.isclose(a, o["p_prechange_fa"], rel_tol=1e-12) and math.isclose(b, o["rmd"], rel_tol=1e-12)
                  and math.isclose(e, o["censored"], rel_tol=1e-12) for a, b, e, o in zip(pre, rmd, cen, ooc)))
        gv = [geom(rep["validation"][LAM][c]["arl_restricted"]) for rep in reps]   # per-replicate A from validation
        p5b[c] = {"p_lt_tau": tci(pre), "geom_p_lt_tau": float(np.mean([g["p_lt_tau"] for g in gv])),
                  "rmd_given_survive": tci(rmd), "geom_rmd_given_survive": float(np.mean([g["rmd_given_survive"] for g in gv])),
                  "censored_given_survive": tci(cen),
                  "geom_censored_given_survive": float(np.mean([g["censored_given_survive"] for g in gv])),
                  "n_eval_mean": float(np.mean([(x >= TAU).sum() for x in t1]))}
        S[c] = np.mean([surv(x) for x in t1], axis=0)
    pairs = {}
    for a, b in [("rf", "garch"), ("rf", "conventional"), ("garch", "conventional")]:
        ia, ib = CHARTS.index(a), CHARTS.index(b)
        dpre = [((T[r][0, ia] < TAU).astype(float) - (T[r][0, ib] < TAU)).mean() for r in range(R)]
        ea = [(T[r][0, ia] >= TAU) for r in range(R)]
        eb = [(T[r][0, ib] >= TAU) for r in range(R)]
        both = np.array([(x & z).sum() for x, z in zip(ea, eb)])
        n_store = [rep["paired"]["1.0"][LAM][f"{a} - {b}"]["dH"]["n"] for rep in reps]
        check(f"P5b |E_{a} ∩ E_{b}| equals stored paired n", list(both) == n_store)
        pairs[f"{a} − {b}"] = {"diff_p_lt_tau": tci(dpre), "n_both_mean": float(both.mean()),
                               "excluded_by_one_only_mean": float(np.mean([(x ^ z).mean() for x, z in zip(ea, eb)]))}

    # ---------------- figure (P5): empirical survival, delta = 1 OOC-stream paths
    tt = np.arange(M + 1)
    sg = (1 - 1 / A0) ** tt
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    style = {"conventional": "C0-", "garch": "C1-", "rf": "C2-", "oracle": "k:"}
    label = {"conventional": "Conventional EWMA", "garch": "GARCH–EWMA", "rf": "RF–EWMA", "oracle": "GARCH, true parameters (diagnostic)"}
    for c in CHARTS:
        ax[0].plot(tt, S[c], style[c], lw=1.2, label=label[c])
        ax[1].plot(tt, 100 * (S[c] - sg), style[c], lw=1.2, label=label[c])
    ax[0].plot(tt, sg, color="grey", ls="--", lw=1, label="Geometric, ARL₀ = 500")
    ax[1].axhline(0, color="grey", ls="--", lw=1)
    for a_, yf in zip(ax, (0.3, 0.55)):            # label heights clear of the curves
        a_.axvline(TAU - 1, color="grey", lw=0.8)
        a_.annotate("t = 49: last pre-change day", (TAU - 1, yf), xycoords=("data", "axes fraction"),
                    xytext=(4, 0), textcoords="offset points", fontsize=7, color="grey")
        a_.set_xlabel("Monitoring day t (change point τ = 50 in shift scenarios)")
        a_.grid(alpha=0.3)
        a_.set_xlim(0, M)
    ax[0].set_ylabel("P(no alarm by day t)")
    ax[0].set_ylim(0.3, 1.0)
    ax[1].set_ylabel("Difference from geometric (percentage points)")
    ax[0].set_title("(a) Empirical in-control survival")
    ax[1].set_title("(b) Departure from the geometric benchmark")
    ax[0].legend(fontsize=8)
    ax[1].legend(fontsize=7, loc="lower right")
    fig.suptitle("No-change (δ = 1) paths of the out-of-control stream, λ = 0.1; equal-weight mean of R = 20 "
                 "systems × 2,000 paths (truncated at day 549; not the validation sample)", fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.94))

    # ---------------- outputs
    mods = sorted(m for m in sys.modules if m == "run" or m == "src" or m.startswith("src."))
    check("no project module imported", not mods)
    ok = all(c["ok"] for c in checks)
    f3 = lambda v: f"{v:.3g}"  # noqa: E731
    ci = lambda x, n=3: f"{x['mean']:.{n}f} [{x['ci95'][0]:.{n}f}, {x['ci95'][1]:.{n}f}]"  # noqa: E731
    out("## Table P4a. RF − GARCH paired RMD₅₀₀ (days), λ = 0.1: between-system heterogeneity (descriptive)")
    out("| δ | Mean | s_b | RMS MC SE | s_b / MC SE | σ̂_sys (stored) | Cochran Q (descr.) | I² (descr.) | Signs +/− |")
    out("|---|---|---|---|---|---|---|---|---|")
    for d, h in het.items():
        out(f"| {float(d):g} | {h['mean']:+.2f} | {h['s_b']:.2f} | {h['rms_mc_se']:.2f} | {h['ratio_sb_mcse']:.2f} | "
            f"{h['sd_between_resid_stored']:.2f} | {h['Q']:.1f} | {h['I2']:.2f} | {h['n_pos']}/{h['n_neg']} |")
    out("\n## Table P4b. Stability of system effects (Spearman ρ across the same 20 systems; descriptive)")
    out("| Comparison | ρ |\n|---|---|")
    for k, v in stab.items():
        out(f"| {k} | {v:+.2f} |")
    out("\n## Table P4c. Exploratory associations with y_r(δ) (Spearman ρ; descriptive, no p-values)")
    out("| Predictor (fixed in advance) | Range over systems | δ = 1.5 | δ = 2 | δ = 3 |\n|---|---|---|---|---|")
    for k, v in assoc.items():
        out(f"| {k} | {f3(v['range'][0])} to {f3(v['range'][1])} | {v['1.5']:+.2f} | {v['2.0']:+.2f} | {v['3.0']:+.2f} |")
    out("\n## Table P4d. Selected RF cell (categorical): group size and mean y_r(δ) (days)")
    out("| Selected cell | n | δ = 1.5 | δ = 2 | δ = 3 |\n|---|---|---|---|---|")
    for c, g in groups.items():
        out(f"| {c} | {g['n']} | {g['1.5']:+.1f} | {g['2.0']:+.1f} | {g['3.0']:+.1f} |")
    out("\n## Table P5a. Independent IC validation (N = 2,000 paths, horizon 5,000; stored summaries), λ = 0.1: "
        "replicate mean [95% t₁₉ CI]")
    out("| Chart | Validated ARL₀ | CV of run length | q10/A | q50/A | q90/A | P(T ≤ 250) | P(T < τ) |")
    out("|---|---|---|---|---|---|---|---|")
    for c, v in p5a.items():
        if c.startswith("geometric"):
            out(f"| {c} | {v['A_val']:.1f} | {v['cv']:.3f} | {v['q10/A']:.3f} | {v['q50/A']:.3f} | {v['q90/A']:.3f} | "
                f"{v['p_le_250']:.3f} | {v['p_lt_tau']:.3f} |")
        else:
            out(f"| {c} | {ci(v['A_val'], 1)} | {ci(v['cv'])} | {ci(v['q10/A'])} | {ci(v['q50/A'])} | {ci(v['q90/A'])} | "
                f"{ci(v['p_le_250'])} | {ci(v['p_lt_tau'])} |")
    out("\n## Table P5b. δ = 1 paths of the separate out-of-control stream (2,000 per system, truncated at day 549), λ = 0.1")
    out("| Chart | P(T < τ) [CI] | Geometric P(T < τ) | RMD₅₀₀ given T ≥ τ [CI] | Geometric, given T ≥ τ | "
        "P(no alarm by 549 ∣ T ≥ τ) [CI] | Geometric, given T ≥ τ | Mean ∣E_k∣ |")
    out("|---|---|---|---|---|---|---|---|")
    for c, v in p5b.items():
        out(f"| {c} | {ci(v['p_lt_tau'], 4)} | {v['geom_p_lt_tau']:.4f} | {ci(v['rmd_given_survive'], 1)} | "
            f"{v['geom_rmd_given_survive']:.1f} | {ci(v['censored_given_survive'])} | {v['geom_censored_given_survive']:.3f} | "
            f"{v['n_eval_mean']:.0f} |")
    out("\n## Table P5c. Paired pre-change false-alarm differences and survivor overlap (δ = 1 OOC-stream paths, λ = 0.1)")
    out("| Pair a − b | P(T_a < τ) − P(T_b < τ) [CI] | Mean ∣E_a ∩ E_b∣ | Fraction excluded by exactly one chart |")
    out("|---|---|---|---|")
    for k, v in pairs.items():
        out(f"| {k} | {ci(v['diff_p_lt_tau'], 4)} | {v['n_both_mean']:.0f} | {v['excluded_by_one_only_mean']:.3f} |")
    out(f"\nchecks: {len(checks)} run, {sum(not c['ok'] for c in checks)} failed")
    for c in checks:
        if not c["ok"]:
            out(f"FAILED: {c['check']}")
    out(f"VERDICT: {'PASS' if ok else 'FAIL'}")

    OUT.mkdir(parents=True)
    fig.savefig(OUT / "fig_rl_survival.png", dpi=150)
    plt.close(fig)
    text = "\n".join(lines) + "\n"
    (OUT / "p45_tables.md").write_text(text)
    (OUT / "p45_log.txt").write_text("selftest: all hand-computed checks passed\n" + text)
    (OUT / "p45_summary.json").write_text(json.dumps({
        "verdict": "PASS" if ok else "FAIL", "label": "exploratory, post hoc, descriptive (27 Oct 2026); primary analysis unchanged",
        "P4": {"heterogeneity": het, "stability_spearman": stab, "associations_spearman": assoc,
               "rf_cell_groups": groups, "selected_cell_by_replicate": cell},
        "P5": {"validation_summaries": p5a, "delta1_ooc_stream": p5b, "paired_prechange": pairs,
               "geometric_A500": g500, "survival_mean": {c: S[c].tolist() for c in CHARTS}},
        "checks": checks}, indent=1))
    git = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    (OUT / "p45_provenance.txt").write_text("\n".join([
        f"run_at: {datetime.now(timezone.utc).isoformat()}", f"git_head: {git}",
        f"python: {platform.python_version()}  numpy: {np.__version__}  scipy: {scipy.__version__}  "
        f"matplotlib: {matplotlib.__version__}",
        f"script_sha256: {hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}",
        *[f"input_sha256 {k}: {v}" for k, v in SHA.items()],
        f"input_sha256 audit_summary.json: {hashlib.sha256(P1.read_bytes()).hexdigest()}", ""]))
    print(text)
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        sys.exit(main())
