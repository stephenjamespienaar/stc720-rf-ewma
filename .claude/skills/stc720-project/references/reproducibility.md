# Environment, execution, reproducibility and Git rules

## Environment (verified 13 Oct 2026)

- **Python:** Ubuntu WSL2 (kernel 6.18), Python **3.14.4** in `.venv/`, which is a venv over the system python.
- **Package pins** (`requirements-lock.txt`): numpy 2.5.4, pandas 3.0.6, scipy 1.18.1, scikit-learn 1.9.1, arch 8.0.0, matplotlib 3.11.2, joblib 1.6.0, statsmodels 0.15.0, yfinance 1.7.0, pytest 9.1.1.
- **Hardware:** 20 logical CPUs, 7,938,636 KiB (≈ 7.57 GiB) RAM. GNU time at `/usr/bin/time`. GNU time's "kbytes" are KiB, and `run.py`'s `peak_rss_mb` values are MiB.
- **Policy:** new dependencies need the user's approval (CLAUDE.md §11).

## Code map

| Path | Role |
|---|---|
| `src/sim.py` | `Garch` parameters and constraint checks (`constraint_violations`, `check`); `simulate` (vectorized GARCH-t; enforces 4th-moment margin ≤ 0.99); `scale_shift` (fault) |
| `src/forecast.py` | `har_features` (strictly lagged); `fit_garch` (`arch`, zero mean, t; asserts constraints); `garch_filter`; `fit_rf`; `predict_rf` (fixed-order tree sum, floor count); `qlike`; `mse`; `slope` (OLS slope, one normalisation) |
| `src/chart.py` | `ewma` (lfilter); `first_alarm`; `calibrate` (bisection on restricted ARL); `validate`; `delays`; `delay_summary`; `paired_diff` (bootstrap, to be replaced in C3); `window_mean`; `masking_ratio`; `garch_masking_theory`; `brook_evans_arl` |
| `src/spy.py` | `download_snapshot` (**do not call without authorization**); `load_snapshot` (SHA-256 check); `log_returns`; `split` |
| `src/report.py` | 7 Markdown tables and 2 figures (replicate 0 only, until C5). Table 4 shows each chart's n eval. Table 6 includes the δ = 1 contrasts |
| `run.py` | `CONFIGS` (`smoke`, `pilot`, `production: None`); `replicate()` pipeline; `ROLES` seeds; `Timer`; results hash; `refuse_overwrite` (never writes into a directory that already holds its `ARTIFACTS`) |
| `scripts/run_simulation.sh` | Execution wrapper |
| `tests/test_core.py` | 34 tests (as parametrized) |

## Commands

```bash
.venv/bin/python -m pytest -q                 # 34 passed (14 Oct 2026)
scripts/run_simulation.sh smoke               # tiny end-to-end run (~2 s)
scripts/run_simulation.sh verify              # smoke twice; compares results hashes
scripts/run_simulation.sh pilot               # reduced pilot (~4 s); canonical hash f92f0715… came from the PRE-remediation source (see below)
# NOT AUTHORIZED: scripts/run_simulation.sh production | sensitivity | any SPY download
```

**What the wrapper does:**
- Creates `results/runs/<mode>_<YYYYmmddTHHMMSS>_<pid>/`.
- Writes:
  - `provenance.txt` (host, `nproc --all`, memory, Python, read-only `git rev-parse` / `branch --show-current` / dirty flag, thread limits)
  - `time.txt` and `resources.txt` (wall, CPU, CPU%, peak RSS, exit status)
  - `stdout.log`, `stderr.log`, `exit_status.txt`, `pip_freeze.txt`, `git_status.txt`, `git_diff_stat.txt`
- `run.py` adds `config.json` (written before computing), `results.json`, `tables.md`, `fig_delay.png` and `fig_profile.png`.
- It sets `OMP/MKL/OPENBLAS/NUMEXPR_NUM_THREADS=1`; RF parallelism uses `n_jobs` = 16 threads (one controlled level).
- Logs are preserved on failure, and the run's exit status is passed through.

## Seeds and determinism

- Master seed **20261013**. Each role draws from `np.random.SeedSequence(master, spawn_key=(replicate, role))`, with roles train 0, dev 1, cal 2, val 3, ooc 4, rf 5, boot 6. The RF `random_state` comes from the `rf` stream.
- `results_sha256` hashes `results.json`, excluding timing, environment and start time.
- Bit-for-bit reproducibility is **demonstrated only on this machine and environment**: `verify` passed, and three identical pilot hashes were produced. Do not claim more.
- **Canonical hash and current code.**
  - `f92f0715…` was produced by **uncommitted** source (HEAD `2a06da8`, dirty).
  - The 14 Oct remediation changed exactly one numerical output: `slope_h` now has one normalisation, which multiplies it by (n−1)/n.
  - A rerun of `pilot` with the current code is therefore expected to give a **different** hash. This was confirmed at smoke scale, where only `slope_h` differed; the pilot was not rerun.
  - Do not describe the pilot as generated from committed source. Future-run provenance: production-plan.md §Source provenance.
- RF prediction is deterministic across thread counts (fixed tree order; tested). RF fitting is deterministic given `random_state`.

## Artifacts and data

- `results/runs/` is **git-ignored**, so its contents are local only. **Never delete or overwrite** these directories. `run.py` refuses to write into a directory that already holds `config.json`, `results.json`, `tables.md`, figures or verify outputs. The wrapper's provenance and log files are allowed. `setup.sh` regenerates `.gitignore` with `results/runs/`.
- Canonical Phase 1 runs:
  - pilot: `pilot_20261013T075339_142070` (hash `f92f07159b682406…`)
  - earlier identical pilots: `pilot_20261013T075248_140805`, `pilot_20261013T075253_141069`; `pilot_20261013T075123_139095` is before the slope diagnostic was added
  - smoke runs
  - verify: `verify_20261013T075053_138405`
- `data/raw/` and `data/processed/` are git-ignored and currently empty. A SPY snapshot, once authorized, must be saved once with its metadata and SHA-256. Never re-download silently.
- `results/figures/` and `results/tables/` are git-ignored and intended for the final report outputs.

## Git rules (CLAUDE.md §13)

- **The user alone** stages, commits, pushes, pulls, merges, rebases, resets, tags, releases, and modifies history or config.
- **Allowed for Claude (read-only):** `git status`, `diff`, `diff --check`, `log`, `show`, `ls-files`, `rev-parse`, `branch --show-current`.
- **Never** add Claude, Anthropic or AI co-author, `Co-authored-by` or `Signed-off-by` trailers. Do not create commits under any identity.
- At milestones: summarise the changes, list the files, report tests, suggest a concise commit message, and wait for the user.
