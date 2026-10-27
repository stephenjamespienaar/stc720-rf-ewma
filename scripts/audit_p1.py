"""P1: independent audit of the frozen production run (methodology eqs. 17, 23, 24, 27, 28).

Recomputes the 12 primary paired contrasts and their four delta = 1 baselines
(RF - GARCH and RF - conventional; RMD_500 and X(20); lambda = 0.1) from the
per-path alarm days in paths.npz, then compares them with results.json. It is
written from the methodology alone: it imports neither `run` nor `src` (run it
with `python -I`, so the project root is not on sys.path; this is asserted at
exit). Read-only on results/runs/; writes only to results/derived/p1_audit/.

    .venv/bin/python -I scripts/audit_p1.py --selftest   # hand-computed checks only
    .venv/bin/python -I scripts/audit_p1.py              # self-test, then the audit
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

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "results/runs/production_20261014T060921_145897"
OUT = ROOT / "results/derived/p1_audit"

# Recorded in .claude/skills/stc720-project/references/production-results.md and
# re-hashed on 27 Oct 2026 before this audit was written.
FILES = {
    "config.json": "897cf519889a117a7282592b9f7108e74eba4ef0bd047201e37261fba340c130",
    "exit_status.txt": "9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa",
    "fig_delay.png": "e3ff5f011f9d7a215407740b1eaa8b18d5797f6dd9f24eeeaa886a519bbe6533",
    "fig_profile.png": "a409411c285eab910ff5f126cef3c9e95ab51047ba23ea436adca9f7226a3f4c",
    "fig_replicates.png": "1af6a11058e6e014397befbbff7a0d6c060f96a277a64293aaeda8456225aecb",
    "git_diff_stat.txt": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "git_status.txt": "310ddd6a95fc9ced5695328a53d21f12d5811abaed0816b15de01e2b2b8ad78a",
    "paths.npz": "0055f1e115e6cd676d88dcc0875dfee19c44018afc8154658b40be9a2ab8cdf3",
    "pip_freeze.txt": "56dfb8c67769f500263680943dd52da6bad044185113742b2977443772cc6557",
    "provenance.txt": "40b6a2af8338f2614e352670e3b90e1df3a53ab9656cd0d38fb900fbdbd676b6",
    "resources.txt": "0bd11ee4c1ea9331361388f7303a08b669fab3dfba3d37d9b4581e943f699678",
    "results.json": "716862ab41d08c581d2bd65c63979c046a9d9cb5930c111381b3eeb6506b708b",
    "source_sha256.txt": "746e9cf88ecbbb127b2bfc4806e4212baa68e8783062cf3184bbb707520f6747",
    "stderr.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "stdout.log": "e686750dbb0911fe0acc854d9655eea677a29493106b81dde67339dc98808bd0",
    "tables.md": "7757c948017b6ee2ef6ed04411534404fe03ea77774ac2de517b8a93ead0dc39",
    "time.txt": "847cb2a5c834f2ae250a8d58b66693a6c208f35db5562210e842f9de5bdd90c5",
}
RESULTS_SHA = "44410144e3feb4a762dd2044fec07a2ddc64fdc742d43637332cc03f731431b8"

TAU, H = 50, 500
M = TAU - 1 + H                      # 549 monitored days; T = M + 1 = 550 is the censoring sentinel
CHARTS = ["conventional", "garch", "rf", "oracle"]   # chart axis of paths.npz (perpath_axes)
DELTAS = [1.0, 1.5, 2.0, 3.0]                        # index 0 = no-change counterfactual
LAMS = [0.1, 0.2]
PRIMARY_PAIRS = [("rf", "garch"), ("rf", "conventional")]
ALL_PAIRS = PRIMARY_PAIRS + [("garch", "conventional")]
ATOL = RTOL = 1e-10


# ---------------------------------------------------------------- estimators (from the methodology)

def delays(T):
    """D_H = min(T - tau + 1, H) (eq. 17), NaN for pre-change alarms (T < tau), and the
    censoring flag T = M + 1. An alarm on day M has D = H and is a detection."""
    T = np.asarray(T, dtype=np.int64)
    if T.min() < 1 or T.max() > M + 1:
        raise ValueError("alarm day outside 1 .. M + 1")
    d = np.minimum(T - TAU + 1, H).astype(float)
    d[T < TAU] = np.nan
    return d, T == M + 1


def hit(d, cens, k):
    """1{D <= k}; censored paths are never detections."""
    return ((d <= k) & ~cens).astype(float)


def paired(Ta, Tb, Ta1, Tb1, metric):
    """Matched contrast a - b over E_a ∩ E_b (eq. 23). Ta, Tb: alarm days at delta;
    Ta1, Tb1: the same paths at delta = 1. metric 'dH' (restricted delay) or 'x_k'
    (paired excess detection, eq. 24). The SE is sd(ddof = 1)/sqrt(n) of the complete
    matched per-path contrast; None (not identifiable) when n < 2."""
    (da, ca), (db, cb), (da1, ca1), (db1, cb1) = map(delays, (Ta, Tb, Ta1, Tb1))
    for x, x1 in ((da, da1), (db, db1)):
        if not np.array_equal(np.isnan(x), np.isnan(x1)):
            raise ValueError("survivor sets differ between delta and delta = 1 (CRN pairing broken)")
    E = ~np.isnan(da) & ~np.isnan(db)
    if metric == "dH":
        y = da - db
    else:
        k = int(metric[2:])
        y = (hit(da, ca, k) - hit(da1, ca1, k)) - (hit(db, cb, k) - hit(db1, cb1, k))
    y = y[E]
    n = len(y)
    mean = float(y.mean()) if n else None
    se = float(y.std(ddof=1) / math.sqrt(n)) if n > 1 else None
    ci = [mean - 1.96 * se, mean + 1.96 * se] if se is not None else [None, None]
    return {"mean": mean, "se_mean": se, "n": n, "ci95": ci}


def sign_p_exact(npos, nneg):
    """Exact two-sided sign test, p = 1/2: min(1, 2 P(X <= min(npos, nneg)))."""
    n = npos + nneg
    tail = sum(Fraction(math.comb(n, i), 2**n) for i in range(min(npos, nneg) + 1))
    return float(min(Fraction(1), 2 * tail))


def across(x, w):
    """Equal-weight replicate aggregate (eq. 27) with the residual between-system
    variance (eq. 28, descriptive)."""
    x, w = np.asarray(x, float), np.asarray(w, float)
    R = len(x)
    sb = float(x.std(ddof=1))
    half = float(stats.t.ppf(0.975, R - 1)) * sb / math.sqrt(R)
    mean = float(x.mean())
    npos, nneg = int((x > 0).sum()), int((x < 0).sum())
    mw2 = float(np.mean(w**2))
    s = {"R": R, "mean": mean, "min": float(x.min()), "max": float(x.max()), "n_pos": npos, "n_neg": nneg,
         "sd_between": sb, "ci95": [mean - half, mean + half], "rms_mc_se": math.sqrt(mw2),
         "var_between_resid": max(0.0, sb**2 - mw2)}
    s["sd_between_resid"] = math.sqrt(s["var_between_resid"])
    if npos + nneg:
        s["sign_p"] = float(stats.binomtest(npos, npos + nneg).pvalue)
        s["sign_p_exact"] = sign_p_exact(npos, nneg)
    return s


# ---------------------------------------------------------------- hand-computed self-test

def selftest():
    """Eight hand-worked paths, tau = 50, M = 549. Expected values were computed by hand
    (comments), not by this code. Charts a and b have different survivor sets."""
    #             p0   p1   p2   p3   p4   p5   p6   p7
    Ta1 = np.array([49, 200, 550, 549, 300, 69, 45, 60])
    Ta = np.array([49, 60, 550, 549, 50, 60, 45, 55])
    Tb1 = np.array([300, 40, 550, 100, 400, 550, 47, 120])
    Tb = np.array([120, 40, 69, 50, 400, 70, 47, 69])
    # Survivors: E_a = {1,2,3,4,5,7} (6), E_b = {0,2,3,4,5,7} (6), E_a ∩ E_b = {2,3,4,5,7} (5).
    d, c = delays(Ta)
    assert np.isnan(d[[0, 6]]).all() and (~np.isnan(d)).sum() == 6
    assert d[2] == 500 and c[2] and d[3] == 500 and not c[3] and d[4] == 1
    assert hit(d, c, 500)[2] == 0 and hit(d, c, 500)[3] == 1          # T = 550 censored, T = 549 detected
    # RMD at delta: a - b = 480, 499, -350, -10, -14 -> mean 605/5; deviations 359, 378, -471, -131, -135.
    r = paired(Ta, Tb, Ta1, Tb1, "dH")
    assert r["n"] == 5 and r["mean"] == 121.0 and math.isclose(r["se_mean"], math.sqrt(528992 / 4 / 5))
    # Difference of per-chart RMDs over their own sets (1029/6 - 484/6) differs from the paired 121.
    assert math.isclose(np.nanmean(d) - np.nanmean(delays(Tb)[0]), 1029 / 6 - 484 / 6)
    # RMD at delta = 1: 0, 449, -100, -480, -60 -> mean -191/5.
    r1 = paired(Ta1, Tb1, Ta1, Tb1, "dH")
    assert r1["n"] == 5 and math.isclose(r1["mean"], -38.2)
    # X(20): x_a = 0,0,1,0,0 (p5: D(1) = 20 counts, boundary D = k); x_b = 1,1,0,0,1
    # y = -1,-1,1,0,-1 -> mean -0.4, sd^2 = 3.2/4, SE = sqrt(0.8/5) = 0.4.
    x = paired(Ta, Tb, Ta1, Tb1, "x_20")
    assert x["n"] == 5 and math.isclose(x["mean"], -0.4) and math.isclose(x["se_mean"], 0.4)
    x1 = paired(Ta1, Tb1, Ta1, Tb1, "x_20")
    assert x1["mean"] == 0.0 and x1["se_mean"] == 0.0                 # delta = 1: zero by construction
    # Not identifiable: n = 1 -> SE None; n = 0 -> mean None.
    one = paired(Ta[[2, 6]], Tb[[2, 6]], Ta1[[2, 6]], Tb1[[2, 6]], "dH")
    assert one["n"] == 1 and one["mean"] == 480.0 and one["se_mean"] is None and one["ci95"] == [None, None]
    assert paired(Ta[[0]], Tb[[0]], Ta1[[0]], Tb1[[0]], "dH")["mean"] is None
    # A survivor at delta = 1 that false-alarms at delta breaks CRN pairing.
    try:
        paired(np.array([40]), np.array([100]), np.array([60]), np.array([100]), "dH")
        raise AssertionError("CRN pairing violation not detected")
    except ValueError:
        pass
    # Aggregation: x = 1..4 -> mean 2.5, s_b^2 = 5/3, t_{3,0.975} = 3.182446; sign test 4/0 -> p = 2/16.
    a = across([1, 2, 3, 4], [1, 1, 1, 1])
    assert a["mean"] == 2.5 and math.isclose(a["sd_between"] ** 2, 5 / 3)
    assert math.isclose(a["ci95"][1] - 2.5, 3.182446305 * math.sqrt(5 / 3) / 2, rel_tol=1e-8)
    assert a["sign_p"] == a["sign_p_exact"] == 0.125 and math.isclose(a["var_between_resid"], 2 / 3)
    b = across([1, -1, 2, 0], [0, 0, 0, 0])                          # zero excluded: 2/1 -> p = 1
    assert (b["n_pos"], b["n_neg"]) == (2, 1) and b["sign_p_exact"] == 1.0
    assert round(float(stats.t.ppf(0.975, 19)), 3) == 2.093
    print("selftest: all hand-computed checks passed")


# ---------------------------------------------------------------- audit

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    selftest()
    if OUT.exists():
        sys.exit(f"refusing to overwrite {OUT}")
    rows, checks = [], []

    def check(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    def cmp(where, field, mine, stored, primary):
        if mine is None or stored is None:
            cls = "EXACT" if mine is None and stored is None else "MISMATCH"
            diff = None
        elif isinstance(mine, (int, np.integer)) and isinstance(stored, int):
            cls, diff = ("EXACT" if mine == stored else "MISMATCH"), abs(int(mine) - stored)
        else:
            diff = abs(float(mine) - float(stored))
            cls = "EXACT" if mine == stored else "FP" if diff <= ATOL + RTOL * abs(stored) else "MISMATCH"
        rows.append({"where": where, "field": field, "independent": mine, "stored": stored,
                     "abs_diff": diff, "class": cls, "primary": primary})

    # A. Integrity and identity.
    actual = {p.name: sha256(p) for p in sorted(RUN.iterdir())}
    check("file set equals the 17 recorded files", set(actual) == set(FILES), sorted(set(actual) ^ set(FILES)))
    for name, h in FILES.items():
        check(f"sha256 {name}", actual.get(name) == h)
    res = json.loads((RUN / "results.json").read_text())
    cfg_file = json.loads((RUN / "config.json").read_text())
    core = {k: v for k, v in res.items() if k not in ("timing", "environment", "results_sha256", "started")}
    rh = hashlib.sha256(json.dumps(core, sort_keys=True, default=float).encode()).hexdigest()
    check("results_sha256 recomputed", rh == res["results_sha256"] == RESULTS_SHA, rh)
    cfg = res["config"]
    check("config.json equals results.json config, mode and seeds",
          cfg_file["config"] == cfg and cfg_file["mode"] == res["mode"] and cfg_file["seeds"] == res["seeds"])
    check("design: production, R = 20, seed 20261014, ARL0 500, tau 50, H 500, deltas, lambdas",
          res["mode"] == "production" and cfg["replicates"] == 20 == len(res["replicates"])
          and cfg["master_seed"] == 20261014 == res["seeds"]["master_seed"] and cfg["target_arl"] == 500
          and cfg["tau"] == TAU and cfg["H"] == H and cfg["deltas"] == DELTAS[1:] and cfg["lams"] == LAMS)
    check("primary spec", cfg["primary"]["lam"] == 0.1 and cfg["primary"]["metrics"] == ["dH", "x_20"]
          and cfg["primary"]["pairs"] == [f"{a} - {b}" for a, b in PRIMARY_PAIRS])
    keys = res["seeds"]["spawn_keys"]
    check("20 distinct replicate spawn keys", sorted(map(int, keys)) == list(range(20))
          and len({tuple(v) for r in keys.values() for v in r.values()}) == 140)
    ax = res["perpath_axes"]
    check("paths.npz axes", ax["delta"] == DELTAS and ax["lam"] == LAMS and ax["chart"] == CHARTS
          and ax["T"] == ["delta", "lam", "chart", "path"])

    npz = np.load(RUN / "paths.npz")
    check("paths.npz holds exactly r0..r19 x {T, occ, uS, uE}",
          sorted(npz.files) == sorted(f"r{r}_{k}" for r in range(20) for k in ("T", "occ", "uS", "uE")))
    Ts = []
    for r in range(20):
        pp = {k: npz[f"r{r}_{k}"] for k in ("T", "occ", "uS", "uE")}
        ph = hashlib.sha256(b"".join(f"{k}{pp[k].dtype}{pp[k].shape}".encode()
                                     + np.ascontiguousarray(pp[k]).tobytes() for k in sorted(pp))).hexdigest()
        check(f"r{r} perpath_sha256 recomputed from paths.npz", ph == res["replicates"][r]["perpath_sha256"])
        Ts.append(pp["T"])

    # B. Per-path coding invariants.
    tally = {}
    for r, T in enumerate(Ts):
        check(f"r{r} T shape, integer dtype, range 1..{M + 1}", T.shape == (4, 2, 4, 2000)
              and np.issubdtype(T.dtype, np.integer) and T.min() >= 1 and T.max() <= M + 1)
        for j, lam in enumerate(LAMS):
            for m, ch in enumerate(CHARTS):
                pre = T[0, j, m] < TAU
                same = all(np.array_equal(T[i, j, m] < TAU, pre) and np.array_equal(T[i, j, m][pre], T[0, j, m][pre])
                           for i in range(4))
                check(f"r{r} lam {lam} {ch}: pre-change alarms identical across delta (CRN)", same)
                for i, dl in enumerate(DELTAS):
                    t = tally.setdefault(f"{dl}/{lam}/{ch}", {"prechange": 0, "censored_550": 0, "alarm_day_549": 0})
                    t["prechange"] += int((T[i, j, m] < TAU).sum())
                    t["censored_550"] += int((T[i, j, m] == M + 1).sum())
                    t["alarm_day_549"] += int((T[i, j, m] == M).sum())
            c = T[:, j, 0]
            check(f"r{r} lam {lam} conventional: T nonincreasing in delta pathwise",
                  bool((np.diff(c, axis=0) <= 0).all()))

    # C-D. Per-replicate contrasts and their aggregates.
    summary = []
    for dl in DELTAS:
        for j, lam in enumerate(LAMS):
            for a, b in ALL_PAIRS:
                ia, ib = CHARTS.index(a), CHARTS.index(b)
                for metric in ("dH", "x_5", "x_20", "x_60"):
                    primary = lam == 0.1 and (a, b) in PRIMARY_PAIRS and metric in ("dH", "x_20")
                    i = DELTAS.index(dl)
                    key = f"{dl}/{lam}/{a} - {b}/{metric}"
                    mine = [paired(T[i, j, ia], T[i, j, ib], T[0, j, ia], T[0, j, ib], metric) for T in Ts]
                    for r, x in enumerate(mine):
                        st = res["replicates"][r]["paired"][str(dl)][str(lam)][f"{a} - {b}"][metric]
                        for f in ("mean", "se_mean", "n"):
                            cmp(f"r{r}/{key}", f, x[f], st[f], primary)
                        for q in (0, 1):
                            cmp(f"r{r}/{key}", f"ci95[{q}]", x["ci95"][q], st["ci95"][q], primary)
                    vals = [x["mean"] for x in mine]
                    agg = across(vals, [x["se_mean"] for x in mine])
                    ns = [x["n"] for x in mine]
                    sk = f"paired/{key}/mean"
                    stored = res["aggregate"]["estimands"].get(sk)
                    if dl == 1.0 and metric != "dH":
                        # Zero by construction; deliberately not aggregated in results.json.
                        check(f"{key}: all 20 replicate values exactly 0 (and not aggregated)",
                              all(v == 0.0 for v in vals) and stored is None)
                    elif stored is None:
                        check(f"{key}: stored aggregate present", False)
                    else:
                        check(f"{sk}: stored values list = stored per-replicate means, R = 20",
                              stored["R"] == 20 and stored["values"] == [
                                  res["replicates"][r]["paired"][str(dl)][str(lam)][f"{a} - {b}"][metric]["mean"]
                                  for r in range(20)])
                        for f in ("mean", "min", "max", "n_pos", "n_neg", "sd_between", "rms_mc_se",
                                  "var_between_resid", "sd_between_resid", "sign_p"):
                            cmp(f"agg/{key}", f, agg.get(f), stored.get(f), primary)
                        for q in (0, 1):
                            cmp(f"agg/{key}", f"ci95[{q}]", agg["ci95"][q], stored["ci95"][q], primary)
                        if "sign_p" in agg:
                            check(f"{key}: scipy sign p = exact sign p",
                                  math.isclose(agg["sign_p"], agg["sign_p_exact"], rel_tol=1e-12))
                        sn = res["aggregate"]["counts"].get(f"paired/{key}/n")
                        check(f"{key}: paired n per replicate = stored counts", sn is not None and sn["values"] == ns)
                    if primary:
                        summary.append({"contrast": key, "role": "primary" if dl != 1.0 else "delta = 1 baseline",
                                        "n_min": min(ns), "n_max": max(ns),
                                        "n_unidentified_se": sum(x["se_mean"] is None for x in mine),
                                        **{k: agg[k] for k in ("mean", "ci95", "sd_between", "rms_mc_se",
                                                               "sd_between_resid", "n_pos", "n_neg")},
                                        "sign_p": agg.get("sign_p"),
                                        "stored_mean": stored["mean"] if stored else None})

    for s in summary:
        own = [x for x in rows if x["where"].endswith("/" + s["contrast"])]
        s["fields_compared"] = len(own)
        s["max_abs_diff"] = max((x["abs_diff"] or 0.0) for x in own)
        s["worst_class"] = max((x["class"] for x in own), key=["EXACT", "FP", "MISMATCH"].index)

    mods = sorted(m for m in sys.modules if m == "run" or m == "src" or m.startswith("src."))
    check("no project module imported (run, src, src.*)", not mods, mods)

    def tally_rows(sel):
        return {c: sum(x["class"] == c for x in sel) for c in ("EXACT", "FP", "MISMATCH")}

    prim = [x for x in rows if x["primary"]]
    verdict = ("PASS" if all(c["ok"] for c in checks) and tally_rows(rows)["MISMATCH"] == 0 else "FAIL")
    out = {"verdict": verdict, "tolerance": {"atol": ATOL, "rtol": RTOL},
           "classes_primary": tally_rows(prim), "classes_all": tally_rows(rows),
           "max_abs_diff_primary": max(x["abs_diff"] or 0.0 for x in prim),
           "max_abs_diff_all": max(x["abs_diff"] or 0.0 for x in rows),
           "checks_failed": [c for c in checks if not c["ok"]], "n_checks": len(checks),
           "primary_table": summary, "boundary_counts_over_20_replicates": tally}

    OUT.mkdir(parents=True)
    (OUT / "audit_summary.json").write_text(json.dumps(out, indent=1))
    (OUT / "audit_rows.json").write_text(json.dumps({"checks": checks, "rows": rows}))
    git = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    (OUT / "audit_provenance.txt").write_text("\n".join([
        f"run_at: {datetime.now(timezone.utc).isoformat()}", f"git_head: {git}",
        f"python: {platform.python_version()}  numpy: {np.__version__}  scipy: {scipy.__version__}",
        f"script_sha256: {sha256(__file__)}", f"input: {RUN.relative_to(ROOT)}",
        *[f"input_sha256 {k}: {v}" for k, v in actual.items()], ""]))

    print(f"checks: {len(checks)} run, {len(out['checks_failed'])} failed")
    for c in out["checks_failed"]:
        print("  FAILED:", c["check"], c["detail"])
    print(f"comparisons primary: {out['classes_primary']}  max |diff| {out['max_abs_diff_primary']:.3g}")
    print(f"comparisons all:     {out['classes_all']}  max |diff| {out['max_abs_diff_all']:.3g}")
    for s in summary:
        print(f"  {s['contrast']:<38} {s['mean']:+10.5f} [{s['ci95'][0]:+.5f}, {s['ci95'][1]:+.5f}]"
              f"  +{s['n_pos']}/-{s['n_neg']}  n {s['n_min']}-{s['n_max']}  {s['worst_class']}")
    print(f"VERDICT: {verdict}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        sys.exit(main())
