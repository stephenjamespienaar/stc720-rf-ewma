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
    assert a["monitor_csv_sha256"] != b["monitor_csv_sha256"]          # only monitoring changed


def test_deterministic_given_recorded_seed(runs):
    assert runs["a1"][1]["results_sha256"] == runs["a2"][1]["results_sha256"]
    assert runs["a1"][1]["seeds"]["master_seed"] == 20261028


def test_calibration_validation_and_rf_streams_are_distinct_and_reproducible():
    g1, g2 = app.streams(SMALL), app.streams(SMALL)
    draws = {k: g1[k].random(4).tolist() for k in g1}
    assert draws == {k: g2[k].random(4).tolist() for k in g2}
    assert len({tuple(v) for v in draws.values()}) == 3


def test_fourth_moment_gate_stops_before_limits_and_monitoring(tmp_path, monkeypatch):
    bad = sim.Garch(0.02, 0.10, 0.895, 5.0)                          # stationary (0.995), m4 > 1: fails the strict check
    assert not sim.constraint_violations(bad, need_m4=False) and sim.constraint_violations(bad)
    monkeypatch.setattr(fc, "fit_garch", lambda r: (bad, {"convergence_flag": 0, "persistence": 0.995}))
    monkeypatch.setattr(app, "limits", lambda *a: pytest.fail("limits must not be calibrated"))
    monkeypatch.setattr(app, "monitor_series", lambda *a: pytest.fail("monitoring returns must not be used"))
    spy.write_snapshot(synth_frame(), tmp_path / "data" / "raw", {"source": "synthetic"})
    assert run.run_spy(SMALL, tmp_path / "out", tmp_path) == 3
    res = json.loads((tmp_path / "out" / "results.json").read_text())
    assert res["status"] == "stopped_at_fourth_moment_gate" and res["fit"]["strict_simulator_check"]["violations"]
    assert not (tmp_path / "out" / "frozen.json").exists() and not (tmp_path / "out" / "monitor.csv").exists()


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
