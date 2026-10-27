"""Mathematical and numerical correctness tests (methodology equation numbers in brackets)."""

import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

import run
from src import aggregate, chart, report, sim, spy
from src import forecast as fc

P = sim.Garch(**run.DGP)


def rng(seed=0):
    return np.random.default_rng(seed)


# --- DGP and constraints (eqs. 2-6) -------------------------------------------------

def test_default_dgp_satisfies_all_constraints():
    assert sim.constraint_violations(P) == []
    assert P.var == pytest.approx(1.0)
    assert P.kappa == pytest.approx(6.0)
    assert P.m4 == pytest.approx(0.91**2 + 2 * 0.07 * 0.91 + 6 * 0.07**2)
    assert P.m4 < 0.99


@pytest.mark.parametrize("bad, msg", [
    (sim.Garch(0.0, 0.07, 0.91, 6), "omega > 0"),
    (sim.Garch(0.02, -0.1, 0.91, 6), "alpha, beta >= 0"),
    (sim.Garch(0.02, 0.10, 0.90, 6), "alpha + beta < 1"),
    (sim.Garch(0.02, 0.07, 0.91, 3.5), "nu > 4"),
    (sim.Garch(0.02, 0.08, 0.90, 5), "m4"),          # 0.81 + 0.144 + 9*0.0064 = 1.0116
])
def test_constraint_violations_detected(bad, msg):
    v = sim.constraint_violations(bad)
    assert any(msg in s for s in v)
    with pytest.raises(ValueError):
        sim.check(bad)


def test_simulated_variance_follows_garch_recursion():
    r, h = sim.simulate(P, 3, 200, rng(1), burn=50)
    assert (h > 0).all()
    np.testing.assert_allclose(h[:, 1:], P.omega + P.alpha * r[:, :-1] ** 2 + P.beta * h[:, :-1])


def test_standardized_t_has_unit_variance():
    e = sim.std_t(rng(2), 6.0, 2_000_000)
    assert e.var() == pytest.approx(1.0, abs=0.01)


def test_scale_shift_equals_garch_with_scaled_omega():
    r, h = sim.simulate(P, 2, 120, rng(3), burn=50)
    ro, ho = sim.scale_shift(r, h, 60, 2.0)
    np.testing.assert_array_equal(ro[:, :60], r[:, :60])
    np.testing.assert_allclose(ro[:, 60:], np.sqrt(2.0) * r[:, 60:])
    # after the change: GARCH(2 omega, alpha, beta) on the observed returns (eq. 6)
    np.testing.assert_allclose(ho[:, 61:], 2 * P.omega + P.alpha * ro[:, 60:-1] ** 2 + P.beta * ho[:, 60:-1])


# --- forecasters: timing, positivity, frozen models (eqs. 8-11) ------------------------

def test_features_match_brute_force_and_use_only_past():
    r = rng(4).standard_normal((2, 80))
    x = fc.har_features(r)
    for t in (22, 40, 79):
        for k, L in enumerate(fc.LAGS):
            assert x[1, t, k] == pytest.approx(np.mean(r[1, t - L:t] ** 2))
    assert np.isnan(x[:, :22, 2]).all()


@pytest.mark.parametrize("t0", [25, 50, 78])
def test_no_lookahead_in_features_and_garch_filter(t0):
    r = rng(5).standard_normal((3, 80))
    r2 = r.copy()
    r2[:, t0:] += 10.0  # change r_t0 and everything after it
    np.testing.assert_array_equal(fc.har_features(r)[:, : t0 + 1], fc.har_features(r2)[:, : t0 + 1])
    np.testing.assert_array_equal(fc.garch_filter(r, P)[:, : t0 + 1], fc.garch_filter(r2, P)[:, : t0 + 1])
    assert not np.array_equal(fc.garch_filter(r, P)[:, t0 + 1], fc.garch_filter(r2, P)[:, t0 + 1])


def test_garch_filter_starts_at_unconditional_variance():
    r = rng(6).standard_normal((1, 5))
    hh = fc.garch_filter(r, P)
    assert hh[0, 0] == pytest.approx(P.var)
    assert hh[0, 1] == pytest.approx(P.omega + P.alpha * r[0, 0] ** 2 + P.beta * P.var)


@pytest.fixture(scope="module")
def small_rf():
    r = sim.simulate(P, 1, 1500, rng(7), burn=100)[0][0]
    return r, fc.fit_rf(r, 50, 1, 20, seed=11, n_jobs=2)


def test_rf_prediction_matches_sklearn_and_is_positive(small_rf):
    r, m = small_rf
    x = fc.har_features(sim.simulate(P, 4, 300, rng(8), burn=100)[0])[:, 22:]
    f, binds = fc.predict_rf(m, x, floor=0.0, n_jobs=3, chunk=97)
    np.testing.assert_allclose(f.ravel(), m.predict(x.reshape(-1, 3).astype(np.float32)), rtol=1e-12)
    y = r[22:] ** 2
    assert binds == 0 and (f > 0).all() and f.min() >= y.min() and f.max() <= y.max()  # convex combination


def test_rf_floor_binds_and_is_counted(small_rf):
    _, m = small_rf
    x = fc.har_features(rng(9).standard_normal((2, 60)))[:, 22:]
    f, binds = fc.predict_rf(m, x, floor=1e6)
    assert binds == f.size and (f == 1e6).all()


def test_rf_prediction_is_deterministic_and_model_frozen(small_rf):
    _, m = small_rf
    fp = hashlib.sha256(b"".join(e.tree_.value.tobytes() for e in m.estimators_)).hexdigest()
    x = fc.har_features(rng(10).standard_normal((5, 400)))[:, 22:]
    a, _ = fc.predict_rf(m, x, 0.0, n_jobs=1)
    b, _ = fc.predict_rf(m, x, 0.0, n_jobs=4, chunk=33)
    np.testing.assert_array_equal(a, b)
    assert fp == hashlib.sha256(b"".join(e.tree_.value.tobytes() for e in m.estimators_)).hexdigest()


def test_rf_rejects_nonfinite_features(small_rf):
    _, m = small_rf
    with pytest.raises(ValueError):
        fc.predict_rf(m, fc.har_features(np.ones((1, 30))), 0.0)  # rows t < 22 are NaN


def test_garch_fit_recovers_parameters_and_respects_constraints():
    r = sim.simulate(P, 1, 3500, rng(12), burn=500)[0][0]
    gp, info = fc.fit_garch(r)
    assert sim.constraint_violations(gp, need_m4=False) == []
    assert info["convergence_flag"] == 0
    assert abs(gp.alpha - P.alpha) < 0.05 and abs(gp.beta - P.beta) < 0.06


def test_slope_is_ols_slope_with_one_normalisation():
    h = rng(18).gamma(2.0, size=(2, 4))  # n = 8: a ddof mismatch would be off by 8/7
    assert fc.slope(0.3 * h + 2.0, h) == pytest.approx(0.3, rel=1e-12)
    assert fc.slope(h, h) == pytest.approx(1.0, rel=1e-12)
    f = rng(19).normal(size=(2, 4))
    assert fc.slope(f, h) == pytest.approx(np.polyfit(h.ravel(), f.ravel(), 1)[0], rel=1e-10)


def test_qlike_minimised_at_true_variance():
    h = 2.0
    grid = np.linspace(0.5, 5, 451)
    expected = np.log(grid) + h / grid  # E[QLIKE(r^2, f)] = log f + h/f
    assert grid[np.argmin(expected)] == pytest.approx(h)


# --- EWMA, run lengths, calibration (eqs. 13-17) ------------------------------------------

def test_ewma_matches_closed_form():
    u = rng(13).exponential(size=(3, 50))
    lam, z0 = 0.15, 1.0
    z = chart.ewma(u, lam, z0)
    t = np.arange(1, 51)
    w = lam * (1 - lam) ** (t[:, None] - t[None, :]) * (t[None, :] <= t[:, None])
    closed = (1 - lam) ** t * z0 + u @ w.T
    np.testing.assert_allclose(z, closed, rtol=1e-12)


def test_first_alarm_and_censoring():
    z = np.array([[0.5, 2.0, 0.1], [0.1, 0.2, 0.3], [3.0, 0.0, 0.0]])
    t, cens = chart.first_alarm(z, 1.0)
    assert t.tolist() == [2, 3, 1] and cens.tolist() == [False, True, False]


def test_delay_conventions_prechange_and_restriction():
    tau, H = 3, 3  # 5 monitored days; change affects day 3 onwards
    z = np.zeros((4, 5))
    z[0, 1] = 9  # alarm on day 2 < tau: pre-change false alarm
    z[1, 2] = 9  # alarm on day 3 = tau: delay 1
    z[2, 4] = 9  # alarm on day 5: delay 3
    d, cens = chart.delays(z, 1.0, tau, H)  # path 4: never -> censored, restricted to H
    assert np.isnan(d[0]) and d[1:].tolist() == [1, 3, 3] and cens.tolist() == [False, False, False, True]
    s = chart.delay_summary(d, cens)
    assert s["p_prechange_fa"] == 0.25 and s["censored"] == pytest.approx(1 / 3)


def test_calibration_is_smallest_threshold_reaching_target():
    z = chart.ewma(rng(14).chisquare(1, (400, 600)), 0.1)
    h, arl = chart.calibrate(z, 50)
    restricted = lambda hh: np.minimum(chart.first_alarm(z, hh)[0], 600).mean()  # noqa: E731
    assert arl >= 50 and restricted(h) == pytest.approx(arl)
    assert restricted(h * (1 - 1e-5)) < 50


def test_calibration_agrees_with_markov_chain_arl():
    """iid chi2(1) input: simulated calibration vs independent Brook-Evans ARL."""
    lam, target = 0.1, 50
    z = chart.ewma(rng(15).chisquare(1, (20_000, 800)), lam)
    h, _ = chart.calibrate(z, target)
    arl_mc = chart.brook_evans_arl(stats.chi2(1).cdf, lam, h, m=800)
    assert arl_mc == pytest.approx(target, rel=0.03)
    v = chart.validate(chart.ewma(rng(16).chisquare(1, (20_000, 800)), lam), h, target, tau=10)
    assert v["passed"] and v["censored"] < 0.01


def test_masking_formulas():
    r_g, m_g = chart.garch_masking_theory(P, P.var, 2.0)
    assert r_g == pytest.approx(2 * 0.09 / 0.16) and m_g == pytest.approx(r_g - 1)
    assert chart.masking_ratio(1.5, 1.0, 2.0) == pytest.approx(0.5)


# --- seeds and reproducibility -----------------------------------------------------------

def test_role_streams_are_distinct_and_reproducible():
    cfg = run.CONFIGS["smoke"]
    a, b = run.streams(cfg, 0), run.streams(cfg, 0)
    draws = {k: g.standard_normal(5) for k, g in a.items()}
    for k, g in b.items():
        np.testing.assert_array_equal(draws[k], g.standard_normal(5))
    vals = [tuple(v) for v in draws.values()]
    assert len(set(vals)) == len(vals)
    assert not np.array_equal(run.streams(cfg, 1)["train"].standard_normal(5), draws["train"])


TINY = {**run.CONFIGS["smoke"], "n_train": 1000, "n_dev": 400, "n_cal": 20, "n_val": 20, "n_ooc": 20,
        "t_max": 200, "target_arl": 20, "tau": 10, "H": 40, "rf_trees": 5, "rf_leaf": [50],
        "sustained": [20, 39], "n_boot": 50, "n_jobs": 2}


def test_pipeline_is_reproducible():
    a = run.replicate(TINY, 0, run.Timer())
    b = run.replicate(TINY, 0, run.Timer())
    dump = lambda x: json.dumps(x, sort_keys=True, default=float)  # noqa: E731
    assert dump(a) == dump(b)
    assert a["frozen_checks"] == {"rf_unchanged": True, "garch_unchanged": True}


# --- artifact overwrite protection ------------------------------------------------------

@pytest.mark.parametrize("mode, existing", [("smoke", "results.json"), ("pilot", "config.json"), ("verify", "verify.txt")])
def test_existing_artifacts_are_never_overwritten(tmp_path, monkeypatch, mode, existing):
    (tmp_path / existing).write_text("evidence")
    monkeypatch.setattr(sys, "argv", ["run.py", mode, "--out", str(tmp_path)])
    with pytest.raises(SystemExit) as e:
        run.main()
    assert "refusing to overwrite" in str(e.value.code)
    with pytest.raises(FileExistsError):
        run.run(mode, TINY, tmp_path)
    assert (tmp_path / existing).read_text() == "evidence"
    assert [q.name for q in tmp_path.iterdir()] == [existing]


def test_fresh_wrapper_directory_is_accepted_and_wrapper_files_kept(tmp_path):
    wrapper = ("provenance.txt", "git_status.txt", "git_diff_stat.txt", "pip_freeze.txt", "time.txt",
               "stdout.log", "stderr.log")
    for n in wrapper:
        (tmp_path / n).write_text(f"{n} from wrapper")
    res = run.run("smoke", TINY, tmp_path)
    assert all((tmp_path / n).read_text() == f"{n} from wrapper" for n in wrapper)
    assert json.loads((tmp_path / "results.json").read_text())["results_sha256"] == res["results_sha256"]
    assert {"config.json", "tables.md", "fig_delay.png", "fig_profile.png"} <= {q.name for q in tmp_path.iterdir()}
    with pytest.raises(FileExistsError):  # a second run into the same directory is refused
        run.run("smoke", TINY, tmp_path)


# --- SPY helpers (no network) --------------------------------------------------------------

def test_spy_returns_split_and_snapshot_hash(tmp_path):
    idx = pd.bdate_range("2005-12-01", periods=60)
    close = pd.Series(100 * np.exp(np.cumsum(rng(17).normal(0, 0.01, 60))), index=idx, name="close")
    r = spy.log_returns(close)
    assert r.iloc[0] == pytest.approx(100 * np.log(close.iloc[1] / close.iloc[0]))
    tr, mo, mu = spy.split(r, "2005-12-29", "2006-01-02")
    assert tr.index.max() < mo.index.min() and tr.mean() == pytest.approx(0) and mu == pytest.approx(r[:tr.index.max()].mean())
    with pytest.raises(ValueError):
        spy.split(r, "2006-01-10", "2006-01-02")
    path = tmp_path / "SPY.csv"
    close.to_csv(path, index_label="date")
    (tmp_path / "SPY.meta.json").write_text(json.dumps({"sha256": hashlib.sha256(path.read_bytes()).hexdigest()}))
    pd.testing.assert_series_equal(spy.load_snapshot(path), close, check_freq=False, check_names=False)
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError):
        spy.load_snapshot(path)


# === Phase 2 (C1-C6): estimators, aggregation, pairing, guards ============================

# --- alarm-day coding and restricted delays (eq. 17) ----------------------------------------

def test_alarm_day_coding_separates_last_day_alarm_from_censoring():
    tau, H = 50, 500
    M = tau - 1 + H  # 549 monitored days
    z = np.zeros((4, M))
    z[0, M - 1] = 9    # alarm on day 549: last observable detection, D = H
    z[1, tau - 2] = 9  # day 49 < tau: pre-change false alarm
    z[2, tau - 1] = 9  # day 50 = tau: D = 1
    T = chart.alarm_days(z, 1.0)          # path 4: no alarm -> censored sentinel 550
    assert T.tolist() == [549, 49, 50, 550]
    d, cens = chart.delays_from_days(T, tau, H)
    np.testing.assert_array_equal(d, [H, np.nan, 1, H])
    assert cens.tolist() == [False, False, False, True]
    np.testing.assert_array_equal(chart.detected(d, cens, H), [1.0, np.nan, 1.0, 0.0])
    assert chart.detected(d, cens, H - 1)[0] == 0.0 and chart.detected(d, cens, 10 * H)[3] == 0.0
    d2, c2 = chart.delays(z, 1.0, tau, H)
    np.testing.assert_array_equal(d2, d)
    np.testing.assert_array_equal(c2, cens)
    with pytest.raises(ValueError):
        chart.delays_from_days(np.array([M + 2]), tau, H)


def test_boundary_alarm_days_survive_npz_round_trip_and_evaluation(tmp_path):
    cfg = {**TINY, "deltas": [2.0], "lams": [0.1], "ks": [5, 20, 60]}
    tau, H = cfg["tau"], cfg["H"]
    M = tau - 1 + H  # TINY: 49 monitored days, censored = 50; k = 60 > H on purpose
    n = 6
    T = np.empty((2, 1, len(run.CHARTS), n), np.int32)
    T[0] = [M, M + 1, tau, tau - 1, M, M + 1]       # no change (delta = 1)
    T[1] = [M, M + 1, tau, tau - 1, tau + 3, M]     # with change, same paths
    pp = {"T": T, "occ": np.zeros_like(T), "uS": np.ones((2, len(run.CHARTS), n)), "uE": np.ones((2, len(run.CHARTS), n))}
    run.save_paths(tmp_path / "paths.npz", {f"r0_{k}": v for k, v in pp.items()})
    back = run.load_paths(tmp_path / "paths.npz", 0)
    assert back.keys() == pp.keys() and all(np.array_equal(back[k], pp[k]) and back[k].dtype == pp[k].dtype for k in pp)
    assert run.perpath_hash(back) == run.perpath_hash(pp)
    o = run.evaluate(back, cfg, rng(0))["ooc"]["2.0"]["0.1"]["rf"]
    # E: 5 of 6 paths. delta = 2: D = [H (day M), censored, 1, -, 4, H (day M)]; delta = 1: [H, cens, 1, -, H, cens]
    assert o["n_eval"] == 5 and o["p_prechange_fa"] == pytest.approx(1 / 6)
    assert o["censored"] == pytest.approx(1 / 5) and o["rmd"] == pytest.approx((H + H + 1 + 4 + H) / 5)
    assert o["p_d_le_60"] == pytest.approx(4 / 5)  # censored path never a detection although D_H = H <= 60
    assert o["x_60"] == pytest.approx(1 / 5) and o["x_5"] == pytest.approx(1 / 5)
    assert o["median_d"] == H and o["q75_d"] == H and o["q25_d"] == 4


# --- per-chart estimators (eqs. 23-26) -------------------------------------------------------

def test_excess_detection_hand_count_and_zero_without_change():
    tau, H = 3, 10  # M = 12, censored = 13
    d, c = chart.delays_from_days(np.array([2, 3, 6, 13, 4, 12]), tau, H)    # with change
    b = chart.delays_from_days(np.array([2, 5, 13, 13, 4, 13]), tau, H)      # same paths, no change
    s = chart.delay_summary(d, c, base=b, ks=(4, 10))
    assert s["n_eval"] == 5 and s["p_prechange_fa"] == pytest.approx(1 / 6) and s["censored"] == pytest.approx(1 / 5)
    assert s["rmd"] == pytest.approx((1 + 4 + 10 + 2 + 10) / 5)
    assert s["x_4"] == pytest.approx(0.2) and s["se_x_4"] == pytest.approx(np.std([0, 1, 0, 0, 0], ddof=1) / np.sqrt(5))
    assert s["x_10"] == pytest.approx(0.4)
    assert (s["q25_d"], s["median_d"], s["q75_d"]) == (2.0, 4.0, 10.0)
    z = chart.delay_summary(d, c, base=(d, c), ks=(4, 10))
    assert z["x_4"] == z["x_10"] == 0.0 and z["se_x_4"] == 0.0


def test_crn_pairing_violation_is_detected():
    tau, H = 3, 10
    d, c = chart.delays_from_days(np.array([2, 3, 6]), tau, H)
    b = chart.delays_from_days(np.array([3, 3, 6]), tau, H)  # path 0 not a pre-change alarm without the change
    with pytest.raises(ValueError, match="CRN"):
        chart.delay_summary(d, c, base=b)


def test_conditional_quantiles_suppressed_when_not_identifiable():
    H = 500
    d = np.array([1.0, 2.0, H, H, H])
    cens = np.array([False, False, True, True, True])  # 60% censored
    assert chart.cond_quantile(d, cens, 0.25) == 2.0
    assert chart.cond_quantile(d, cens, 0.5) is None and chart.cond_quantile(d, cens, 0.75) is None
    d, cens = np.array([1.0, H, H, H]), np.array([False, True, True, True])
    assert chart.cond_quantile(d, cens, 0.25) == 1.0 and chart.cond_quantile(d, cens, 0.5) is None  # never H
    assert chart.cond_quantile(np.array([np.nan, 3.0]), np.array([False, False]), 0.5) == 3.0  # pre-change excluded


def test_paired_diff_normal_se_with_bootstrap_check():
    g = rng(30)
    a = g.normal(10, 3, 4000)
    b = a + g.normal(-1, 1, 4000)
    a[:7] = np.nan
    b[5:12] = np.nan
    s = chart.paired_diff(a, b, rng(31), n_boot=2000)
    ok = ~np.isnan(a) & ~np.isnan(b)
    diff = a[ok] - b[ok]
    assert s["n"] == ok.sum() == 4000 - 12
    assert s["mean"] == pytest.approx(diff.mean()) and s["se_mean"] == pytest.approx(diff.std(ddof=1) / np.sqrt(len(diff)))
    assert s["ci95"] == pytest.approx([s["mean"] - 1.96 * s["se_mean"], s["mean"] + 1.96 * s["se_mean"]])
    assert s["boot_ci95"] == pytest.approx(s["ci95"], abs=0.2 * s["se_mean"])
    assert "boot_ci95" not in chart.paired_diff(a, b)


def test_masking_delta_method_se_matches_replication_sd():
    g = rng(32)
    K, N = 2000, 400
    B = g.gamma(2.0, 0.5, (K, N))
    A = 1.4 * B * g.lognormal(0.0, 0.3, (K, N))  # paired, positively correlated
    est = [chart.ratio_se(A[i], B[i]) for i in range(K)]
    r = np.array([e[0] for e in est])
    assert r == pytest.approx(A.mean(axis=1) / B.mean(axis=1))
    assert np.mean([e[1] for e in est]) == pytest.approx(r.std(ddof=1), rel=0.1)


# --- replicate aggregation (eqs. 27-28) -----------------------------------------------------

def test_across_replicates_formulas():
    v, w = [1.0, 3.0, 2.0, 6.0], [0.5, 1.5, 1.0, 1.0]
    a = aggregate.across(v, w)
    sb = np.std(v, ddof=1)
    half = stats.t.ppf(0.975, 3) * sb / 2
    assert a["mean"] == 3.0 and a["sd_between"] == pytest.approx(sb) and a["ci95"] == pytest.approx([3 - half, 3 + half])
    assert a["values"] == v and (a["min"], a["max"]) == (1.0, 6.0)
    assert stats.t.ppf(0.975, 9) == pytest.approx(2.262, abs=1e-3) and stats.t.ppf(0.975, 4) == pytest.approx(2.776, abs=1e-3)
    assert stats.t.ppf(0.975, 19) == pytest.approx(2.093, abs=1e-3)  # production R = 20
    mw2 = np.mean(np.square(w))  # 1.125, whereas mean(w)^2 = 1.0 (Jensen)
    assert a["rms_mc_se"] == pytest.approx(np.sqrt(mw2)) and a["var_between_resid"] == pytest.approx(sb**2 - mw2)
    assert a["var_between_resid"] != pytest.approx(sb**2 - np.mean(w) ** 2)
    assert a["n_pos"] == 4 and a["n_neg"] == 0 and a["sign_p"] == pytest.approx(0.125)
    t = aggregate.across([1.0, 1.1], [5.0, 5.0])  # Monte Carlo noise exceeds the spread: truncated at 0
    assert t["var_between_resid"] == 0.0 and t["sd_between_resid"] == 0.0
    one = aggregate.across([2.5], [0.3])
    assert "ci95" not in one and "sd_between" not in one and one["mean"] == 2.5 and one["rms_mc_se"] == pytest.approx(0.3)


def test_collect_uses_equal_weights_and_keeps_counts_flags_separate():
    def rep(rmd, se, n, med, ok):
        return {"ooc": {"1.0": {"0.1": {"rf": {"rmd": rmd, "se_rmd": se, "n_eval": n, "median_d": med}}}},
                "validation": {"0.1": {"rf": {"passed": ok}}}}
    reps = [rep(10.0, 1.0, 10, None, True), rep(20.0, 2.0, 1000, 7.0, False)]
    sch = {"estimands": [(("ooc", "1.0", "0.1", "rf", "rmd"), "se_rmd"), (("ooc", "1.0", "0.1", "rf", "median_d"), None)],
           "flags": [("validation", "0.1", "rf", "passed")], "counts": [("ooc", "1.0", "0.1", "rf", "n_eval")]}
    out = aggregate.collect(reps, sch)
    e = out["estimands"]["ooc/1.0/0.1/rf/rmd"]
    assert e["mean"] == 15.0  # equal weights, not the path-weighted 19.9: paths are never pooled
    assert e["rms_mc_se"] == pytest.approx(np.sqrt(2.5))
    assert out["estimands"]["ooc/1.0/0.1/rf/median_d"]["values"] == [None, 7.0]
    assert "mean" not in out["estimands"]["ooc/1.0/0.1/rf/median_d"]
    assert out["counts"]["ooc/1.0/0.1/rf/n_eval"] == {"values": [10, 1000], "min": 10, "max": 1000}
    assert out["flags"]["validation/0.1/rf/passed"] == {"n_true": 1, "R": 2}


def test_schema_is_an_explicit_allowlist_with_the_primary_endpoints():
    cfg = run.CONFIGS["production"]
    sch = aggregate.schema(cfg, run.CHARTS, run.PAIRS)
    paths = {p for p, _ in sch["estimands"]}
    assert not any(p[0] in ("rf_seed", "rf_grid", "profile", "perpath_sha256", "dgp_var", "floor_rows") for p in paths)
    assert not any(p[-1] in ("n_eval", "n", "passed", "convergence_flag") for p in paths)
    assert not any(p[0] == "ooc" and p[1] == "1.0" and p[-1].startswith(("x_", "occupancy_excess")) for p in paths)
    pr = cfg["primary"]
    primary = {("paired", str(d), str(pr["lam"]), pair, m, "mean") for pair in pr["pairs"] for m in pr["metrics"]
               for d in cfg["deltas"]}
    assert len(primary) == 12 and primary <= paths
    assert ("validation", "0.1", "rf", "passed") in sch["flags"] and ("floor_binds",) in sch["counts"]


# --- matched paths, reproducibility and recomputation (2 replicates) -------------------------

@pytest.fixture(scope="module")
def tiny2(tmp_path_factory):
    cfg = {**TINY, "replicates": 2}
    out = tmp_path_factory.mktemp("tiny2")
    return cfg, out, run.run("smoke", cfg, out)


def test_counterfactual_pairing_and_conventional_monotonicity(tiny2):
    cfg, out, res = tiny2
    tau, H = cfg["tau"], cfg["H"]
    conv = run.CHARTS.index("conventional")
    for r in range(cfg["replicates"]):
        T = run.load_paths(out / "paths.npz", r)["T"]
        assert ((T < tau) == (T[:1] < tau)).all()  # CRN: identical pre-change data, identical pre-change alarms
        # Conventional chart only: u(delta) = delta u(1) after the change (fixed denominator), so T(delta) <= T(1).
        assert (T[1:, :, conv] <= T[0, :, conv]).all()
        for i in range(1, T.shape[0]):
            for j in range(T.shape[1]):
                d, c = chart.delays_from_days(T[i, j, conv], tau, H)
                b = chart.delays_from_days(T[0, j, conv], tau, H)
                x = chart.detected(d, c, 20) - chart.detected(*b, 20)
                assert set(np.unique(x[~np.isnan(x)])) <= {0.0, 1.0}
        for m in res["replicates"][r]["masking"].values():  # M = 1 by construction for the conventional chart
            assert m["conventional"]["M"] == pytest.approx(1.0, abs=1e-12) and m["conventional"]["se_M"] < 1e-12


def test_results_are_recomputable_from_paths_npz(tiny2):
    cfg, out, _ = tiny2
    saved = json.loads((out / "results.json").read_text())
    for r in range(cfg["replicates"]):
        pp, rep = run.load_paths(out / "paths.npz", r), saved["replicates"][r]
        assert run.perpath_hash(pp) == rep["perpath_sha256"]
        ev = run.evaluate(pp, cfg, run.streams(cfg, r)["boot"])
        assert json.dumps(ev["ooc"], sort_keys=True) == json.dumps(rep["ooc"], sort_keys=True)
        assert json.dumps(ev["paired"], sort_keys=True) == json.dumps(rep["paired"], sort_keys=True)
        for key, mk in ev["masking"].items():
            for k, v in mk.items():
                assert v.items() <= rep["masking"][key][k].items()
    again = aggregate.collect(saved["replicates"], aggregate.schema(cfg, run.CHARTS, run.PAIRS))
    assert json.dumps(again, sort_keys=True) == json.dumps(saved["aggregate"], sort_keys=True)


def test_two_replicate_run_is_reproducible_and_replicates_independent(tiny2, tmp_path):
    cfg, out, res = tiny2
    assert run.run("smoke", cfg, tmp_path)["results_sha256"] == res["results_sha256"]
    with np.load(out / "paths.npz") as a, np.load(tmp_path / "paths.npz") as b:
        assert sorted(a.files) == sorted(b.files) and all(np.array_equal(a[k], b[k]) for k in a.files)
    r0, r1 = res["replicates"]
    assert r0["s2_train"] != r1["s2_train"] and r0["rf_seed"] != r1["rf_seed"]
    assert r0["perpath_sha256"] != r1["perpath_sha256"]
    assert res["aggregate"]["estimands"]["s2_train"]["values"] == [r0["s2_train"], r1["s2_train"]]


# --- configurations and authorization guards (C1) -------------------------------------------

def test_production_sensitivity_and_benchmark_configurations():
    P, S, B = (run.CONFIGS[m] for m in ("production", "sensitivity_arl100", "benchmark"))
    assert {k: P[k] for k in ("n_train", "n_dev", "n_cal", "n_val", "n_ooc", "t_max", "tau", "H", "rf_trees",
                              "replicates", "target_arl", "master_seed")} == {
        "n_train": 3500, "n_dev": 3500, "n_cal": 2000, "n_val": 2000, "n_ooc": 2000, "t_max": 5000, "tau": 50,
        "H": 500, "rf_trees": 500, "replicates": 20, "target_arl": 500, "master_seed": 20261014}
    assert P["deltas"] == [1.5, 2.0, 3.0] and P["lams"] == [0.1, 0.2] and P["dgp"] == run.DGP
    assert P["primary"]["lam"] == 0.1 and P["primary"]["pairs"] == ["rf - garch", "rf - conventional"]
    assert P["primary"]["metrics"] == ["dH", "x_20"] and "before production" in P["primary"]["label"]
    assert {k for k in P if P[k] != S[k]} == {"target_arl", "label"} and S["target_arl"] == 100  # same seed and paths
    assert S["replicates"] == 20 and S["master_seed"] == 20261014  # sensitivity inherits R = 20: matched to production
    assert P["ic_validation"] == S["ic_validation"] == B["ic_validation"] and P["ic_validation"]["tol"] == 0.15
    assert "post-pilot, post-benchmark methodological amendment made before production" in P["ic_validation"]["label"]
    assert chart.ic_equivalence((0, 0), S["target_arl"], S["ic_validation"]["tol"])[0] == [85.0, 115.0]
    assert {k for k in P if P[k] != B[k]} == {"replicates", "master_seed", "label"}
    assert B["replicates"] == 1 and B["master_seed"] == 20261013
    assert "not a reproduction of the original pilot" in B["label"] and "excluded from the primary" in B["label"]
    assert run.CONFIGS["pilot"]["master_seed"] == run.CONFIGS["smoke"]["master_seed"] == 20261013
    assert set(run.GUARDED) == {"production", "sensitivity_arl100", "benchmark", "spy"}  # spy added 27 Oct 2026


@pytest.mark.parametrize("mode", ["production", "sensitivity_arl100", "benchmark"])
def test_guarded_modes_refuse_without_approved(tmp_path, monkeypatch, mode):
    called = []
    monkeypatch.setattr(run, "run", lambda *a: called.append(a))
    out = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", ["run.py", mode, "--out", str(out)])
    with pytest.raises(SystemExit) as e:
        run.main()
    assert "--approved" in str(e.value.code) and not called and not out.exists()


@pytest.mark.parametrize("mode", ["production", "sensitivity_arl100", "benchmark"])
def test_guarded_modes_with_approved_reach_run_with_their_config(tmp_path, monkeypatch, mode):
    called = []
    monkeypatch.setattr(run, "run", lambda *a: called.append(a))  # nothing is simulated
    monkeypatch.setattr(sys, "argv", ["run.py", mode, "--approved", "--out", str(tmp_path)])
    run.main()
    assert called == [(mode, run.CONFIGS[mode], tmp_path)]


def test_approved_guarded_mode_still_refuses_to_overwrite(tmp_path, monkeypatch):
    (tmp_path / "paths.npz").write_text("evidence")
    monkeypatch.setattr(run, "run", lambda *a: pytest.fail("must not run"))
    monkeypatch.setattr(sys, "argv", ["run.py", "production", "--approved", "--out", str(tmp_path)])
    with pytest.raises(SystemExit) as e:
        run.main()
    assert "refusing to overwrite" in str(e.value.code)
    assert (tmp_path / "paths.npz").read_text() == "evidence" and [q.name for q in tmp_path.iterdir()] == ["paths.npz"]


@pytest.mark.parametrize("mode", ["production", "sensitivity_arl100", "benchmark"])
def test_wrapper_refuses_guarded_modes_without_approved(mode):
    root = Path(run.__file__).resolve().parent
    runs = root / "results" / "runs"
    before = set(runs.iterdir()) if runs.exists() else set()
    p = subprocess.run(["bash", str(root / "scripts" / "run_simulation.sh"), mode], capture_output=True, text=True,
                       timeout=60)
    assert p.returncode == 2 and "--approved" in p.stderr
    assert (set(runs.iterdir()) if runs.exists() else set()) == before


# === Phase 2 audit remediation (M1, M2, D6) ================================================

def _pp(T):
    """Per-path arrays around given alarm days (zero occupancy, unit window means)."""
    nd, _, nc, n = T.shape
    return {"T": T, "occ": np.zeros_like(T), "uS": np.ones((nd, nc, n)), "uE": np.ones((nd, nc, n))}


def test_empty_survivor_set_keeps_full_schema_with_missing_values():
    tau, H = 3, 10
    full = chart.delay_summary(*chart.delays_from_days(np.array([5, 6, 13]), tau, H),
                               base=chart.delays_from_days(np.array([5, 6, 13]), tau, H))
    d, c = chart.delays_from_days(np.array([1, 2, 2]), tau, H)  # every path alarms before tau
    s = chart.delay_summary(d, c, base=(d, c))
    assert s.keys() == full.keys()
    assert s["n_eval"] == 0 and s["p_prechange_fa"] == 1.0 and s["se_p_prechange_fa"] == 0.0  # uses all paths
    missing = [k for k in s if k not in ("n_eval", "p_prechange_fa", "se_p_prechange_fa")]
    assert missing and all(s[k] is None for k in missing)  # never 0 for an unidentified estimate or SE
    e = chart.paired_diff(d, d)
    assert e == {"mean": None, "se_mean": None, "n": 0, "ci95": [None, None]}


def test_mismatched_counterfactual_survivors_raise_even_when_empty():
    tau, H = 3, 10
    empty = chart.delays_from_days(np.array([1, 2, 2]), tau, H)
    some = chart.delays_from_days(np.array([1, 5, 2]), tau, H)
    with pytest.raises(ValueError, match="CRN"):
        chart.delay_summary(*empty, base=some)
    with pytest.raises(ValueError, match="CRN"):
        chart.delay_summary(*some, base=empty)


def test_partially_identified_quantities():
    tau, H = 3, 10
    d, c = chart.delays_from_days(np.array([1, 2, 7]), tau, H)  # one evaluable path, D = 5
    s = chart.delay_summary(d, c, base=(d, c), ks=(5,))
    assert s["n_eval"] == 1 and s["rmd"] == 5.0 and s["se_rmd"] is None
    assert s["p_d_le_5"] == 1.0 and s["se_p_d_le_5"] is None and s["median_d"] == 5.0
    d2, c2 = chart.delays_from_days(np.array([1, 2, 13]), tau, H)  # one evaluable path, censored
    s2 = chart.delay_summary(d2, c2)
    assert s2["censored"] == 1.0 and s2["median_d"] is None and s2["q25_d"] is None  # never H for a censored path
    one = chart.paired_diff(np.array([4.0, np.nan]), np.array([1.0, 2.0]), rng(0), n_boot=50)
    assert one == {"mean": 3.0, "se_mean": None, "n": 1, "ci95": [None, None]}  # no SE, CI or bootstrap from n = 1
    agg = aggregate.across([1.0, 3.0], None)
    assert "rms_mc_se" not in agg and "var_between_resid" not in agg and agg["mean"] == 2.0


def test_aggregation_handles_unidentified_replicate_endpoints():
    cfg = {**TINY, "deltas": [2.0], "lams": [0.1]}
    tau, H = cfg["tau"], cfg["H"]
    M, rf = tau - 1 + H, run.CHARTS.index("rf")
    T0 = np.full((2, 1, len(run.CHARTS), 6), M, np.int32)
    T0[:, :, rf] = 1                                     # replicate 0: every RF path alarms before tau
    T1 = T0.copy()
    T1[:, :, rf] = [1, 1, 1, 1, 1, tau + 2]              # replicate 1: a single RF survivor
    reps = [run.evaluate(_pp(T), cfg, rng(0)) for T in (T0, T1)]
    sch = aggregate.schema(cfg, run.CHARTS, run.PAIRS)
    sub = {"estimands": [e for e in sch["estimands"] if e[0][0] in ("ooc", "paired", "masking") and e[0][-1] != "M_theory"],
           "flags": [],
           "counts": [c for c in sch["counts"] if c[0] in ("ooc", "paired")]}
    out = aggregate.collect(reps, sub)  # previously KeyError
    e = out["estimands"]["ooc/2.0/0.1/rf/rmd"]
    assert e["values"] == [None, 3.0] and "mean" not in e and "not identifiable" in e["note"]
    assert out["counts"]["ooc/2.0/0.1/rf/n_eval"]["values"] == [0, 1]
    g = out["estimands"]["ooc/2.0/0.1/garch/rmd"]
    assert g["mean"] == H and "rms_mc_se" in g  # other charts unaffected
    assert "mean" not in out["estimands"]["paired/2.0/0.1/rf - garch/dH/mean"]


def test_reporting_with_unidentified_endpoints(tiny2, tmp_path):
    cfg, _, res = tiny2
    tau, H = cfg["tau"], cfg["H"]
    M, rf = tau - 1 + H, run.CHARTS.index("rf")
    T = np.full((1 + len(cfg["deltas"]), len(cfg["lams"]), len(run.CHARTS), cfg["n_ooc"]), M, np.int32)
    T[:, :, rf] = 1  # replicate 0: no RF survivor, so every RF endpoint and RF contrast is unidentified
    bad = copy.deepcopy(res)
    ev = run.evaluate(_pp(T), cfg, rng(0))
    bad["replicates"][0].update({k: ev[k] for k in ("ooc", "paired")})
    bad["aggregate"] = aggregate.collect(bad["replicates"], aggregate.schema(cfg, run.CHARTS, run.PAIRS))
    report.write(bad, tmp_path)  # previously KeyError 'mean'
    md = (tmp_path / "tables.md").read_text()
    assert "n/i" in md and all((tmp_path / f).exists() for f in ("fig_delay.png", "fig_profile.png", "fig_replicates.png"))
    # R = 1 with a single RF survivor: estimate identified, SE not
    T[:, :, rf, -1] = tau + 1
    one = copy.deepcopy(res)
    ev = run.evaluate(_pp(T), cfg, rng(0))
    one["replicates"] = [one["replicates"][0] | {k: ev[k] for k in ("ooc", "paired")}]
    one["aggregate"] = aggregate.collect(one["replicates"], aggregate.schema(cfg, run.CHARTS, run.PAIRS))
    assert one["replicates"][0]["ooc"]["2.0"]["0.1"]["rf"]["se_rmd"] is None
    (tmp_path / "r1").mkdir()
    report.write(one, tmp_path / "r1")
    assert "n/i" in (tmp_path / "r1" / "tables.md").read_text()


def test_figure_series_omits_unidentified_points_and_never_zero_fills():
    entries = [{"mean": 2.0, "ci95": [1.0, 3.0]}, {"values": [None, 4.0], "note": "not identifiable in every replicate"},
               None, {"mean": 5.0}, {"mean": 6.0}]
    pts = report.series([1.0, 1.5, 2.0, 3.0, 4.0], entries, [0.1, 0.1, 0.1, None, 0.5])
    assert [p[0] for p in pts] == [1.0, 3.0, 4.0]  # valid points at other shifts are kept
    assert pts[0][2] == 1.0 and np.isnan(pts[1][2]) and pts[2][2] == pytest.approx(1.96 * 0.5)


@pytest.mark.parametrize("R", [1, 2, 10, 20, 50])
def test_replicate_jitter_stays_inside_axis_and_own_shift(R):
    """P3 regression: the old fixed 0.03 jitter put replicates 0 and 19 outside the axis
    at delta = 1 and 3 when R = 20, and mixed the delta = 1.5 and 2 clouds."""
    xs = [1.0, 1.5, 2.0, 3.0]
    offs, gap = report.jitter(xs, R)
    assert len(offs) == R and gap == 0.5 and len(set(offs)) == R
    assert (np.abs(offs) <= 0.3 * gap + 1e-12).all() and (R > 1 or offs[0] == 0.0)
    pos = np.add.outer(xs, offs)                                   # [x, replicate]
    assert (pos > xs[0] - gap / 2).all() and (pos < xs[-1] + gap / 2).all()
    assert (pos[:-1].max(axis=1) < pos[1:].min(axis=1)).all()      # clouds of neighbouring shifts disjoint


def test_paired_excess_contrast_hand_counted_over_two_shifts_and_two_lambdas():
    """rf - garch X(k) and RMD contrasts from alarm days counted by hand (tau = 10, H = 40:
    D = T - 9, T = 49 is a detection with D = 40, T = 50 is censored, T < 10 is a pre-change alarm)."""
    cfg = {**TINY, "deltas": [1.5, 2.0], "lams": [0.1, 0.2], "ks": [5, 20, 60], "n_boot": 0}
    assert (cfg["tau"], cfg["H"]) == (10, 40)
    gi, ri = run.CHARTS.index("garch"), run.CHARTS.index("rf")
    T = np.full((3, 2, len(run.CHARTS), 5), 49, np.int32)
    # lambda = 0.1: RF path 0 and GARCH path 1 alarm before tau at every delta; paired set = paths 2, 3, 4
    T[:, 0, ri] = [[5, 15, 50, 40, 20], [5, 12, 25, 20, 20], [5, 10, 15, 50, 12]]
    T[:, 0, gi] = [[12, 9, 50, 50, 25], [11, 9, 30, 50, 14], [10, 9, 35, 49, 11]]
    # lambda = 0.2: GARCH path 4 alarms before tau; paired set = paths 0-3
    T[:, 1, ri] = [[30, 50, 18, 50, 50], [25, 30, 14, 49, 50], [12, 20, 12, 30, 40]]
    T[:, 1, gi] = [[50, 20, 50, 15, 3], [50, 19, 22, 15, 3], [40, 15, 18, 12, 3]]
    ev = run.evaluate(_pp(T), cfg, None)
    c = lambda d, lam, m: ev["paired"][d][lam]["rf - garch"][m]  # noqa: E731
    # lambda 0.1, delta 1.5: x_rf(20) = [1, 1, 0], x_garch(20) = [0, 0, 0]; x(5): [0, 0, 0] vs [0, 0, 1]
    assert c("1.5", "0.1", "x_20")["n"] == 3
    assert c("1.5", "0.1", "x_20")["mean"] == pytest.approx(2 / 3) and c("1.5", "0.1", "x_20")["se_mean"] == pytest.approx(1 / 3)
    assert c("1.5", "0.1", "x_5")["mean"] == pytest.approx(-1 / 3)
    # lambda 0.1, delta 2: x(20) [1, 0, 0] vs [0, 0, 0]; x(60) [1, -1, 0] vs [1, 1, 0] (GARCH T = 49: D = 40 <= 60)
    assert c("2.0", "0.1", "x_20")["mean"] == pytest.approx(1 / 3) and c("2.0", "0.1", "x_20")["se_mean"] == pytest.approx(1 / 3)
    assert c("2.0", "0.1", "x_60")["mean"] == pytest.approx(-2 / 3)
    # lambda 0.2, delta 1.5: x(20) [1, 0, 0, 0] vs [0, 0, 1, 0] -> diff [1, 0, -1, 0]
    assert c("1.5", "0.2", "x_20")["n"] == 4 and c("1.5", "0.2", "x_20")["mean"] == pytest.approx(0.0)
    assert c("1.5", "0.2", "x_20")["se_mean"] == pytest.approx(np.sqrt(2 / 3) / 2)
    # lambda 0.2, delta 2: x(20) [1, 1, 0, 0] vs [0, 0, 1, 0] -> diff [1, 1, -1, 0]; D_H [3, 11, 3, 21] vs [31, 6, 9, 3]
    assert c("2.0", "0.2", "x_20")["mean"] == pytest.approx(0.25)
    assert c("2.0", "0.2", "x_20")["se_mean"] == pytest.approx(np.sqrt(2.75 / 3) / 2)
    assert c("2.0", "0.2", "dH")["mean"] == pytest.approx(-11 / 4)
    assert ev["ooc"]["2.0"]["0.2"]["rf"]["x_20"] == pytest.approx(2 / 5)  # per-chart, over all 5 RF survivors
    assert c("1.0", "0.1", "x_20")["mean"] == 0.0  # no change: zero by construction


# === Phase 2 final reporting corrections: report cells and inferential status =============

def _table(md, heading):
    """Rows (header -> cell) of the first Markdown table after the line starting with `heading`."""
    lines = md.splitlines()
    i = next(j for j, line in enumerate(lines) if line.startswith(heading))
    j = next(j for j in range(i + 1, len(lines)) if lines[j].startswith("| "))
    cells = lambda line: [c.strip() for c in line.strip().strip("|").split("|")]  # noqa: E731
    hdr, rows = cells(lines[j]), []
    for line in lines[j + 2:]:
        if not line.startswith("|"):
            break
        assert len(cells(line)) == len(hdr), line
        rows.append(dict(zip(hdr, cells(line))))
    return rows


def _row(rows, **match):
    hit = [r for r in rows if all(r[k] == v for k, v in match.items())]
    assert len(hit) == 1, (match, hit)
    return hit[0]


def _report_with(res, cfg, T_by_rep, R=None, **cfg_over):
    """tables.md text after replacing the out-of-control results of the given replicates by those of the
    synthetic alarm days T (same evaluate() and aggregation path as a real run)."""
    out = copy.deepcopy(res)
    out["config"].update(cfg_over)
    cfg = {**cfg, **cfg_over}
    if R:
        out["replicates"] = out["replicates"][:R]
    for r, T in T_by_rep.items():
        ev = run.evaluate(_pp(T), cfg, rng(0))
        out["replicates"][r].update({k: ev[k] for k in ("ooc", "paired")})
    out["aggregate"] = aggregate.collect(out["replicates"], aggregate.schema(cfg, run.CHARTS, run.PAIRS))
    return report.tables(out)


def _alarm_days(cfg, rf_days=None):
    """Every path alarms on day M (a detection, D = H) for every chart; RF alarm days optionally overridden."""
    M = cfg["tau"] - 1 + cfg["H"]
    T = np.full((1 + len(cfg["deltas"]), len(cfg["lams"]), len(run.CHARTS), cfg["n_ooc"]), M, np.int32)
    if rf_days is not None:
        T[:, :, run.CHARTS.index("rf")] = rf_days
    return T


def test_delta_one_excess_cells_read_stored_values(tiny2):
    cfg, _, res = tiny2
    no_rf = _alarm_days(cfg, rf_days=1)  # replicate 0: every RF path alarms before tau
    md = _report_with(res, cfg, {0: no_rf, 1: _alarm_days(cfg)})
    t4 = _table(md, "## Table 4.")
    rf1 = _row(t4, **{"δ": "1.000", "λ": "0.100", "chart": "RF-EWMA"})
    assert rf1["X(5) [E]"] == rf1["X(20) [E]"] == rf1["X(60) [E]"] == "n/i"  # empty survivor set: unidentified
    assert rf1["occupancy excess [all]"] == "0 (by constr.)"                   # all-path zero preserved
    conv1 = _row(t4, **{"δ": "1.000", "λ": "0.100", "chart": "Conventional EWMA"})
    assert conv1["X(20) [E]"] == "0 (by constr.)"                              # non-empty: valid zero
    t7 = _table(md, "## Table 7a.")
    empty = _row(t7, **{"contrast (a − b)": "rf - garch", "metric": "X(20)", "δ": "1.000"})
    assert empty["mean [95% CI]"] == "n/i" and empty["s_b"] == "n/i" and empty["paths (E_a ∩ E_b)"] == "0–20"
    ok = _row(_table(_report_with(res, cfg, {0: _alarm_days(cfg), 1: _alarm_days(cfg)}), "## Table 7a."),
              **{"contrast (a − b)": "rf - garch", "metric": "X(20)", "δ": "1.000"})
    assert ok["mean [95% CI]"] == "0 (by constr.)" and ok["s_b"] == "–" and ok["paths (E_a ∩ E_b)"] == "20"


def test_one_survivor_contrast_shows_estimate_with_unidentified_se(tiny2):
    cfg, _, res = tiny2
    one = _alarm_days(cfg, rf_days=1)
    one[:, :, run.CHARTS.index("rf"), -1] = cfg["tau"] + 1  # a single RF survivor, D = 2; GARCH D = H = 40
    md = _report_with(res, cfg, {0: one}, R=1)
    r8 = _row(_table(md, "## Table 8."), rep="0", contrast="rf - garch", metric="RMD_H (days)", **{"δ": "2.000"})
    assert r8["estimate"] == "-38.00" and r8["SE"] == "n/i" and r8["normal 95% CI"] == "n/i"
    assert r8["bootstrap 95% CI"] == "n/i" and r8["n (E_a ∩ E_b)"] == "1"
    r7 = _row(_table(md, "## Table 7a."), **{"contrast (a − b)": "rf - garch", "metric": "RMD_H (days)", "δ": "2.000"})
    assert r7["mean [95% CI]"] == "-38.00" and r7["MC SE"] == "n/i" and r7["s_b"] == "n/i"  # R = 1
    two = _row(_table(_report_with(res, cfg, {0: one, 1: _alarm_days(cfg)}), "## Table 7a."),
               **{"contrast (a − b)": "rf - garch", "metric": "RMD_H (days)", "δ": "2.000"})
    assert two["MC SE"] == "n/i" and two[report.RESID] == "n/i"  # one replicate has no Monte Carlo SE
    assert two["s_b"] == "26.87" and two["mean [95% CI]"].startswith("-19.00 [")  # mean of -38 and 0


def test_inapplicable_cells_are_dashes(tiny2):
    cfg, _, res = tiny2
    md = _report_with(res, cfg, {0: _alarm_days(cfg)}, n_boot=0)
    assert _row(_table(md, "## Table 2."), forecaster="Conventional EWMA")["gap closed G"] == "–"
    assert _row(_table(md, "## Table 6."), chart="RF-EWMA")["M first-order theory"] == "–"
    r8 = _row(_table(md, "## Table 8."), rep="0", contrast="rf - garch", metric="RMD_H (days)", **{"δ": "2.000"})
    assert r8["bootstrap 95% CI"] == "–" and r8["SE"] == "0.00"  # no bootstrap requested; a valid zero SE


def _headings(md):
    return [line for line in md.splitlines() if line.startswith("#")]


@pytest.mark.parametrize("mode, phrase", [("sensitivity_arl100", "All findings in this report are secondary"),
                                          ("benchmark", "Performance evidence only"),
                                          ("smoke", "not production evidence")])
def test_non_production_reports_claim_no_primary_status(tiny2, mode, phrase):
    _, _, res = tiny2
    md = report.tables(copy.deepcopy(res) | {"mode": mode})
    assert not [h for h in _headings(md) if "primary" in h.lower()]
    banner = next(line for line in md.splitlines() if line.startswith("**Inferential status:**"))
    assert phrase in banner
    t7a = next(h for h in _headings(md) if h.startswith("## Table 7a."))
    assert t7a.endswith(report.STATUS[mode][0] if mode in report.STATUS else "`smoke` run")
    if mode == "benchmark":
        assert "excluded from the primary production inference" in banner


def test_production_report_identifies_the_primary_endpoints(tiny2):
    cfg, _, res = tiny2
    md = report.tables(copy.deepcopy(res) | {"mode": "production"})
    pr = cfg["primary"]
    assert "## Table 7a. PRIMARY ENDPOINTS — paired contrasts, " + pr["label"] in _headings(md)
    assert any(h.startswith("## Table 8. Primary contrasts per replicate") for h in _headings(md))
    rows = _table(md, "## Table 7a.")
    got = {(r["contrast (a − b)"], r["metric"], r["δ"], r["λ"]) for r in rows}
    want = {(p, report.METRIC[m], f"{d:.3f}", f"{pr['lam']:.3f}") for p in pr["pairs"] for m in pr["metrics"]
            for d in [1.0, *cfg["deltas"]]}
    assert got == want and len(rows) == len(want)


# === Final production design: R = 20, amended IC validation rule, provenance ==================

@pytest.mark.parametrize("target, lo, hi", [(500, 425.0, 575.0), (100, 85.0, 115.0)])
def test_ic_equivalence_exact_boundaries(target, lo, hi):
    """Eq. 29: pass iff the whole CI lies in [A0(1 - 0.15), A0(1 + 0.15)], both bounds included."""
    ok = lambda a, b: chart.ic_equivalence((a, b), target, 0.15)[1]  # noqa: E731
    assert chart.ic_equivalence((target, target), target, 0.15)[0] == [lo, hi]
    up, down = np.inf, -np.inf
    assert ok(lo, hi) and ok(lo, target) and ok(target, hi)                       # exactly on the bounds
    assert ok(np.nextafter(lo, up), np.nextafter(hi, down))                       # one ulp inside
    assert not ok(np.nextafter(lo, down), target) and not ok(target, np.nextafter(hi, up))  # one ulp outside
    assert ok(target * (1 - 0.15), target * (1 + 0.15))  # float products (100 * 1.15 = 114.99999999999999) are inside
    assert not ok(target - 0.2 * target, target + 0.05 * target)                  # point on target, CI crosses lo
    assert not ok(target - 0.05 * target, target + 0.2 * target)                  # point on target, CI crosses hi
    assert not ok(lo - 50, lo - 10) and not ok(hi + 10, hi + 50) and not ok(lo - 10, hi + 10)  # clearly outside


@pytest.mark.parametrize("days, arl, se, ci, rel, passed, old_rule", [
    ([400, 500, 500, 600], 500.0, 40.824829046386, (419.983335069, 580.016664931), 0.0, False, True),
    ([460, 470, 470, 480], 470.0, 4.082482904639, (461.998333507, 478.001666493), -0.06, True, False),
    ([420, 430, 430, 440], 430.0, 4.082482904639, (421.998333507, 438.001666493), -0.14, False, False)])
def test_validate_hand_checked_examples(days, arl, se, ci, rel, passed, old_rule):
    """Hand values: SE = sd/sqrt(4) with sd = sqrt(20000/3) or sqrt(200/3); CI = ARL -/+ 1.96 SE."""
    z = np.zeros((4, 1000))
    z[np.arange(4), np.array(days) - 1] = 2.0  # first exceedance of h = 1 on the planted alarm day
    v = chart.validate(z, 1.0, 500, tau=50, tol=0.15)
    assert v["arl_restricted"] == arl and v["se_arl_restricted"] == pytest.approx(se, rel=1e-11)
    assert v["ci95"] == pytest.approx(list(ci), rel=1e-11) and v["rel_dev"] == pytest.approx(rel)
    assert (v["n_paths"], v["target"], v["tol"], v["accept"], v["passed"]) == (4, 500, 0.15, [425.0, 575.0], passed)
    lo, hi = v["ci95"]
    assert (lo <= 500 <= hi and abs(v["rel_dev"]) <= 0.15) == old_rule  # original rule, for contrast only


def test_production_streams_distinct_over_twenty_replicates():
    P, B = run.CONFIGS["production"], run.CONFIGS["benchmark"]
    draws = [g.random(4).tobytes() for rep in range(P["replicates"]) for g in run.streams(P, rep).values()]
    assert P["replicates"] == 20 and len(draws) == 20 * len(run.ROLES) == len(set(draws))
    bench = {g.random(4).tobytes() for g in run.streams(B, 0).values()}  # benchmark and pilot seed 20261013
    assert len(bench) == len(run.ROLES) and not bench & set(draws)


def test_git_provenance_classifies_untracked_files():
    """Read-only Git; the test only creates and removes two probe files in the worktree."""
    root = Path(run.__file__).resolve().parent
    tag = f"_probe_{os.getpid()}"
    src, ign = root / "src" / f"{tag}.py", root / "data" / "processed" / f"{tag}.py"
    try:
        src.write_text("")
        ign.write_text("")
        p = subprocess.run(["bash", str(root / "scripts" / "git_provenance.sh")], capture_output=True, text=True,
                           timeout=60)
    finally:
        src.unlink(missing_ok=True)
        ign.unlink(missing_ok=True)
    assert p.returncode == 0, p.stderr
    line = dict(x.split(": ", 1) for x in p.stdout.splitlines())
    assert set(line) == {"git_tracked_modified", "git_untracked_tool_state", "git_untracked_unclassified",
                         "git_ignored_python"} and line["git_tracked_modified"] in ("yes", "no")
    assert f"src/{tag}.py" in line["git_untracked_unclassified"].split() and "not assumed harmless" in line[
        "git_untracked_unclassified"]
    assert f"data/processed/{tag}.py" in line["git_ignored_python"].split()
    assert ".serena" not in line["git_untracked_unclassified"]
    if any((root / ".serena").rglob("*")):
        assert line["git_untracked_tool_state"].startswith(".serena/ (")


def test_report_lists_validation_failures_without_dropping_them(tiny2):
    cfg, _, res = tiny2
    out = copy.deepcopy(res) | {"mode": "production"}
    for rep in out["replicates"]:
        for v in rep["validation"].values():
            for k in v:
                v[k]["passed"] = True
    sch = aggregate.schema(cfg, run.CHARTS, run.PAIRS)
    out["aggregate"] = aggregate.collect(out["replicates"], sch)
    md = report.tables(out)
    assert "**Validation failures:** none." in md and "all 2 replicate(s) passed for every chart" in md
    out["replicates"][1]["validation"]["0.1"]["rf"]["passed"] = False
    out["aggregate"] = aggregate.collect(out["replicates"], sch)
    md = report.tables(out)
    assert md.count("RF-EWMA λ = 0.1: replicate(s) [1] of 2") == 2  # under Table 3 and before Table 7a
    assert "nominal ARL₀ control is not established" in md and "comparability and nominal ARL₀ control are limited" in md
    rows = _table(md, "## Table 3.")
    assert len(rows) == 2 * len(cfg["lams"]) * len(report.PRIMARY)  # every replicate and configuration kept
    assert _row(rows, rep="1", chart="RF-EWMA", **{"λ": "0.100"})["pass"] == "NO"
    assert _row(_table(md, "Across replicates:"), chart="RF-EWMA", **{"λ": "0.100"})["passed"] == "1/2"
    assert len(_table(md, "## Table 7a.")) == len(_table(report.tables(res | {"mode": "production"}), "## Table 7a."))
