# P1: independent audit of the frozen production results

*27 Oct 2026. Audits `results/runs/production_20261014T060921_145897/` (results hash `44410144…`, source `3529ddd`). Audit script: `scripts/audit_p1.py` (SHA-256 `64d86bb8a31df387…`), run on HEAD `fb73ecd`. Outputs: `results/derived/p1_audit/`. No simulation was run, and no frozen file was changed.*

**Verdict: PASS.**
- All 12 primary contrasts and their 4 δ = 1 baselines were recomputed from `paths.npz` with independent code. They agree **bit-for-bit** with `results.json`: 1,768 of 1,768 comparisons are exact.
- 518 integrity, design and invariant checks were run, and none failed.
- The secondary sweep (all stored paired contrasts) found 0 scientific mismatches and 29 floating-point-level differences (≤ 3.6 × 10⁻¹⁵).

## 1. Scope and independence

**Independence.** The script imports only the standard library, NumPy and `scipy.stats`. Its estimators are written from methodology eqs. 17, 23, 24, 27 and 28, not from `run.py`, `src/chart.py` or `src/aggregate.py`.
- The script runs under `python -I`. Its `sys.path[0]` is then `scripts/`, so the project packages cannot be imported.
- At exit the script asserts that no `run`, `src` or `src.*` module is in `sys.modules`. The assertion passed.
- Two provenance encodings were re-implemented from their one-line definitions in `run.py`: the `results_sha256` canonical-JSON rule and the per-replicate `perpath_sha256` byte layout. These are hashing conventions, not estimators.

**Audited quantities**, at λ = 0.1 for the pairs RF − GARCH and RF − conventional:

| Role | Metric | δ |
|---|---|---|
| Primary (12) | paired RMD₅₀₀ and paired X(20) | 1.5, 2, 3 |
| δ = 1 baselines (4) | paired RMD₅₀₀ (2) and paired X(20) (2) | 1 |

**Fields compared.**
- *Per replicate:* mean, SE, n and both 95% CI limits.
- *Aggregate:* mean, min, max, n₊, n₋, s_b, t₁₉ CI limits, RMS Monte Carlo SE, σ̂²_sys, σ̂_sys and the sign-test p.
- *Counts and order:* stored per-replicate n against `aggregate.counts`. The stored `values` list was checked against the 20 per-replicate means, in replicate order.

**Secondary sweep** (not part of the verdict). The same loop ran over every stored paired contrast: 3 pairs × 2 λ × 4 δ × {dH, x₅, x₂₀, x₆₀}.

## 2. Definitions implemented

The audit uses these definitions:

| Quantity | Definition |
|---|---|
| Coding | M = τ − 1 + H = 549 monitored days. T < τ is a pre-change alarm. T = 550 is censored. T = 549 is a detection with D = H |
| Delays | D = T − τ + 1 and D_H = min(D, 500). 1{D ≤ k} excludes censored paths |
| Survivor eligibility | E_k = {T_k ≥ τ}. It must be identical at δ and at δ = 1, otherwise the script raises an error. Paired set: E_a ∩ E_b (boolean intersection) |
| RMD contrast | y_i = D_H,a(δ) − D_H,b(δ) on E_a ∩ E_b |
| X(20) contrast | y_i = [1{D_a(δ) ≤ 20} − 1{D_a(1) ≤ 20}] − [1{D_b(δ) ≤ 20} − 1{D_b(1) ≤ 20}] on E_a ∩ E_b |
| Within-replicate uncertainty | SE = sd(y, ddof = 1)/√n of the **complete matched per-path contrast**, never a combination of chart-level SEs. CI = mean ± 1.96 SE. If n < 2 the SE is not identifiable (None, never 0) |
| Aggregation | Equal weights over R = 20 systems. s_b uses ddof = 1. CI = mean ± t₁₉,₀.₉₇₅ s_b/√20, where t₁₉ = 2.093 (checked). Exact two-sided sign test with zeros excluded; `scipy.stats.binomtest` was cross-checked against an exact `Fraction`/`math.comb` computation |

## 3. Results: primary contrasts and δ = 1 baselines

**Table P1.** Independently recomputed replicate-level estimates (λ = 0.1, R = 20, t₁₉ CIs, **not adjusted for multiplicity**). The stored mean equals the independent mean in every row.

| Contrast | δ | Mean [95% CI] | s_b | RMS MC SE | Signs +/− | Sign p | Paired n | Class |
|---|---|---|---|---|---|---|---|---|
| RF − GARCH, RMD₅₀₀ | 1 (baseline) | +0.274 [−1.242, 1.789] | 3.24 | 2.61 | 9/11 | 0.82 | 1,734–1,793 | EXACT |
| | 1.5 | −6.053 [−10.474, −1.632] | 9.45 | 2.79 | 6/14 | 0.115 | 1,734–1,793 | EXACT |
| | 2 | −9.943 [−17.082, −2.804] | 15.25 | 2.76 | 5/15 | 0.041 | 1,734–1,793 | EXACT |
| | 3 | −13.133 [−22.875, −3.391] | 20.82 | 2.55 | 6/14 | 0.115 | 1,734–1,793 | EXACT |
| RF − GARCH, X(20) | 1 (baseline) | 0 (all 20 exactly 0) | 0 | 0 | 0/0 | – | 1,734–1,793 | EXACT |
| | 1.5 | +0.00089 [−0.00208, 0.00385] | 0.0063 | 0.0046 | 10/10 | 1.00 | 1,734–1,793 | EXACT |
| | 2 | +0.00132 [−0.00271, 0.00535] | 0.0086 | 0.0055 | 12/8 | 0.50 | 1,734–1,793 | EXACT |
| | 3 | −0.00054 [−0.00922, 0.00813] | 0.0185 | 0.0068 | 13/7 | 0.26 | 1,734–1,793 | EXACT |
| RF − conventional, RMD₅₀₀ | 1 (baseline) | −3.801 [−6.532, −1.069] | 5.84 | 4.00 | 5/15 | 0.041 | 1,645–1,717 | EXACT |
| | 1.5 | +37.538 [32.962, 42.115] | 9.78 | 3.98 | 20/0 | 1.9 × 10⁻⁶ | 1,645–1,717 | EXACT |
| | 2 | +60.402 [52.961, 67.843] | 15.90 | 3.62 | 20/0 | 1.9 × 10⁻⁶ | 1,645–1,717 | EXACT |
| | 3 | +63.629 [53.005, 74.252] | 22.70 | 2.92 | 20/0 | 1.9 × 10⁻⁶ | 1,645–1,717 | EXACT |
| RF − conventional, X(20) | 1 (baseline) | 0 (all 20 exactly 0) | 0 | 0 | 0/0 | – | 1,645–1,717 | EXACT |
| | 1.5 | −0.00809 [−0.01100, −0.00518] | 0.0062 | 0.0066 | 1/18 | 7.6 × 10⁻⁵ | 1,645–1,717 | EXACT |
| | 2 | −0.02513 [−0.02905, −0.02122] | 0.0084 | 0.0087 | 0/20 | 1.9 × 10⁻⁶ | 1,645–1,717 | EXACT |
| | 3 | −0.06084 [−0.06931, −0.05236] | 0.0181 | 0.0106 | 0/20 | 1.9 × 10⁻⁶ | 1,645–1,717 | EXACT |

- RMD values are in trading days. A negative RMD contrast means RF detects faster. A positive X(20) contrast means RF has more excess detections within 20 days.
- The two δ = 1 X(20) baselines are 0 on all 20 replicates, with SE 0. As designed, `results.json` does not aggregate them; the script confirms they are absent rather than missing.
- Every primary per-replicate SE was identifiable: n ≥ 1,645 throughout, and 0 values were unidentified.
- Each row compared 112 fields: 20 × 5 per replicate, plus 12 aggregate fields. The X(20) baseline rows compared 100 fields, because they have no stored aggregate.
- These values match the frozen summary in `production-results.md`.

## 4. Integrity and invariant checks (518; all passed)

**Identity.**
- All 17 production files match their recorded SHA-256s, before and after the audit. They were re-checked with `sha256sum -c` after the run.
- The recomputed `results_sha256` = `44410144e3feb4a7…`.
- All 20 recomputed `perpath_sha256` values match. This ties the arrays in `paths.npz` to `results.json`.

**Design and configuration.**
- `config.json["config"]` equals `results.json["config"]`, and its mode and seeds also match.
- Mode `production`, R = 20, master seed 20261014, ARL₀ = 500, τ = 50, H = 500, δ {1.5, 2, 3}, λ {0.1, 0.2}.
- The primary specification is λ = 0.1, the two pairs and {dH, x_20}.
- There are 140 distinct spawn keys: 20 replicates × 7 roles.
- `paths.npz` holds exactly the 80 arrays r0–r19 × {T, occ, uS, uE}. Every T has shape (4, 2, 4, 2000), integer type and range 1–550.

**Survivor eligibility (CRN).** The check covers every replicate × λ × chart (160 cells), including the oracle. The pre-change alarm set {T < τ} is identical across δ ∈ {1, 1.5, 2, 3}, and so are the pre-change alarm days themselves.

**Conventional chart.** T is non-increasing in δ for every path, as expected because u scales by δ after τ.

**Pairing.**
- For every audited contrast, the per-replicate paired n equals the stored `aggregate.counts` entry.
- The stored aggregate `values` list equals the 20 per-replicate means, in order, so no replicate is missing or duplicated.
- The SciPy sign-test p equals the exact p.

**Boundary coding in the real data** (λ = 0.1, summed over 20 × 2,000 paths):
- Pre-change alarms: 5,000 conventional (0.125), 3,746 GARCH (0.094) and 4,061 RF (0.102).
- Over all cells, 432 paths alarm on day 549 (a detection with D = H) and 209,932 are censored (T = 550).
- Censoring among GARCH survivors at δ = 1.5 is 7,769 of 36,254 (21.4%).
- The day-549 case therefore occurs in the data, and the audit codes it as a detection, separately from censoring.

## 5. Differences from stored values

| Scope | EXACT | FP (≤ tol) | MISMATCH | Max \|Δ\| |
|---|---|---|---|---|
| Primary and baselines | 1,768 | 0 | 0 | 0 |
| All paired contrasts (secondary sweep) | 10,507 | 29 | 0 | 3.6 × 10⁻¹⁵ |

- Tolerance: |Δ| ≤ 10⁻¹⁰ + 10⁻¹⁰·|stored|. Integers must match exactly.
- All 29 FP rows are the descriptive σ̂²_sys (17) and σ̂_sys (12) of secondary contrasts.
- The cause is the order of operations. The audit uses mean(w²) directly, while the project squares the stored RMS SE, √mean(w²). The difference is harmless rounding, **not** a scientific discrepancy.
- No primary quantity differs at all.

## 6. Statistical limitations (unchanged by the audit)

- **Multiplicity.** The 12 CIs are not adjusted for multiplicity (methodology §7.4). The Holm adjustment is P2: post hoc and supplementary.
- **Survivor conditioning.** Contrasts are over E_a ∩ E_b, which is conditional on no pre-change alarm by either chart.
- **Unequal pre-change false alarms.** Equal ARL₀ did not give equal pre-change false-alarm rates: 0.125 against 0.094. **The RF − conventional RMD baseline at δ = 1 is itself −3.80 days, and its CI excludes 0.** The δ > 1 RF − conventional RMD contrasts should be read next to this baseline. The X(20) contrasts are baseline-adjusted by construction.
- **Restricted mean.** RMD is a restricted mean, administratively censored at H = 500. It is never ARL₁.
- **Heterogeneity.** RF − GARCH RMD varies across fitted systems much more than Monte Carlo error: s_b is 9.4–20.8 against an RMS MC SE of about 2.6–2.8. The sign tests (p = 0.115 / 0.041 / 0.115) are weaker than the t intervals. P4 investigates this descriptively.
- **Small-R inference.** The t₁₉ intervals assume approximate normality of the replicate estimates. σ̂_sys is a descriptive method-of-moments quantity, truncated at 0 for RF − conventional X(20) at δ = 1.5 and 2.
- **Scope of the evidence.** The results hold for the GARCH(1,1)-t DGP only, and the IC calibration is conditional on each h*.

## 7. What the audit does not verify

- **Upstream simulation.** The audit treats the per-path alarm days in `paths.npz` as given. It verifies everything computed from them. It does not verify the simulation, forecasters, EWMA or calibration that produced them, because that would need re-simulation, which is not authorized. The hashes show only that the stored arrays are the ones `results.json` was computed from.
- **`boot_ci95`.** These secondary check intervals were not reproduced; that would require replicating the project's exact RNG call order.
- **Other quantities.** Masking, occupancy, per-chart levels, quantiles and IC validation are outside P1.
- **Rerun reproducibility.** Bit-for-bit rerun reproducibility of production is still not demonstrated.

## 8. Reproduction

```bash
.venv/bin/python -I scripts/audit_p1.py --selftest   # hand-computed checks only, about 1 s
mv results/derived/p1_audit results/derived/p1_audit.prev   # the script refuses to overwrite
.venv/bin/python -I scripts/audit_p1.py              # self-test, then the audit; exit 0 iff PASS
```

The run took 1.4 s wall time on 27 Oct 2026 (Python 3.14.4, NumPy 2.5.4, SciPy 1.18.1).

**Outputs** in `results/derived/p1_audit/`:
- `audit_summary.json`: verdict, class tallies, Table P1 data and boundary counts (12 KB)
- `audit_log.txt`: console output
- `audit_provenance.txt`: time, HEAD, versions, script hash and input hashes
- `audit_rows.json`: every comparison and check (1.8 MB)

**Self-test.** The self-test uses 8 hand-worked paths in which the two charts have different survivor sets: 6 and 6 survivors, with an intersection of 5. It checks:
- the expected paired RMD (121.0, SE √(528992/20)) and X(20) (−0.4, SE 0.4)
- the δ = 1 RMD (−38.2) and X(20) (0)
- that the paired contrast differs from the difference of per-chart RMDs
- T = 550 coded as censored, T = 549 as a detection, and D = k counted as a hit
- n = 1 giving SE None, and n = 0 giving mean None
- detection of a CRN-pairing violation
- the aggregation, t₃, t₁₉ and sign-test values

Four deliberate mutations were each caught: counting censored paths as detections, union instead of intersection, wrong censoring sentinel, and ddof = 0.

## 9. Remediation

- **No numerical remediation is required.**
- **Documentation only.** `CLAUDE.md` §18 still describes HEAD `3529ddd` with uncommitted post-production docs, but the user has since committed them as `fb73ecd`. It should be updated at the user's request.
