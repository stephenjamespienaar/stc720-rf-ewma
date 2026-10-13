"""Mathematical and numerical correctness tests (methodology equation numbers in brackets)."""

import hashlib
import json
import sys

import numpy as np
import pandas as pd
import pytest
from scipy import stats

import run
from src import chart, sim, spy
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
