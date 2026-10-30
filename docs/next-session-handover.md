# Next-session handover: START HERE (authoritative)

*Written 30 Oct 2026 at the end-of-session checkpoint, for the session of **31 Oct 2026**. This file is the authoritative starting point for the next session. The detailed record is in [`project-status.md`](project-status.md); the frozen numbers are in [`production-results.md`](../.claude/skills/stc720-project/references/production-results.md).*

**Deadline:** Thu **5 Nov 2026, 23:59 SAST** (ClickUP). **Target submission:** Wed **4 Nov 2026**.

## 1. Verified state at the checkpoint (read-only checks, 30 Oct 2026)

**Git**
- Branch `main`; HEAD `5fcdf6bbd92d6d84e2326d85853315436553bcdb` ("docs: record completed SPY application and update Git exclusions", user commit).
- HEAD equals `origin/main`. The repository is public at https://github.com/stephenjamespienaar/stc720-rf-ewma.

**Uncommitted Stage 1 work (the user commits)**
- Modified:
  - `src/application.py`
  - `tests/test_spy.py`, `tests/test_core.py`
  - `docs/project-status.md`, `docs/references.md`
  - `CLAUDE.md`, `.claude/skills/stc720-project/SKILL.md`, `.claude/skills/stc720-project/references/reproducibility.md`
  - `.gitignore`
- New:
  - `docs/paper_outlines.md`, this file
  - `scripts/spy_figures.py`, `scripts/paper_assets.py`
  - `results/derived/spy_figures/`
  - `report/main.tex`, `report/refs.bib`, `report/tables/`, `report/figures/`, `report/main.pdf`

**Frozen artifacts re-verified at the checkpoint (`sha256sum -c`)**
- Production: 17/17 files match the P1 record.
- SPY: `results.json`, `monitor.csv`, `frozen.json` and both original PNGs match.
- The snapshot `data/raw/SPY.csv` (`7cd6d400…`) matches.
- The derived SPY figures match.

**At this checkpoint** no tests, builds or analyses were run; only documentation was edited.

## 2. Completed and frozen; never rerun or modify

| Work | Record |
|---|---|
| R = 20 production simulation | `results/runs/production_20261014T060921_145897/`; `results_sha256` `44410144e3feb4a762dd2044fec07a2ddc64fdc742d43637332cc03f731431b8`; `results.json` file `716862ab…`. Numbers and caveats: `production-results.md` |
| P1 independent audit | PASS: 1,768/1,768 primary comparisons bit-identical. It covers the downstream calculations only, not the upstream simulation. `docs/p1_audit_report.md` |
| P2 Holm (supplementary, post hoc) | 6/12 rejected (all RF − conventional); RF − GARCH RMD₅₀₀ Holm p = 0.0533. `docs/p2_multiplicity_report.md` |
| P3 figure repair | The repaired `results/derived/p3_figures/fig_replicates.png` (`6e4fbcde…`). `docs/p3_figure_report.md` |
| P4/P5 exploratory diagnostics | Descriptive; no p-values. `docs/p45_diagnostics_report.md` |
| SPY application | `results/runs/spy_20261027T061202_150671/`; `results_sha256` `5725d5e3…`; `results.json` `877b5f09…`, `monitor.csv` `3ba20094…`, `frozen.json` `5a979745…`. Variance-targeted GARCH-t; restricted target E[min(T, 5000)] = 500; 6/6 validations pass. Descriptive only. `docs/spy_vt_remediation.md`, methodology §11 |

**Main conclusions** (λ = 0.1; simulation; do not alter):
1. Conventional EWMA detected the persistent increases fastest. RMD₅₀₀ for conventional / RF / GARCH:

   | δ | Conventional | RF | GARCH |
   |---|---|---|---|
   | 1.5 | 205 | 243 | 249 |
   | 2 | 132 | 192 | 202 |
   | 3 | 63 | 126 | 140 |

2. RF − GARCH: −6.05 / −9.94 / −13.13 days (unadjusted CIs exclude 0). It is not robust to the post hoc Holm adjustment and varies strongly between systems. There is no X(20) difference.
3. The forecast-accuracy ranking is roughly the reverse of the detection ranking. Adaptation masking is *consistent with* this, not shown to be its cause.

## 3. Stage 1, completed 30 Oct 2026 (as reported in that session's Stage 1 report)

**SPY figures**
- Legends and in-panel labels no longer hide data. This was a plotting-only change in `src/application.py`.
- Regenerated from the frozen outputs into `results/derived/spy_figures/`: `fig_spy_charts.png` `0f87a801…`, `fig_spy_variance.png` `7b3b2359…`.
- 35/35 checks; the originals are unchanged.

**Tests**
- 134 passed.
- New legend and label regression test in `tests/test_spy.py`.
- The provenance-test assumption was updated after the user's `.gitignore` change in `5fcdf6b`.

**Report scaffold**
- `report/main.tex` follows the rubric structure, with numbered core equations (1)–(3), a draft AI declaration and the Code Availability statement.
- `report/refs.bib` has 16 Zotero-verified entries.
- `scripts/paper_assets.py` builds the tables, the figure copies and `report/tables/values.json` (208 values for number tracing). 110/110 checks.
- The initial PDF is 8 pages, with no LaTeX warnings and no overfull boxes.

**Zotero**
- Holm (1979), Brook & Evans (1972) and Lucas & Saccucci (1990) were read in full text.
- Francq et al. (2011) was read as a preprint (FT-pre).
- Lee et al. (2020) is at abstract level.
- Evidence levels are in `docs/references.md` v1.1.

**Writing outlines:** `docs/paper_outlines.md`.

## 4. Approved, not yet done: TOMORROW'S FIRST TASK

**Publication-size figure readability correction (plotting only; approved by the user on 30 Oct 2026; not started).**

At final size, figure text prints at about 3.4–5.7 pt, because the PNGs are 10–15 in wide but printed about 5.4–6.3 in wide. The steps:

1. Regenerate the selected simulation figures (from the frozen production `results.json`) and SPY figures (from the frozen SPY `results.json` and `monitor.csv`) at publication dimensions (≈ 6.3 in wide), with labels, ticks and legends at **8–10 pt**.
2. Preserve all numerical data. Never touch the frozen originals; write derived outputs only (new directories under `results/derived/`).
3. Verify numerical equivalence: plotted values must equal the stored values, as in `scripts/p3_figures.py` and `scripts/spy_figures.py`. Inspect the figures at actual printed size.
4. Point `scripts/paper_assets.py` (the source paths and hashes in `FIGS`) and the LaTeX scaffold at the corrected figures, then rebuild and inspect the PDF.
5. Re-verify all original artifact hashes and run `pytest`. Update `project-status.md`.

The figures concerned are `fig_delay`, `fig_profile` and `fig_replicates` (production; plotting code in `src/report.py` and the P3 jitter) and `fig_spy_charts` and `fig_spy_variance` (code in `src/application.py`).

## 5. Then Stage 2: drafting (after the readability task)

**Claude drafts:**
- the literature review within §1;
- §2 Mathematical background;
- §3 Proposed chart and experimental design;
- the §4 results and technical comparisons;
- §5 the SPY illustrative example;
- the tables, captions and bibliography.

**The user writes and substantially revises:**
- the Introduction motivation;
- the interpretive Discussion (inside §4, within its 3 pages);
- §6 Conclusion and recommendations;
- the Abstract.

**Outlines:** `docs/paper_outlines.md`.

**Paper rules (user decisions, 30 Oct 2026)**

*Structure and format*
- LaTeX PDF; the rubric structure exactly: §1 Introduction (with the literature review), §2 Mathematical background (2.1 ±1.5 p, 2.2 ≤ 2 p), §3 Proposed chart (≤ 3 p), §4 Results and discussion (≤ 3 p; 4.1 ≤ 2 p, 4.2 1 p), §5 Illustrative example (±2 p), §6 Conclusion (±½ p), References.
- Abstract of 150–250 words; ≥ 3 keywords; an accurate generative-AI use declaration directly below the keywords.
- Every equation, table and figure numbered; table titles above, figure captions below.
- No code appendix, listings, file maps, file paths or commands in the paper. Only a short Code Availability statement with the public URL above.
- Clarity first: drop secondary figures (replicates, then SPY variance) before shrinking anything.

*Wording and evidence*
- Say **"pre-specified"**, never "pre-registered".
- Keep **simulation RMD₅₀₀** (a restricted detection delay, H = 500) distinct from the **SPY target E[min(T, 5000)] = 500** (a restricted in-control run length).
- Label the evidence tiers: pre-specified primary contrasts; P1-verified downstream calculations; supplementary post hoc Holm; exploratory P4/P5; descriptive SPY.
- SPY alarm counts are never detection accuracy.
- Disclose:
  - the GARCH home advantage;
  - the calibration limitations (validation conditional on h*; overshoot warnings at λ = 0.2);
  - the infinite fourth moment (1.0039), with the limitation from Francq et al. (2011): VTE asymptotic normality needs E ε⁴ < ∞, and their second step is Gaussian QML, not our Student-t;
  - the observational nature of SPY.

## 6. Outstanding corrections before the report is complete (none done yet)

- [ ] Remove `\nocite{*}` from `report/main.tex`.
- [ ] Holm (1979): keep 1979 in `refs.bib` (the Zotero record wrongly shows 2026; the user may correct it).
- [ ] Keep the Francq et al. (2011) limitation for the SPY model.
- [ ] Replace the student-number placeholder.
- [ ] Finalize the AI-use declaration with the student's approval.
- [ ] Check against every rubric requirement, including page budgets and abstract word count.
- [ ] Independent numerical-traceability check of the in-text numbers against `report/tables/values.json` and the frozen files, plus a bibliography check against `docs/references.md`.
- [ ] Decide whether to commit `report/main.pdf`.

## 7. Not authorized

- Any simulation: production rerun, ARL₀ = 100 sensitivity (deferred), benchmark.
- Any SPY run, refit, recalibration or data download.
- Changing results, statistical conclusions or frozen outputs.
- Git staging, commits or pushes (the user only; no AI attribution trailers).

## 8. Schedule

| Day | Work |
|---|---|
| Sat 31 Oct | Figure readability correction (first task) → user review → start Stage 2 (§2, §3); the user starts writing their sections |
| Sun 1 Nov | §1 literature review, §4 results, §5 SPY |
| Mon 2 Nov | Integrate the user's sections; full PDF; page-budget pass |
| Tue 3 Nov | Traceability and bibliography checks; rubric checklist; AI declaration; proofreading |
| Wed 4 Nov | Final approval; Turnitin; **submit** |
| Thu 5 Nov | Buffer only (deadline 23:59) |

## 9. Restart instruction

> Use the stc720-project skill and read `docs/next-session-handover.md` first. Verify the Git state and frozen hashes read-only. Then do the approved publication-size figure readability correction (plotting only, derived outputs) and stop for my review before Stage 2 drafting. No simulations, refits, downloads or Git writes.

*The approved completion plan (30 Oct 2026, with the user's 10 amendments) is summarized in §§4–8 above. Its working copy lives outside the repository at `~/.claude/plans/pasted-content-id-e1e7-stc-wise-brook.md`.*
