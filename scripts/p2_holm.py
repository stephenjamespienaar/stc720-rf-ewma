"""P2: supplementary, post hoc multiplicity analysis of the 12 primary contrasts.

Decided on 27 Oct 2026, after the primary production results were seen; the
pre-registered primary analysis (methodology §7.4: unadjusted estimates and t_19
CIs, no multiplicity adjustment) is unchanged. Family (fixed in advance of any
p-value): RF - GARCH and RF - conventional x RMD_500 and X(20) x delta in
{1.5, 2, 3}, lambda = 0.1. Test: two-sided one-sample t_19 test of the 20
equal-weight replicate contrasts (eq. 27 framework). Adjustment: Holm step-down,
FWER alpha = 0.05, decided on unrounded values. Robustness: Holm over the exact
sign tests, which test the balance of positive and negative replicate effects
(a different null from the mean-zero t-test).

Inputs are the frozen, P1-audited results.json and the committed P1 summary.
Imports neither `run` nor `src`; writes only to results/derived/p2_holm/.

    .venv/bin/python -I scripts/p2_holm.py --selftest
    .venv/bin/python -I scripts/p2_holm.py
"""

import hashlib
import json
import math
import platform
import subprocess
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

import numpy as np
import scipy
from scipy import stats
from statsmodels.stats.multitest import multipletests  # cross-check only

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results/runs/production_20261014T060921_145897/results.json"
RESULTS_SHA = "716862ab41d08c581d2bd65c63979c046a9d9cb5930c111381b3eeb6506b708b"
P1 = ROOT / "results/derived/p1_audit/audit_summary.json"
OUT = ROOT / "results/derived/p2_holm"
ALPHA, R = 0.05, 20
PAIRS = ["rf - garch", "rf - conventional"]
METRICS = ["dH", "x_20"]
FAMILY = [f"{d}/0.1/{p}/{m}" for p in PAIRS for m in METRICS for d in ("1.5", "2.0", "3.0")]
BASELINES = [f"1.0/0.1/{p}/dH" for p in PAIRS]          # context only, not in the family
TARGET = ("the mean paired contrast across independently generated and fitted monitoring systems "
          "under the specified simulation design (GARCH(1,1)-t DGP, ARL0 = 500, lambda = 0.1, H = 500, "
          "survivors E_a ∩ E_b); not consistent superiority in every fitted system, nor superiority "
          "in real markets")


def holm(p):
    """Holm step-down adjusted p-values: p~(i) = max_{j<=i} min(1, (m - j + 1) p(j)), in input order."""
    p = np.asarray(p, float)
    m, order = len(p), np.argsort(p, kind="stable")
    adj, rank, run = np.empty(m), np.empty(m, int), 0.0
    for j, i in enumerate(order):
        run = max(run, min(1.0, (m - j) * p[i]))
        adj[i], rank[i] = run, j + 1
    return adj, rank


def sign_p(npos, nneg):
    """Exact two-sided sign test (p = 1/2), zeros excluded."""
    n = npos + nneg
    tail = sum(Fraction(math.comb(n, i), 2**n) for i in range(min(npos, nneg) + 1))
    return float(min(Fraction(1), 2 * tail))


def ttest(x):
    """Two-sided one-sample t-test of mean 0 on replicate estimates, with the t CI (eq. 27)."""
    x = np.asarray(x, float)
    n, mean, sb = len(x), float(x.mean()), float(x.std(ddof=1))
    se = sb / math.sqrt(n)
    t = mean / se
    half = float(stats.t.ppf(0.975, n - 1)) * se
    return {"mean": mean, "sd_between": sb, "se": se, "t": t, "df": n - 1,
            "p": float(2 * stats.t.sf(abs(t), n - 1)), "ci95": [mean - half, mean + half]}


def selftest():
    adj, rank = holm([0.01, 0.04, 0.03, 0.005])
    # by hand: sorted 0.005, 0.01, 0.03, 0.04 -> 0.02, 0.03, 0.06, max(0.06, 0.04) = 0.06
    assert np.allclose(adj, [0.03, 0.06, 0.06, 0.02], rtol=0, atol=1e-15) and list(rank) == [2, 4, 3, 1]
    assert list(holm([0.6, 0.7])[0]) == [1.0, 1.0]                               # cap at 1
    r = ttest([1, 2, 3, 4])                                                     # t = 2.5 / (sqrt(5/3)/2) = sqrt(15)
    ref = stats.ttest_1samp([1, 2, 3, 4], 0.0)
    assert math.isclose(r["t"], math.sqrt(15)) and math.isclose(r["p"], ref.pvalue, rel_tol=1e-12)
    assert sign_p(4, 0) == 0.125 and sign_p(6, 14) == 120920 / 2**20 and sign_p(2, 1) == 1.0
    print("selftest: all hand-computed checks passed")


def main():
    selftest()
    if OUT.exists():
        sys.exit(f"refusing to overwrite {OUT}")
    log, checks = [], []

    def out(line=""):
        print(line)
        log.append(line)

    def check(name, ok):
        checks.append({"check": name, "ok": bool(ok)})

    raw = RESULTS.read_bytes()
    check("results.json SHA-256 equals the frozen, audited file", hashlib.sha256(raw).hexdigest() == RESULTS_SHA)
    est = json.loads(raw)["aggregate"]["estimands"]
    audited = {s["contrast"]: s for s in json.loads(P1.read_text())["primary_table"]}
    check("P1 verdict PASS", json.loads(P1.read_text())["verdict"] == "PASS")

    rows = {}
    for key in FAMILY + BASELINES:
        st, a = est[f"paired/{key}/mean"], audited[key]
        x = st["values"]
        check(f"{key}: R = 20 finite replicate values", st["R"] == R == len(x) and all(map(math.isfinite, x)))
        check(f"{key}: stored mean and CI equal the P1-audited values exactly",
              st["mean"] == a["mean"] and st["ci95"] == a["ci95"])
        r = ttest(x)
        ref = stats.ttest_1samp(x, 0.0)
        check(f"{key}: t and p equal scipy.stats.ttest_1samp",
              math.isclose(r["t"], ref.statistic, rel_tol=1e-12) and math.isclose(r["p"], ref.pvalue, rel_tol=1e-9))
        check(f"{key}: recomputed mean, s_b and t_19 CI equal the stored values (1e-10)",
              all(abs(u - v) <= 1e-10 * (1 + abs(v)) for u, v in
                  [(r["mean"], st["mean"]), (r["sd_between"], st["sd_between"]), *zip(r["ci95"], st["ci95"])]))
        check(f"{key}: CI-test duality (0 outside the 95% CI iff p < 0.05)",
              (r["ci95"][0] > 0 or r["ci95"][1] < 0) == (r["p"] < 0.05))
        npos, nneg = int(sum(v > 0 for v in x)), int(sum(v < 0 for v in x))
        sp = sign_p(npos, nneg)
        check(f"{key}: sign counts and exact sign p equal the stored values",
              (npos, nneg) == (st["n_pos"], st["n_neg"]) and math.isclose(sp, st["sign_p"], rel_tol=1e-12))
        rows[key] = {"contrast": key, **r, "n_pos": npos, "n_neg": nneg, "sign_p": sp,
                     "paired_n_range": [a["n_min"], a["n_max"]], "in_family": key in FAMILY}

    p = [rows[k]["p"] for k in FAMILY]
    adj, rank = holm(p)
    sp = [rows[k]["sign_p"] for k in FAMILY]
    sadj, _ = holm(sp)
    sm = multipletests(p, alpha=ALPHA, method="holm")
    check("Holm (t) equals statsmodels multipletests(method='holm') to 1e-12",
          np.allclose(adj, sm[1], rtol=0, atol=1e-12) and list(sm[0]) == list(adj <= ALPHA))
    check("Holm (sign) equals statsmodels to 1e-12",
          np.allclose(sadj, multipletests(sp, alpha=ALPHA, method="holm")[1], rtol=0, atol=1e-12))
    check("adjusted p >= raw p, and nondecreasing in Holm rank",
          bool((adj >= np.asarray(p)).all() and (np.diff(adj[np.argsort(rank)]) >= 0).all()))
    for k, a_, r_, s_ in zip(FAMILY, adj, rank, sadj):
        rows[k] |= {"holm_rank": int(r_), "p_holm": float(a_), "reject_fwer_0.05": bool(a_ <= ALPHA),
                    "sign_p_holm": float(s_), "sign_reject_fwer_0.05": bool(s_ <= ALPHA)}

    mods = sorted(m for m in sys.modules if m == "run" or m == "src" or m.startswith("src."))
    check("no project module imported", not mods)
    ok = all(c["ok"] for c in checks)

    def f(v):
        return f"{v:.3g}"

    name = {"dH": "RMD₅₀₀", "x_20": "X(20)"}
    lines = ["| Contrast | δ | Estimate | Unadjusted 95% t₁₉ CI | s_b | t₁₉ | Raw p | Holm rank | Holm p "
             "| Reject (FWER 0.05) | Signs +/− | Sign p (raw / Holm) |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k in FAMILY + BASELINES:
        r = rows[k]
        d, _, pair, m = k.split("/")
        dec = 4 if m == "x_20" else 2
        est_ = f"{r['mean']:+.{dec}f}"
        ci = f"[{r['ci95'][0]:+.{dec}f}, {r['ci95'][1]:+.{dec}f}]"
        tail = (f"{r['holm_rank']} | {f(r['p_holm'])} | {'yes' if r['reject_fwer_0.05'] else 'no'} | "
                f"{r['n_pos']}/{r['n_neg']} | {f(r['sign_p'])} / {f(r['sign_p_holm'])}") if r["in_family"] else \
               f"– | – | context, not in family | {r['n_pos']}/{r['n_neg']} | {f(r['sign_p'])} / –"
        label = pair.replace("rf", "RF").replace("garch", "GARCH").replace(" - ", " − ")
        lines.append(f"| {label}, {name[m]} | {float(d):g} | "
                     f"{est_} | {ci} | {r['sd_between']:.3g} | {r['t']:+.3f} | {f(r['p'])} | {tail} |")
    table = "\n".join(lines)

    summary = {"verdict": "PASS" if ok else "FAIL", "label": "supplementary, post hoc (decided 27 Oct 2026 after "
               "the primary production results were seen); not a pre-registered adjustment",
               "inferential_target": TARGET, "family": FAMILY, "alpha": ALPHA, "test": "two-sided one-sample t, df 19",
               "adjustment": "Holm step-down (valid under arbitrary dependence)",
               "robustness": "exact two-sided sign test, Holm-adjusted; tests the balance of positive and negative "
                             "replicate effects, a different null from the mean-zero t-test",
               "n_reject_t": int((adj <= ALPHA).sum()), "n_reject_sign": int((sadj <= ALPHA).sum()),
               "rows": [rows[k] for k in FAMILY + BASELINES], "checks": checks}

    OUT.mkdir(parents=True)
    (OUT / "holm_summary.json").write_text(json.dumps(summary, indent=1))   # full float precision (repr)
    (OUT / "holm_table.md").write_text(table + "\n")
    out(f"checks: {len(checks)} run, {sum(not c['ok'] for c in checks)} failed")
    for c in checks:
        if not c["ok"]:
            out(f"  FAILED: {c['check']}")
    out(f"family of {len(FAMILY)}; rejected at FWER {ALPHA}: t-test Holm {summary['n_reject_t']}, "
        f"sign-test Holm {summary['n_reject_sign']}")
    out(table)
    out(f"VERDICT: {summary['verdict']}")
    (OUT / "p2_log.txt").write_text("selftest: all hand-computed checks passed\n" + "\n".join(log) + "\n")
    git = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    (OUT / "p2_provenance.txt").write_text("\n".join([
        f"run_at: {datetime.now(timezone.utc).isoformat()}", f"git_head: {git}",
        f"python: {platform.python_version()}  numpy: {np.__version__}  scipy: {scipy.__version__}  "
        f"statsmodels: {sys.modules['statsmodels'].__version__}",
        f"script_sha256: {hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}",
        f"input_sha256 results.json: {hashlib.sha256(raw).hexdigest()}",
        f"input_sha256 audit_summary.json: {hashlib.sha256(P1.read_bytes()).hexdigest()}", ""]))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        sys.exit(main())
