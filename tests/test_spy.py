"""SPY application (methodology §11): synthetic-data tests only. No network, no real SPY data."""

import json
import subprocess
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import run
from src import application as app
from src import chart, sim, spy
from src import forecast as fc

# Toy sizes; the diagnostics are exactly those of the real SPY configuration.
SMALL = {**run.SPY, "rf_trees": 10, "rf_leaf": [50, 200], "rf_max_features": [1], "n_jobs": 2, "n_cal": 40,
         "n_val": 40, "t_max": 600, "target_arl": 50, "burn": 200}
SYNTH = sim.Garch(0.05, 0.05, 0.90, 8.0)  # unit variance, m4 = 0.911: passes the strict gate


def synth_frame(seed=0):
    """Business days 1993-01-29 .. 2026-09-30 without 2007-01-01/02 (as in the real calendar,
    no return falls between 2006-12-29 and 2007-01-03)."""
    idx = pd.bdate_range("1993-01-29", "2026-09-30")
    idx = idx[~idx.isin(pd.to_datetime(["2007-01-01", "2007-01-02"]))]
    r = sim.simulate(SYNTH, 1, len(idx) - 1, np.random.default_rng(seed), 200)[0][0]
    c = 100 * np.exp(np.concatenate([[0.0], np.cumsum(r / 100)]))
    return pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c, "Volume": 1e6}, index=idx)


def perturbed(seed=0):
    """The same prices up to 2006-12-29; every later price changed."""
    df = synth_frame(seed)
    late = df.index > pd.Timestamp("2006-12-29")
    df.loc[late, "Close"] *= np.exp(np.cumsum(np.random.default_rng(99).normal(0, 0.02, late.sum())))
    return df


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    base, out = tmp_path_factory.mktemp("spy"), {}
    for name, df in (("a1", synth_frame()), ("a2", synth_frame()), ("b", perturbed())):
        root = base / name
        spy.write_snapshot(df, root / "data" / "raw", {"source": "synthetic test frame"})
        code = run.run_spy(SMALL, root / "out", root)
        out[name] = (code, json.loads((root / "out" / "results.json").read_text()), root / "out")
    return out


# --- data ------------------------------------------------------------------------------------

def test_download_snapshot_passes_s1_arguments_and_freezes(tmp_path, monkeypatch):
    seen = {}

    def fake(ticker, **kw):
        seen.update(kw, ticker=ticker)
        return synth_frame()
    monkeypatch.setitem(sys.modules, "yfinance", types.SimpleNamespace(download=fake, __version__="1.7.0"))
    path = spy.download_snapshot(tmp_path)
    assert seen["ticker"] == "SPY" and seen["auto_adjust"] is True and seen["multi_level_index"] is False
    assert seen["repair"] is False and seen["keepna"] is True and (seen["start"], seen["end"]) == ("1993-01-29", "2026-10-01")
    meta = json.loads(path.with_suffix(".meta.json").read_text())
    assert meta["yfinance_version"] == "1.7.0" and meta["accessed_utc"] and len(meta["sha256"]) == 64
    assert meta["first_date"] == "1993-01-29" and "back-adjusted" in meta["note"] and "Volume" in meta["columns"]
    pd.testing.assert_series_equal(spy.load_snapshot(path), synth_frame()["Close"], check_freq=False, check_names=False)
    with pytest.raises(FileExistsError):
        spy.download_snapshot(tmp_path)          # the frozen snapshot is never overwritten
    path.write_text(path.read_text().replace("1993-02-01", "1993-02-02", 1))
    with pytest.raises(ValueError, match="SHA-256"):
        spy.load_snapshot(path)


def test_integrity_hard_errors_and_row_count_is_only_diagnostic():
    c = synth_frame()["Close"]
    rep = spy.integrity(c, "1993-01-29", "2026-09-30")
    assert rep["errors"] == [] and rep["rows_in_expected_range"] is False   # about 8,600 business days: flagged only
    bad = {
        "duplicate": pd.concat([c, c.iloc[[5]]]).sort_index(),
        "unsorted": c.iloc[::-1],
        "tz": c.tz_localize("America/New_York"),
        "nan": c.mask(c.index == c.index[100]),
        "nonpositive": c.mask(c.index == c.index[100], 0.0),
        "first date": c.iloc[1:],
        "late": pd.concat([c, pd.Series([c.iloc[-1]], index=[pd.Timestamp("2026-10-01")])]),
    }
    for name, x in bad.items():
        assert spy.integrity(x, "1993-01-29", "2026-09-30")["errors"], name
    gap = c.drop(c.index[(c.index > "2001-09-10") & (c.index < "2001-09-17")])
    assert ("2001-09-10", "2001-09-17", 7) in [tuple(g) for g in spy.integrity(gap, "1993-01-29", "2026-09-30")["calendar_gaps_over_4_days"]]


def test_return_boundaries_and_training_only_mean():
    close = synth_frame()["Close"]
    tr, mo, mu = app.returns(close, SMALL)
    r = spy.log_returns(close)
    assert (tr.index[0], tr.index[-1], mo.index[0], mo.index[-1]) == tuple(map(pd.Timestamp, (
        "1993-02-01", "2006-12-29", "2007-01-03", "2026-09-30")))
    assert mu == pytest.approx(r[:"2006-12-29"].mean(), abs=1e-14)
    assert np.allclose(mo.to_numpy(), r["2007-01-03":].to_numpy() - mu, atol=0, rtol=1e-15)   # same training mean
    extra = synth_frame()["Close"]
    extra.loc[pd.Timestamp("2007-01-02")] = extra.iloc[-1]
    with pytest.raises(ValueError, match="between training and monitoring"):
        app.returns(extra.sort_index(), SMALL)
    with pytest.raises(ValueError, match="last training return"):
        app.returns(close.drop(pd.Timestamp("2006-12-29")), SMALL)


# --- fitting, limits and leakage ------------------------------------------------------------

def test_pipeline_completes_and_freezes(runs):
    code, res, out = runs["a1"]
    assert code == 0 and res["status"] == "complete" and all(res["frozen_checks"].values())
    for f in ("config.json", "results.json", "frozen.json", "monitor.csv", "tables.md", "fig_spy_charts.png",
              "fig_spy_variance.png"):
        assert (out / f).exists(), f
    g = res["fit"]["rf_grid"]
    assert sum(c["selected"] for c in g) == 1 and min(g, key=lambda c: c["dev_qlike"])["selected"]
    sel = res["fit"]["rf_selection"]
    assert sel["dev_first"] == "2004-01-01" and sel["fit_rows"] + sel["dev_rows"] == res["data"]["n_train"]
    assert res["fit"]["strict_simulator_check"]["passed"] and set(res["limits"]["h"]) == {"0.1", "0.2"}


def test_post_2006_price_changes_leave_training_fits_and_limits_unchanged(runs):
    a, b = runs["a1"][1], runs["b"][1]
    assert a["data"]["train_mean"] == b["data"]["train_mean"]
    assert a["fit"] == b["fit"] and a["limits"] == b["limits"]          # bit-identical, incl. RF fingerprint and h*
    assert a["diagnostics"] == b["diagnostics"]                          # and every calibration diagnostic
    assert a["monitor_csv_sha256"] != b["monitor_csv_sha256"]          # only monitoring changed


def test_deterministic_given_recorded_seed(runs):
    assert runs["a1"][1]["results_sha256"] == runs["a2"][1]["results_sha256"]
    assert runs["a1"][1]["seeds"]["master_seed"] == 20261028


def test_calibration_validation_and_rf_streams_are_distinct_and_reproducible():
    g1, g2 = app.streams(SMALL), app.streams(SMALL)
    draws = {k: g1[k].random(4).tolist() for k in g1}
    assert draws == {k: g2[k].random(4).tolist() for k in g2}
    assert len({tuple(v) for v in draws.values()}) == 3


def _stopped(tmp_path, monkeypatch, cfg, gp):
    monkeypatch.setattr(fc, "fit_garch_vt", lambda r, s2: (gp, {"estimator": "variance_targeted", "convergence_flag": 0}))
    monkeypatch.setattr(fc, "fit_garch", lambda r: (gp, {"convergence_flag": 0}))
    monkeypatch.setattr(app, "limits", lambda *a: pytest.fail("limits must not be calibrated"))
    monkeypatch.setattr(app, "monitor_series", lambda *a: pytest.fail("monitoring returns must not be used"))
    spy.write_snapshot(synth_frame(), tmp_path / "data" / "raw", {"source": "synthetic"})
    assert run.run_spy(cfg, tmp_path / "out", tmp_path) == 3
    assert not (tmp_path / "out" / "frozen.json").exists() and not (tmp_path / "out" / "monitor.csv").exists()
    return json.loads((tmp_path / "out" / "results.json").read_text())


def test_strict_mode_still_stops_at_fourth_moment_gate(tmp_path, monkeypatch):
    bad = sim.Garch(0.02, 0.10, 0.895, 5.0)                          # stationary (0.995), m4 > 1
    assert not sim.constraint_violations(bad, need_m4=False) and sim.constraint_violations(bad)
    res = _stopped(tmp_path, monkeypatch, {**SMALL, "finite_variance_simulation": False}, bad)
    assert res["status"] == "stopped_at_fourth_moment_gate" and res["fit"]["strict_simulator_check"]["violations"]


@pytest.mark.parametrize("gp, stop", [(sim.Garch(0.02, 0.10, 0.92, 5.0), "a"),     # alpha + beta = 1.02
                                      (sim.Garch(1e-5, 0.02, 0.9799, 6.0), "b")])  # 0.9999^200 > 1e-3
def test_finite_variance_mode_stops_on_admissibility_and_burn_in(tmp_path, monkeypatch, gp, stop):
    res = _stopped(tmp_path, monkeypatch, SMALL, gp)
    assert res["status"] == f"stopped_at_diagnostic_{stop}"
    failed = [c["id"] for c in res["diagnostics"]["checks"] if not c["passed"]]
    assert failed[0] == stop                                       # all pre-limit checks recorded; first failure stops


def test_numerical_failure_stops_before_monitoring(tmp_path, monkeypatch):
    def boom(*a):
        raise FloatingPointError("finite-variance simulation produced non-finite or non-positive values")
    monkeypatch.setattr(app, "limits", boom)
    monkeypatch.setattr(app, "monitor_series", lambda *a: pytest.fail("monitoring returns must not be used"))
    spy.write_snapshot(synth_frame(), tmp_path / "data" / "raw", {"source": "synthetic"})
    assert run.run_spy(SMALL, tmp_path / "out", tmp_path) == 3
    res = json.loads((tmp_path / "out" / "results.json").read_text())
    assert res["status"] == "stopped_at_diagnostic_c" and not (tmp_path / "out" / "frozen.json").exists()


def test_strict_simulator_output_is_bit_identical_to_committed_code():
    """Reference hash computed from src/sim.py at commit 7e2eaa1 (before the opt-in existed)."""
    import hashlib
    r, h = sim.simulate(sim.Garch(0.02, 0.07, 0.91, 6.0), 3, 200, np.random.default_rng(20261028), 100)
    assert hashlib.sha256(r.tobytes() + h.tobytes()).hexdigest() == \
        "465f466d860f75a28ed3644b23ec15a22a342b6266aa639b244761fafc5e9839"
    r2, h2 = sim.simulate(sim.Garch(0.02, 0.07, 0.91, 6.0), 3, 200, np.random.default_rng(20261028), 100, need_m4=False)
    assert np.array_equal(r, r2) and np.array_equal(h, h2)        # the opt-in changes only the admissibility check


def test_finite_variance_option_accepts_infinite_fourth_moment_and_rejects_invalid_models():
    b = sim.Garch(0.00513, 0.0593, 0.9363, 7.63)                 # model B (rounded): finite variance, m4 > 1
    assert not sim.moments(b)["finite_fourth_moment"]
    with pytest.raises(ValueError, match="m4"):
        sim.simulate(b, 2, 50, np.random.default_rng(0))           # strict default refuses it
    r, h = sim.simulate(b, 2, 500, np.random.default_rng(0), 2000, need_m4=False)
    assert np.isfinite(r).all() and (h > 0).all()
    for bad in (sim.Garch(0.02, 0.10, 0.90, 6.0), sim.Garch(0.02, 0.05, 0.90, 2.0), sim.Garch(0.0, 0.05, 0.90, 6.0),
                sim.Garch(0.02, -0.01, 0.90, 6.0), sim.Garch(0.02, 0.05, -0.1, 6.0)):
        for need in (True, False):
            with pytest.raises(ValueError):
                sim.simulate(bad, 1, 10, np.random.default_rng(0), need_m4=need)


def test_finite_variance_option_refuses_non_finite_simulations():
    with np.errstate(over="ignore", invalid="ignore"):
        with pytest.raises(FloatingPointError):
            sim.simulate(sim.Garch(1e306, 0.30, 0.65, 2.5), 50, 400, np.random.default_rng(1), 10, need_m4=False)


def test_standardized_t_innovations_have_unit_variance():
    nu = 7.63
    e = sim.std_t(np.random.default_rng(3), nu, 2_000_000)
    assert np.array_equal(e, np.random.default_rng(3).standard_t(nu, 2_000_000) * np.sqrt((nu - 2) / nu))
    assert e.var() == pytest.approx(1.0, rel=0.01) and sim.Garch(0.1, 0.05, 0.9, nu).kappa == pytest.approx(
        3 * (nu - 2) / (nu - 4))


def test_calibration_and_validation_draw_from_their_own_streams(monkeypatch):
    tr, _, _ = app.returns(synth_frame()["Close"], SMALL)
    g = app.streams(SMALL)
    f = app.fit(tr, SMALL, 3)
    seen, real = [], sim.simulate
    monkeypatch.setattr(sim, "simulate", lambda p, n, m, rng, burn, need_m4: seen.append(rng) or real(p, n, m, rng, burn,
                                                                                                    need_m4=need_m4))
    app.limits(f, SMALL, g)
    assert seen == [g["cal"], g["val"]] and seen[0] is not seen[1]


def test_restricted_run_length_convention():
    z = np.array([[0.1, 0.2, 2.0, 0.1, 0.1], [0.1, 0.1, 0.1, 0.1, 0.1], [0.1, 0.1, 0.1, 0.1, 2.0]])
    t, cens = chart.first_alarm(z, 1.0)
    assert t.tolist() == [3, 5, 5] and cens.tolist() == [False, True, False]   # censored path counts t_max = 5
    h, arl = chart.calibrate(np.random.default_rng(0).gamma(2.0, 0.5, (300, 400)).cumsum(axis=1) / np.arange(1, 401), 50)
    assert arl >= 50


def _diag_inputs(**over):
    c = {"h": 2.0, "arl_cal": 500.2, "restricted_mean_check": 500.2, "censored_cal": 0.0, "overshoot_rel": 0.0004,
         "arl_just_below_h": 499.9, "split_half_arl": [490.0, 510.0]} | over
    v = {"ci95": [470.0, 530.0], "accept": [425.0, 575.0], "passed": True, "rel_se": 0.02}
    return {"0.1": {"rf": c}}, {"0.1": {"rf": v}}, {"cal_max_h": 50.0, "val_max_h": 60.0, "cal_max_u": {"rf": 30.0}}


@pytest.mark.parametrize("over, num, stop", [
    ({"censored_cal": 0.01}, None, None),                            # at the threshold: passes (<= 0.01)
    ({"censored_cal": 0.0100001}, None, "d"),                       # full precision: just above stops
    ({"overshoot_rel": 0.0011, "arl_cal": 500.55, "restricted_mean_check": 500.55}, None, None),  # warning only
    ({"arl_just_below_h": 500.0}, None, "e"),                       # h* not minimal: hard stop
    ({"h": float("nan")}, None, "e"),                               # non-finite limit: hard stop
    ({"h": 0.0}, None, "e"),                                        # non-positive limit: hard stop
    ({"h": -1.0}, None, "e"),
    ({"restricted_mean_check": 500.3}, None, "e"),                  # inconsistent restricted-mean computation
    ({"split_half_arl": [400.0, 600.0]}, None, None),               # split-half: warning only
    ({"split_half_arl": [425.0, 575.0]}, None, None),               # exact inclusive bounds pass
    ({}, {"cal_max_h": float("inf")}, "c"),
])
def test_diagnostic_thresholds_and_actions(over, num, stop):
    cal, val, n = _diag_inputs(**over)
    checks, got = app.diagnose(cal, val, n | (num or {}), run.SPY)
    assert got == stop
    if over.get("split_half_arl") == [400.0, 600.0]:
        assert [c["id"] for c in checks if not c["passed"]] == ["f"] and checks[-1]["action"] == "warn"
    if over.get("split_half_arl") == [425.0, 575.0]:
        assert all(c["passed"] for c in checks)


def test_overshoot_is_a_recorded_warning_with_exact_values():
    cal, val, n = _diag_inputs(overshoot_rel=0.0016, arl_cal=500.8, restricted_mean_check=500.8)
    checks, stop = app.diagnose(cal, val, n, run.SPY)
    assert stop is None and run.SPY["diagnostics"]["overshoot_action"] == "warn"
    o = next(c for c in checks if c["id"] == "e_overshoot")
    assert not o["passed"] and o["action"] == "warn" and o["threshold"] == "<= 0.001"
    assert o["value"] == {"overshoot_rel": 0.0016, "achieved_restricted_arl": 500.8, "target_deviation": 500.8 - 500}
    assert next(c for c in checks if c["id"] == "e")["passed"]          # the hard part of e still passes


def test_bisection_failure_is_a_hard_stop(tmp_path, monkeypatch):
    monkeypatch.setattr(chart, "calibrate", lambda z, t: (_ for _ in ()).throw(ValueError("no bracket")))
    monkeypatch.setattr(app, "monitor_series", lambda *a: pytest.fail("monitoring returns must not be used"))
    spy.write_snapshot(synth_frame(), tmp_path / "data" / "raw", {"source": "synthetic"})
    assert run.run_spy(SMALL, tmp_path / "out", tmp_path) == 3
    res = json.loads((tmp_path / "out" / "results.json").read_text())
    assert res["status"] == "stopped_at_diagnostic_e" and "no bracket" in res["diagnostics"]["checks"][-1]["value"]
    assert not (tmp_path / "out" / "frozen.json").exists()


def test_results_preserve_overshoot_and_diagnostic_status(runs):
    res = runs["a1"][1]
    for lam, row in res["limits"]["calibration"].items():
        for k, c in row.items():
            assert c["overshoot_rel"] == c["arl_cal"] / SMALL["target_arl"] - 1
            assert c["target_deviation"] == c["arl_cal"] - SMALL["target_arl"] and c["arl_cal"] == c["restricted_mean_check"]
    ov = [c for c in res["diagnostics"]["checks"] if c["id"] == "e_overshoot"]
    assert len(ov) == 6 and all(set(c["value"]) == {"overshoot_rel", "achieved_restricted_arl", "target_deviation"} for c in ov)
    assert all(c["passed"] for c in res["diagnostics"]["checks"] if c["id"] == "e")       # hard part holds
    assert res["diagnostics"]["criteria"] == run.SPY["diagnostics"]


def test_warnings_never_trigger_recalibration(tmp_path, monkeypatch):
    calls, real = [], chart.calibrate
    monkeypatch.setattr(chart, "calibrate", lambda z, t: calls.append(1) or real(z, t))
    spy.write_snapshot(synth_frame(), tmp_path / "data" / "raw", {"source": "synthetic"})
    assert run.run_spy(SMALL, tmp_path / "out", tmp_path) == 0
    res = json.loads((tmp_path / "out" / "results.json").read_text())
    assert res["status"] == "complete" and res["diagnostics"]["warnings"]        # toy sizes produce warnings
    assert len(calls) == len(SMALL["lams"]) * len(app.CHARTS)                    # each limit calibrated exactly once


def test_production_simulator_defaults_are_unchanged():
    assert not sim.constraint_violations(sim.Garch(**run.DGP))
    bad = sim.Garch(0.02, 0.10, 0.895, 5.0)
    with pytest.raises(ValueError, match="m4"):
        sim.simulate(bad, 1, 10, np.random.default_rng(0))
    with pytest.raises(ValueError, match="nu > 4"):
        sim.simulate(sim.Garch(0.02, 0.05, 0.90, 4.0), 1, 10, np.random.default_rng(0))


# --- monitoring --------------------------------------------------------------------------------

def test_monitoring_forecasts_use_only_past_returns():
    close = synth_frame()["Close"]
    tr, mo, _ = app.returns(close, SMALL)
    f = app.fit(tr, SMALL, 7)
    k = 1000
    mo2 = mo.copy()
    mo2.iloc[k:] *= 3.0
    d1, u1, _ = app.monitor_series(tr, mo, f, SMALL)
    d2, u2, _ = app.monitor_series(tr, mo2, f, SMALL)
    for c in app.CHARTS:
        assert np.array_equal(d1[c][: k + 1], d2[c][: k + 1]) and np.array_equal(u1[c][:k], u2[c][:k])
        z1, z2 = chart.ewma(u1[c], 0.1)[0], chart.ewma(u2[c], 0.1)[0]
        assert np.array_equal(z1[:k], z2[:k])
    assert not np.array_equal(d1["garch"][k + 1:], d2["garch"][k + 1:])


def test_continuous_ewma_has_no_reset(runs):
    df = pd.read_csv(runs["a1"][2] / "monitor.csv")
    for c in app.CHARTS:
        u, z = df[f"u_{c}"].to_numpy(), df[f"z_{c}_0.1"].to_numpy()
        prev = np.concatenate([[1.0], z[:-1]])
        assert np.allclose(z, 0.1 * u + 0.9 * prev, rtol=1e-12, atol=0)   # every day, also after exceedances
    z = chart.ewma(np.array([0.5, 40.0, 0.5, 0.5]), 0.1)[0]
    assert z[2] == pytest.approx(0.1 * 0.5 + 0.9 * z[1]) and z[1] > 3      # still above a limit of 3: not reset


def test_episode_definition_hand_example():
    ex, eps = chart.episodes([0.5, 1.2, 1.3, 1.0, 1.1, 1.1, 0.8, 2.0], 1.0)
    assert ex.tolist() == [False, True, True, False, True, True, False, True]   # Z = h is not an exceedance
    assert eps == [(1, 2), (4, 5), (7, 7)]
    assert chart.episodes([1.5], 1.0)[1] == [(0, 0)]                            # Z_0 = 1 <= h, so day 1 starts one
    with pytest.raises(ValueError):
        chart.episodes([0.5], 0.9, z0=1.0)


def test_reference_states_hand_example():
    dates = pd.bdate_range("2020-01-01", periods=8)
    z = np.array([0.5, 1.5, 0.5, 0.5, 2.0, 2.0, 0.5, 3.0])
    cfg = {"event_window": 3, "reference_dates": [{"date": str(dates[1].date())}, {"date": str(dates[2].date())},
                                                  {"date": str(dates[6].date())}]}
    s = app.reference_states(dates, z, 1.0, cfg)
    assert [x["active_on_date"] for x in s] == [True, False, False]
    assert [x["first_exceedance_offset"] for x in s] == [0, 2, 1]
    assert [x["crossings_in_window"] for x in s] == [1, 1, 1] and s[2]["window_days"] == 2   # truncated at the end
    assert [x["exceedance_days_in_window"] for x in s] == [1, 1, 1] and s[1]["max_z_over_h_in_window"] == 2.0
    with pytest.raises(ValueError, match="never moved"):
        app.reference_states(dates, z, 1.0, {"event_window": 3, "reference_dates": [{"date": "2020-01-04"}]})


def test_reported_monitoring_counts_match_saved_series(runs):
    res, out = runs["a1"][1], runs["a1"][2]
    df = pd.read_csv(out / "monitor.csv")
    for lam in ("0.1", "0.2"):
        for c in app.CHARTS:
            m = res["monitoring"][lam][c]
            ex, eps = chart.episodes(df[f"z_{c}_{lam}"].to_numpy(), m["h"])
            assert m["exceedance_days"] == ex.sum() and m["episodes"] == len(eps) == len(m["episode_list"])
    assert len(res["monitoring"]["0.1"]["rf"]["reference_dates"]) == len(run.SPY["reference_dates"])


# --- configuration and guards ---------------------------------------------------------------

def test_spy_configuration_matches_approved_design():
    c = run.SPY
    assert (c["first_price"], c["train_start"], c["train_end"], c["monitor_start"], c["monitor_end"]) == (
        "1993-01-29", "1993-02-01", "2006-12-29", "2007-01-03", "2026-09-30")
    assert c["master_seed"] == 20261028 and c["lams"] == [0.1, 0.2] and c["primary_lam"] == 0.1
    assert c["rf_trees"] == 500 and c["rf_leaf"] == [50, 200, 800] and c["rf_max_features"] == [1, 3]
    assert c["target_arl"] == 500 and c["ic_validation"]["tol"] == 0.15 and c["event_window"] == 63
    d = pd.to_datetime([r["date"] for r in c["reference_dates"]])
    assert d.is_monotonic_increasing and (d > pd.Timestamp(c["monitor_start"])).all() and (d.dayofweek < 5).all()


def test_spy_mode_is_guarded(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "run_spy", lambda *a: pytest.fail("must not run"))
    monkeypatch.setattr(sys, "argv", ["run.py", "spy", "--out", str(tmp_path / "o")])
    with pytest.raises(SystemExit) as e:
        run.main()
    assert "--approved" in str(e.value.code) and not (tmp_path / "o").exists()
    called = []
    monkeypatch.setattr(run, "run_spy", lambda *a: called.append(a) or 0)
    monkeypatch.setattr(sys, "argv", ["run.py", "spy", "--approved", "--out", str(tmp_path / "o")])
    with pytest.raises(SystemExit) as e:
        run.main()
    assert e.value.code == 0 and called == [(run.CONFIGS["spy"], tmp_path / "o")]
    root = Path(run.__file__).resolve().parent
    runs_dir = root / "results" / "runs"
    before = set(runs_dir.iterdir())
    p = subprocess.run(["bash", str(root / "scripts" / "run_simulation.sh"), "spy"], capture_output=True, text=True,
                       timeout=60)
    assert p.returncode == 2 and "--approved" in p.stderr and set(runs_dir.iterdir()) == before


# --- variance-targeted GARCH-t (post-stop refinement, 27 Oct 2026) ------------------------------

def vt_path(p, n, seed):
    return sim.simulate(p, 1, n, np.random.default_rng(seed), 1000)[0][0]


def test_vt_likelihood_equals_standardized_t_density():
    from scipy import stats
    r = vt_path(SYNTH, 400, 3)
    om, a, b, nu, h1 = 0.04, 0.06, 0.90, 6.5, 1.1
    nll, h = fc.garch_t_nll(r, om, a, b, nu, h1)
    hh, ll = h1, 0.0
    for t, x in enumerate(r):                      # explicit loop and SciPy's t density, independent of lfilter
        if t:
            hh = om + a * r[t - 1] ** 2 + b * hh
        sc = np.sqrt(hh * (nu - 2) / nu)           # unit-variance t: eta = sqrt((nu-2)/nu) T (sim.std_t)
        ll += stats.t.logpdf(x / sc, nu) - np.log(sc)
        assert h[t] == pytest.approx(hh, rel=1e-12)
    assert nll == pytest.approx(-ll, rel=1e-10)


def test_vt_identity_admissibility_and_recovery():
    true = sim.Garch(0.02, 0.07, 0.91, 6.0)        # the production DGP
    r = vt_path(true, 20000, 11)
    p, info = fc.fit_garch_vt(r)
    s2 = float(np.mean(r**2))
    assert p.omega == pytest.approx(s2 * (1 - p.alpha - p.beta), rel=1e-14) and p.var == pytest.approx(s2, rel=1e-12)
    assert p.alpha >= 0 and p.beta >= 0 and p.alpha + p.beta < 1 and p.nu > 2
    assert abs(p.alpha - 0.07) < 0.02 and abs(p.beta - 0.91) < 0.03 and abs(p.nu - 6) < 1.5
    assert info["convergence_flag"] == 0 and info["n_at_best"] >= info["n_starts"] // 2   # optima agree across starts
    assert info["max_param_spread_at_best"] < 1e-3 and info["estimator"] == "variance_targeted"


def raw_garch_t(p, n, seed, burn=3000):
    """Test-only GARCH-t path without the production simulator's strict fourth-moment check."""
    eta = sim.std_t(np.random.default_rng(seed), p.nu, burn + n)
    r, h = np.empty(burn + n), p.var
    for t in range(burn + n):
        r[t] = np.sqrt(h) * eta[t]
        h = p.omega + p.alpha * r[t] ** 2 + p.beta * h
    return r[burn:]


def test_vt_admissible_for_near_integrated_data_with_infinite_fourth_moment():
    true = sim.Garch(0.002, 0.06, 0.938, 7.0)                       # persistence 0.998, m4 = 1.010
    assert not sim.moments(true)["finite_fourth_moment"]
    r = raw_garch_t(true, 4000, 6)
    p, info = fc.fit_garch_vt(r)
    assert p.alpha >= 0 and p.beta >= 0 and p.alpha + p.beta < 1 and p.nu > 2 and info["convergence_flag"] == 0
    assert p.var == pytest.approx(np.mean(r**2), rel=1e-12)


def test_vt_refuses_unidentified_data_explicitly():
    """iid normal returns: alpha -> 0 leaves beta unidentified and nu -> infinity; the estimator must
    fail loudly, never return a clipped or silently doubtful fit."""
    with pytest.raises(RuntimeError, match="unusable"):
        fc.fit_garch_vt(np.random.default_rng(5).normal(0, 1.2, 4000))


def test_vt_fit_is_deterministic():
    r = vt_path(SYNTH, 3000, 8)
    assert fc.fit_garch_vt(r) == fc.fit_garch_vt(r)


def test_moment_conditions_distinguish_second_and_fourth():
    spy_like = sim.Garch(0.00457, 0.0599, 0.9377, 7.35)        # the stopped run's unrestricted SPY fit (rounded)
    m = sim.moments(spy_like)
    assert m["finite_variance"] and not m["finite_fourth_moment"] and not m["strict_gate"] and m["m4"] > 1
    assert 250 < m["half_life_days"] < 330
    d = sim.moments(sim.Garch(**run.DGP))
    assert d["finite_variance"] and d["finite_fourth_moment"] and d["strict_gate"]
    t = sim.moments(sim.Garch(0.02, 0.05, 0.90, 3.5))          # finite variance, kappa infinite
    assert t["finite_variance"] and not t["finite_fourth_moment"] and t["kappa"] == np.inf
    assert not sim.moments(sim.Garch(0.02, 0.10, 0.90, 6.0))["finite_variance"]


def test_estimator_selected_only_by_spy_config(monkeypatch):
    assert run.SPY["garch_estimator"] == "variance_targeted"
    assert all("garch_estimator" not in run.CONFIGS[m] for m in ("smoke", "pilot", "production", "sensitivity_arl100",
                                                                  "benchmark"))
    tr, _, _ = app.returns(synth_frame()["Close"], SMALL)
    used = []
    monkeypatch.setattr(fc, "fit_garch_vt", lambda r, s2: used.append("vt") or (SYNTH, {"estimator": "variance_targeted"}))
    monkeypatch.setattr(fc, "fit_garch", lambda r: used.append("mle") or (SYNTH, {}))
    monkeypatch.setattr(fc, "fit_rf", lambda *a, **k: pytest.skip("estimator choice checked before the forest"))
    cfg = {k: v for k, v in SMALL.items() if k != "garch_estimator"}
    with pytest.raises(pytest.skip.Exception):
        app.fit(tr, cfg, 1)                                     # default: unrestricted ML
    with pytest.raises(pytest.skip.Exception):
        app.fit(tr, SMALL, 1)                                   # SPY config: variance-targeted
    assert used == ["mle", "vt"]


def test_spy_pipeline_uses_targeted_fit_trained_on_pre_2007_only(runs):
    a, b = runs["a1"][1], runs["b"][1]
    g = a["fit"]["garch"]
    assert g["estimator"] == "variance_targeted" and g["unconditional_var"] == pytest.approx(a["fit"]["s2"], rel=1e-12)
    assert a["fit"] == b["fit"]                                  # post-2006 changes leave the targeted fit unchanged
