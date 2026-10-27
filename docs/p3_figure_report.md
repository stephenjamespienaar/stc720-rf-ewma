# P3: repair of the production replicate figure

*27 Oct 2026. Source: the frozen `results/runs/production_20261014T060921_145897/results.json`, with file SHA-256 `716862ab…` and results hash `44410144…`. The change is to plotting code only. No simulation was run, and no estimate was recomputed. The original figures are untouched.*

**Verdict: PASS.**
- 41/41 figure checks passed.
- 85 tests passed.
- All 17 production files are unchanged.

## Root cause

The replicate offsets in `src/report.py` `figures()` were a fixed 0.03 · (r − (R − 1)/2), against fixed x limits of [0.75, 3.25].
- At R = 20 the offsets span ±0.285, so replicates 0 and 1 were drawn at x = 0.715 and 0.745 (δ = 1), and replicates 18 and 19 at 3.255 and 3.285 (δ = 3). All four lie outside the axes.
- **Data was hidden.** The most extreme RF − conventional δ = 1 value, −16.58 (replicate 0), was one of the hidden points.
- **A second defect.** The δ = 1.5 and δ = 2 clouds overlapped between x = 1.715 and 1.785, so in that range a point could not be assigned to its δ.

## Change (plotting only)

- **New `report.jitter(xs, R)`.** The offsets are 0.6 · gap · (r/(R − 1) − ½), where gap is the smallest spacing between the δ values (0.5). They are 0 when R = 1.
- **New x limits.** `figures()` uses these offsets, and its x limits are [x₀ − gap/2, x_last + gap/2], which is still [0.75, 3.25] here.
- **Effect.** For any R, every point stays within ±0.15 of its own δ, inside the axes, and apart from the neighbouring clouds.
- **Unchanged.** Values, labels, titles, method and panel ordering, mean markers and error bars are unchanged. Simulation, calibration, estimator and aggregation code are untouched.
- **Regression test.** `test_replicate_jitter_stays_inside_axis_and_own_shift`, run at R ∈ {1, 2, 10, 20, 50}. The old formula fails all three of its assertions.

## Verification

Regeneration script: `scripts/p3_figures.py`. It writes to `results/derived/p3_figures/`, and `p3_summary.json` lists every check. For each of the 4 panels it confirms:
- titles and labels
- 20 replicate series
- every plotted replicate value exactly equal to the stored per-replicate mean
- x = δ plus that replicate's offset
- every point inside the axis limits
- the clouds of neighbouring δ disjoint
- the mean markers equal to the stored aggregate means
- the error bars equal to the stored t₁₉ CIs, to within 10⁻¹²

Across the whole figure it also confirms the legend is present, all 280 replicate points are drawn (20 × (4 + 3) × 2 pairs), and the original figures are unchanged.

| Figure | Original (`results/runs/…/`) | Regenerated (`results/derived/p3_figures/`) |
|---|---|---|
| `fig_replicates.png` | `1af6a11058e6e014397befbbff7a0d6c060f96a277a64293aaeda8456225aecb` (defective) | `6e4fbcde288886ebc271bdf4bc54ee8284618e0bc6d24cb91c86bb5a16893e30` (repaired) |
| `fig_delay.png` | `e3ff5f011f9d7a21…` | identical |
| `fig_profile.png` | `a409411c285eab91…` | identical |

- **Rendering is unchanged.** The bit-identical `fig_delay` and `fig_profile` show that the plotting environment reproduces exactly, and that only the replicate figure changed.
- **Visual inspection at 1500 × 1140 px:**
  - four separate clusters per panel
  - no clipped points
  - the legend does not collide with any data
  - the x and y limits contain all data
- **The empty δ = 1 column in the X(20) panels is by design:** X(20) is 0 there by construction.

**Presentation note for the article** (not changed, because the figure labels were to be preserved): the panel titles use internal names ("rf - garch") and the y label reads "RMD_H". For the final report you may want to relabel them, for example "RF − GARCH" and "RMD₅₀₀ (days)".

Reproduce:

```bash
.venv/bin/python scripts/p3_figures.py   # refuses to overwrite an existing results/derived/p3_figures
```
