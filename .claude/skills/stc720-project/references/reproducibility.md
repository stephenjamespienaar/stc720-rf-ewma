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
| `src/chart.py` | `mean_se` (estimate + `se_` sibling); `ewma` (lfilter); `first_alarm`; `alarm_days` (censored = n + 1); `calibrate` (bisection on restricted ARL); `ic_equivalence` (amended validation rule, eq. 29, exact rational comparison); `validate` (adds target, tol, bounds, rel. dev., N); `delays_from_days` / `delays`; `detected`; `cond_quantile` (censoring-aware, eq. 25); `delay_summary` (with X(k) via `base`, eq. 24); `paired_diff` (normal paired SE, optional bootstrap check, eq. 23); per-path `window_mean`; `ratio_se` (delta method, eq. 26); `masking_ratio`; `garch_masking_theory`; `brook_evans_arl` |
| `src/aggregate.py` | `across` (equal-weight replicate mean, t CI, s_b, residual between-system SD σ̂_sys = `sd_between_resid`, sign test; eqs. 27–28); `schema` (explicit allowlist: estimands, flags, counts); `collect` |
| `src/spy.py` | `download_snapshot` (**do not call without authorization**); `load_snapshot` (SHA-256 check); `log_returns`; `split` |
| `src/report.py` | Tables 1–9 (per-replicate and aggregate; primary endpoints separate; diagnostic section separate) and figures `fig_delay`, `fig_profile`, `fig_replicates` |
| `run.py` | `CONFIGS` (`smoke` R = 2, `pilot`, guarded `production`, `sensitivity_arl100`, `benchmark`); `GUARDED` + `--approved`; `replicate()` pipeline; `evaluate()` (all out-of-control estimates from per-path arrays); `save_paths` / `load_paths` (`paths.npz`); `perpath_hash`; `ROLES` seeds; `Timer`; results hash; `refuse_overwrite` |
| `scripts/run_simulation.sh` | Execution wrapper |
| `scripts/git_provenance.sh` | Read-only worktree classification appended to `provenance.txt` |
| `tests/test_core.py` | 80 tests (as parametrized; 34 Phase 1 + 24 Phase 2 + 7 audit-remediation + 7 report-cell regression tests + 8 final-design tests: equivalence bounds, hand-checked validation, R = 20 streams, provenance classification, failure reporting) |

## Commands

```bash
.venv/bin/python -m pytest -q                 # 134 passed (30 Oct 2026)
.venv/bin/python scripts/spy_figures.py       # derived SPY figures from the frozen SPY run (refuses to overwrite results/derived/spy_figures/)
.venv/bin/python scripts/paper_assets.py      # report tables, figure copies and values.json from frozen results (hash-checked)
(cd report && latexmk -pdf main.tex)          # build the report
scripts/run_simulation.sh smoke               # tiny end-to-end run (~2 s); checks execution, not ARL0 validation
scripts/run_simulation.sh verify              # smoke twice; compares results hashes
scripts/run_simulation.sh pilot               # reduced pilot (~4 s); canonical hash f92f0715… came from the PRE-remediation source (see below)
# NOT AUTHORIZED (each needs explicit user authorization, then --approved):
#   scripts/run_simulation.sh benchmark --approved      (already run once, 14 Oct 2026; do not repeat)
#   scripts/run_simulation.sh production --approved     (run once, 14 Oct 2026; frozen; no rerun authorized)
#   scripts/run_simulation.sh sensitivity_arl100 --approved
# EXECUTED 27 Oct 2026 (spy_20261027T061202_150671); NO FURTHER SPY RUN AUTHORIZED: scripts/run_simulation.sh spy --approved
# Without --approved the wrapper exits 2 before creating a directory; run.py exits before writing anything.
```

**What the wrapper does:**
- Creates `results/runs/<mode>_<YYYYmmddTHHMMSS>_<pid>/`.
- Writes:
  - `provenance.txt` (host, `nproc --all`, memory, Python, read-only `git rev-parse` / `branch --show-current` / dirty flag, thread limits). From 14 Oct 2026 (after the benchmark) it also carries the `scripts/git_provenance.sh` lines:
    - `git_tracked_modified`: staged or unstaged changes to tracked files
    - `git_untracked_tool_state`: `.serena/` only, development-tool state
    - `git_untracked_unclassified`: every other untracked file, listed individually and treated as potentially execution-relevant
    - `git_ignored_python`: ignored `*.py`/`*.pth` outside `.venv/`, which could shadow modules
    - `git_worktree_dirty` keeps its old meaning (any `git status --porcelain` output). Historical provenance files are unchanged; the benchmark's `dirty: yes` came only from untracked `.serena/`
  - `time.txt` and `resources.txt` (wall, CPU, CPU%, peak RSS, exit status)
  - `stdout.log`, `stderr.log`, `exit_status.txt`, `pip_freeze.txt`, `git_status.txt`, `git_diff_stat.txt`, `source_sha256.txt` (SHA-256 of `run.py`, `src/*.py`, `scripts/*.sh` (the wrapper only, before 14 Oct 2026 post-benchmark) and the lock file)
- `run.py` adds `config.json` (written before computing; includes the primary endpoints and the run label), `results.json`, `paths.npz` (per-path T, occupancy and window means; layout in `results.json` → `perpath_axes`; detection, occupancy and empirical masking statistics are reconstructible from it, bootstrap CIs also need the config and bootstrap stream, daily score profiles are not), `tables.md`, `fig_delay.png`, `fig_profile.png` and `fig_replicates.png`.
- It sets `OMP/MKL/OPENBLAS/NUMEXPR_NUM_THREADS=1`; RF parallelism uses `n_jobs` = 16 threads (one controlled level).
- Logs are preserved on failure, and the run's exit status is passed through.

## Seeds and determinism

- Master seed **20261013** for smoke, pilot and the performance benchmark; **20261014** for production and the ARL₀ = 100 sensitivity (user decision, 14 Oct 2026). Each role draws from `np.random.SeedSequence(master, spawn_key=(replicate, role))`, with roles train 0, dev 1, cal 2, val 3, ooc 4, rf 5, boot 6. The RF `random_state` comes from the `rf` stream.
- `results_sha256` hashes `results.json`, excluding timing, environment and start time. Each replicate's `perpath_sha256` (hash of its per-path arrays) is inside it, so `verify` also covers `paths.npz` content.
- Bit-for-bit reproducibility is **demonstrated only on this machine and environment**: `verify` passed, and three identical pilot hashes were produced. Do not claim more.
- **Canonical hash and current code.**
  - `f92f0715…` was produced by **uncommitted** source (HEAD `2a06da8`, dirty).
  - The **Phase 1** remediation (14 Oct, committed in `f77297b`) changed exactly one numerical output relative to the pilot source: `slope_h` now has one normalisation, which multiplies it by (n−1)/n. This was confirmed at smoke scale, where only `slope_h` differed.
  - The **Phase 2** source (committed by the user in `9b286e1`) also changes output schemas, replicate aggregation, paired intervals and reporting. A `pilot` rerun with the current code would therefore differ in more than `slope_h`; the pilot was not rerun, and its original artifacts are preserved.
  - Do not describe the pilot as generated from committed source. Future-run provenance: production-plan.md §Source provenance.
- RF prediction is deterministic across thread counts (fixed tree order; tested). RF fitting is deterministic given `random_state`.
- The `arch` GARCH-t fit is bit-reproducible only with single-threaded BLAS, as the wrapper sets (`OMP/MKL/OPENBLAS=1`). Multi-threaded BLAS changes it at about 10⁻⁵ relative (found 27 Oct 2026). `forecast.fit_garch_vt` is thread-invariant. Run fit-dependent checks under the wrapper's thread settings.

## Artifacts and data

- `results/runs/` is **git-ignored**, so its contents are local only. **Never delete or overwrite** these directories. `run.py` refuses to write into a directory that already holds `config.json`, `results.json`, `tables.md`, figures or verify outputs. The wrapper's provenance and log files are allowed. `setup.sh` regenerates `.gitignore` with `results/runs/`.
- Canonical Phase 1 runs:
  - pilot: `pilot_20261013T075339_142070` (hash `f92f07159b682406…`)
  - earlier identical pilots: `pilot_20261013T075248_140805`, `pilot_20261013T075253_141069`; `pilot_20261013T075123_139095` is before the slope diagnostic was added
  - smoke runs
  - verify: `verify_20261013T075053_138405`
- Production-scale performance benchmark (performance evidence only, excluded from inference; never modify): `benchmark_20261014T041247_106190` (results hash `77e20ffa…`, `results.json` `970ab9ea…`, `paths.npz` `5069c9da…`; committed source `9b286e1`)
- **Frozen production run (primary evidence; never modify, overwrite or regenerate):** `results/runs/production_20261014T060921_145897/`, from clean committed `3529dddf5ea7dcc68d3f279e31e6150dd188d3d7`.
  - `results_sha256` `44410144e3feb4a762dd2044fec07a2ddc64fdc742d43637332cc03f731431b8`; recompute it with `run.results_hash(json.load(...))`
  - file SHA-256s: `results.json` `716862ab41d08c581d2bd65c63979c046a9d9cb5930c111381b3eeb6506b708b`, `paths.npz` `0055f1e115e6cd676d88dcc0875dfee19c44018afc8154658b40be9a2ab8cdf3`, `config.json` `897cf519889a117a7282592b9f7108e74eba4ef0bd047201e37261fba340c130`, `tables.md` `7757c948017b6ee2ef6ed04411534404fe03ea77774ac2de517b8a93ead0dc39`; the rest are in [production-results.md](production-results.md)
  - derived outputs (audit, Holm, repaired figures) go to a **separate directory**, computed from these files
  - bit-for-bit rerun reproducibility of production is **not demonstrated**: it was not rerun, and `verify` shows determinism at smoke scale on this machine only
- `data/raw/` and `data/processed/` are git-ignored and currently empty. A SPY snapshot, once authorized, must be saved once with its metadata and SHA-256. Never re-download silently.
- `results/figures/` and `results/tables/` are git-ignored and intended for the final report outputs.

## Git rules (CLAUDE.md §13)

- **The user alone** stages, commits, pushes, pulls, merges, rebases, resets, tags, releases, and modifies history or config.
- **Allowed for Claude (read-only):** `git status`, `diff`, `diff --check`, `log`, `show`, `ls-files`, `rev-parse`, `branch --show-current`.
- **Never** add Claude, Anthropic or AI co-author, `Co-authored-by` or `Signed-off-by` trailers. Do not create commits under any identity.
- At milestones: summarise the changes, list the files, report tests, suggest a concise commit message, and wait for the user.
