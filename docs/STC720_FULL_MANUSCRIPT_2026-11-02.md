# STC 720 — Complete Research Manuscript: Authorised Execution Contract

**Date:** 2 November 2026 (South African Standard Time)  
**Repository:** `/home/stephen/projects/stc720-rf-ewma`  
**Deliverable today:** A complete, compiled, scientifically checked STC 720 article in `report/main.tex` and `report/main.pdf`, ready for the student's substantive review.  
**Official deadline:** 5 November 2026, 23:59 SAST.  
**GitHub code repository:** https://github.com/stephenjamespienaar/stc720-rf-ewma

> **EXECUTION AUTHORISATION.** The student has expressly replaced the former *mixed drafting / student-written sections* arrangement. You are authorised to draft **every section** of the paper (including Abstract, Introduction, Discussion, Conclusion, and the AI-use declaration), revise the existing LaTeX scaffold, repair publication-size figures using frozen outputs, compile and inspect the PDF, and verify the manuscript. The student will subsequently **critically read, revise, and approve** the entire draft. You are **not** authorised to submit, run scientific experiments, refit, recalibrate, download new data, stage, commit, push, or publish the report. This is an **implementation task, not another planning task**. Do not stop after a plan, an outline, an initial section, or a partial PDF.

## A. Authority, context, and starting files

1. Enter `/home/stephen/projects/stc720-rf-ewma`; load the `.claude/skills/stc720-project/SKILL.md` project skill. Inspect actual Git branch, HEAD, worktree, origin, and pending edits read-only. **Do not reset, clean, stash, discard, or overwrite user work**. If Stage 1 files are uncommitted, work on top of them carefully.
2. Read, in order of relevance: `docs/STC720_assignment_rubric.pdf`, `CLAUDE.md`, `docs/project-status.md`, `docs/next-session-handover.md`, `docs/paper_outlines.md`, `docs/methodology.md`, `docs/references.md`, `docs/research_plan.md`, project skill scientific-design/production-results/reproducibility/research-literature references, `docs/p1_audit_report.md`, `docs/p2_multiplicity_report.md`, `docs/p3_figure_report.md`, `docs/p45_diagnostics_report.md`, `docs/spy_vt_remediation.md`, and any SPY completion checks. Check the available Zotero `STC-720-lib` sources and cite at their verified evidence level.
3. **The authoritative starting paper is the EXISTING `report/main.tex`, not a new document.** Examine `report/main.pdf`, `report/refs.bib`, `report/tables/`, `report/figures/`, `scripts/paper_assets.py`, `scripts/spy_figures.py`, and their provenance. Existing equations, figure assets, and table bodies are a valuable verified scaffold. Preserve their factual content and traceability; edit for scientific clarity and layout only. Do not hand-edit machine-generated table entries.
4. Inspect the student's **previous completed OC-SVM–CAE–MEWMA report** (`main.tex` and `main.pdf`) read-only, discovering its actual location beneath `/home/stephen/projects/one-class-cae-svm-mewma/` or another accessible original thesis directory. It is a **style exemplar**: restrained academic prose; mathematically defined notation; paragraph-level synthesis; reasoned interpretations, figure/table captions, and cohesive transitions. **It is not a scientific source for STC 720.** Do not copy passages, equations, graphs, front matter, supervisor/ethics declarations, acknowledgements, or the 28-page thesis structure. In particular, do **not** blindly adopt its double spacing or thesis title pages if these make the short STC 720 article violate the rubric. If the previous report cannot be accessed, continue using the supplied current scaffold and established writing conventions; note the limitation at the end rather than stopping.
5. Resolve conflicts in this order: (i) actual STC 720 rubric and academic integrity requirements; (ii) frozen verified evidence and methodology; (iii) explicit student decisions in this contract; (iv) latest project notes; (v) prior thesis as visual/style reference only. A prior note saying the student must write Abstract/Introduction/Discussion/Conclusion is **superseded by this authorisation**. Do not alter the experimental design to improve the story.

## B. Exactly what must be delivered

Write the **entire manuscript**, not just an introduction to the verified tables:

- Academic title, abstract **150–250 words**, and at least **3 keywords**.
- Accurate **Generative AI use declaration immediately below keywords**.
- **1 Introduction:** approximately one page; motivation, dependence/volatility-monitoring problem, relevant SPC and ML literature synthesis, research gap, precise objectives, contribution, and map of the paper if space permits. The literature review belongs **inside the Introduction**, not a separate main section.
- **2 Mathematical background:** at most **3.5 pages**, with **2.1 Existing charts** (approximately 1.5 pages: EWMA, normalized squared returns, GARCH-t and run lengths) and **2.2 Machine learning** (at most 2 pages: RF conditional-variance regression, lagged squared-return features, chronology, QLIKE and positivity/forecasting constraints). Explain rather than merely listing formulas.
- **3 Proposed monitoring chart:** at most **3 pages**. Precisely specify all three comparison schemes, frozen estimators, the common monitoring score and EWMA state, control limit calibration, independent IC validation, stochastic design, change convention, primary metrics and paired analysis. Avoid needless implementation details.
- **4 Results and discussion:** at most **3 pages** total, containing **4.1 Performance of proposed RF–EWMA** (at most 2 pages), **4.2 Performance comparison** (about 1 page), and the interpretation **within section 4**, not a new main section. The **12 pre-specified contrasts**, their uncertainty, and the forecast-accuracy/detection contrast are essential.
- **5 Illustrative example:** approximately **2 pages**; SPY ETF (not falsely described as the S&P 500 index itself), training/monitoring periods, frozen modelling, variance-targeted GARCH-t calibration, validation, alarm states/episodes, interpretation and limitations.
- **6 Conclusion and recommendations:** approximately **half a page**, answering the research question without exaggerating RF superiority, with limitations and proportionate recommendations.
- **References**, containing only relevant cited literature.
- A short **Code availability** statement with this *already verified public URL*: `https://github.com/stephenjamespienaar/stc720-rf-ewma`.

**No code appendix, code snippets, source-file maps, commands, hashes, paths, or Git workflow prose in the academic manuscript.** These technical trace details belong in repository records, not the paper. The student has already chosen this presentation and accepted the rubric interpretation risk. Do not resurrect that debate. Do not add the previous thesis's title pages, table of contents, list of figures, signature sheets, acknowledgements, or ethics wording.

## C. Scientific source of truth and constraints

Read the frozen data and existing verified reports; do **not** substitute recollection or guesses for actual stored quantities.

### Primary simulation

- Frozen run: `results/runs/production_20261014T060921_145897/`; production `results_sha256` = `44410144e3feb4a762dd2044fec07a2ddc64fdc742d43637332cc03f731431b8`. The **17 archived production files** must not change. R = **20** independently trained/fitted systems; 160/160 independent IC validation configurations passed the **practical interval-within-[425,575] rule**, not an assertion that each CI contained exactly 500.
- Methods: conventional EWMA on `r_t² / s_train²`; GARCH–EWMA using causal one-step-ahead GARCH-t variance predictions; RF–EWMA using causally formed frozen RF variance predictions from lagged squared returns. Common score and recursion:

  \[
  u_t=\frac{r_t^2}{d_t},\qquad Z_t=\lambda u_t+(1-\lambda)Z_{t-1},\quad Z_0=1;\qquad \text{signal iff }Z_t>h^*.
  \]

- Simulation design: standardized Student-t GARCH(1,1) innovations and stationary conditional variance as frozen; R = 20; primary `lambda=0.1`, nominal `ARL_0=500`; shifts `delta=1.5,2,3` with `delta=1` no-change context; change at `tau=50`; `H=500` for the *restricted mean detection delay* `RMD_500`; paired **baseline-adjusted** excess detection `X(20)`; consistent within-replicate common random numbers; independent training/development/calibration/validation/evaluation roles. Cite the full specification in `docs/methodology.md`, not assumptions inferred from a chart.
- Primary **12 pre-specified** paired RF–GARCH and RF–conventional contrasts, at `lambda=0.1`: `RMD_500` and `X(20)` each across three shifted `delta` values. The **unadjusted** estimates and 95% `t_19` CIs are primary; label the Holm step-down p-values *supplementary, post hoc*, not part of the original inferential design. `P1` checked downstream calculations, not a complete independent re-execution of the upstream simulation. `P4/P5` are exploratory and descriptive, not causal evidence.
- Central empirical pattern, to be supported with exact stored numbers: conventional EWMA generally has **shorter detection delays** than RF–EWMA, despite worse variance forecasting QLIKE; GARCH has the most accurate variance forecasts under the simulation's known conditional-variance benchmark, but generally **longer detection delays**. RF falls between conventional and GARCH on the studied persistent changes. RF–GARCH RMD gaps have unadjusted intervals excluding zero but **none** survives 12-test Holm adjustment (the relevant adjusted p approximately **0.05327**). All **six** Holm rejections involve RF–conventional; do not call RF superior to conventional. Evidence is consistent with *forecast adaptation masking the change*, not proof of mechanism.
- The known-parameter oracle is an **internal diagnostic**, not a fourth competing deployable chart. QLIKE in the simulation is evaluated against the *true* conditional variance; in SPY against the noisy squared-return proxy; do not equate their numerical values as like-for-like accuracy metrics.
- `delta=1` is a no-change contextual baseline, not one of the 12 post-change primary contrasts. Equal design ARL does **not** imply equal early false-alarm probabilities `P(T<tau)`. Be precise about truncation/censoring in all run-length language. Do not treat `RMD_500` as unrestricted `ARL_1`.

### SPY illustrative application

- Frozen completed run: `results/runs/spy_20261027T061202_150671/`; results-hash prefix `5725d5e3`. Frozen local snapshot `data/raw/SPY.csv` (checksum prefix `7cd6d400`), original stopped SPY run, `results.json`, `monitor.csv`, `frozen.json` and original figures must not change. **Never re-download** Yahoo-adjusted SPY data or change the training cutoffs.
- Daily adjusted-price percent log returns; **3,507** training returns during **1993-02-01 to 2006-12-29**, **4,967** monitored returns during **2007-01-03 to 2026-09-30**. Training-only chronology and frozen RF hyperparameter selection. Use the actual results for exact values.
- The **unrestricted initial GARCH fit failed the strict fourth-moment gate**. A variance-targeted GARCH(1,1)-Student-t specification was adopted *after that stop* on training-only grounds and used for both GARCH chart and calibration law. It has `alpha+beta≈0.9955<1` (finite unconditional variance), but a fourth-moment coefficient `≈1.0039>1` (infinite fourth moment of returns). Asymptotic normality theory from Francq et al. is **not automatically applicable** to this specific fitted Student-t estimator; distinguish literature context from a proof.
- Finite-variance-only simulation was a **narrow SPY opt-in**; all original strict simulation defaults remain intact. The nominal **SPY target** is the *restricted in-control mean run length* `E[min(T,5000)]=500` under the **fitted** GARCH-t simulation law, **not** unrestricted `E[T]` nor the simulation's `RMD_500`.
- Six out of six chart-by-`lambda` configurations passed the approved independent validation **interval-contained-in-[425,575]** adequacy criterion; the independent validation CI does **not** necessarily contain 500, and validation is conditional on fitted control limit. Two minor overshoot warnings at `lambda=0.2` were recorded, not tuned away. Model-based calibration may favor GARCH.
- At `lambda=0.1`, descriptive monitoring results: conventional **638** exceedance days / **44** episodes; GARCH **143** / **20**; RF **216** / **27**, across 4,967 monitored dates. At `lambda=0.2`, conventional **391/58**, GARCH **77/19**, RF **135/23**. These are **alarm states under a frozen historical reference**, not known true changes, not empirical detection accuracies, and **not** a fair method ranking simply by count.
- SPY RF forecasts were bounded by the range of leaf-averaged training targets and therefore did not extrapolate to the largest 2008/2020 volatility spikes; that suggests a plausible difference from GARCH adaptive response, but do not claim causal identification. Pre-specified market reference dates were selected prior to inspecting monitoring outputs, although the events themselves were selected retrospectively with historical knowledge. Yahoo adjusted prices are retrospectively revised. Disclose the frozen training baseline's long span and the strong persistence.

## D. Literature: exact evidence tiers, no fabrication

1. Verify `report/refs.bib` metadata against `docs/references.md` and available Zotero material; remove `\nocite{*}`. Verify correct `1979` date for Holm in the manuscript; the Zotero record may incorrectly say 2026. Do not silently modify the user's Zotero collection.
2. Use Roberts (1959), Lucas & Saccucci (1990), Bollerslev (1986), Breiman (2001), Patton (2011), Holm (1979), Brook & Evans (1972), Francq/Horváth/Zakoïan (2011) and other directly relevant verified sources as warranted by claims. Brook–Evans is a *CUSUM/Markov-chain run-length foundation*, not automatically direct validation of a specific GARCH oracle implementation. A bibliographic-only paper must not support asserted empirical findings or quotations from its unread text.
3. Use a consistent professional citation convention; the current scaffold uses `natbib` author-year style. Do not change it merely to imitate the old thesis's numbered citations. Place citations at the claims they support; avoid uncited literature summaries or uncited technical assertions that need sourcing.
4. Explain what this specific design adds **within the literature reviewed**; never claim categorical global novelty without evidence.

## E. Formatting and figure/table implementation

1. **First implement the already-approved publication-size readability pass** using frozen results only. Several Stage 1 figures were rendered 10–15 inches wide but embedded around 6 inches; target ~8–10 pt readable tick/legend/axis text at their actual final dimensions. Improve axis labels, legend placement and caption clarity without changing data. Use separate derived outputs; do not overwrite original frozen figures. Verify source hashes, traces, numeric equivalence and printed-size legibility, then cite derived figure paths inside LaTeX source only. If figure verification genuinely blocks you, use a readable verified existing version and explicitly flag it rather than abandoning the full draft.
2. Keep the **priority figures**: (i) simulation detection delay versus `delta`, (ii) masking score profiles *if readable and helpful*, (iii) SPY monitoring; use the replicate-contrast figure and SPY variance plot only if page budget supports them. The two main tables are (i) simulation performances and (ii) 12 pre-specified primary contrasts. Include SPY calibration/monitoring tables in legible condensed form, perhaps splitting or selectively summarizing. Never sacrifice primary contrast uncertainty to include an exploratory picture.
3. Maintain the generated table pipeline; verify its output against frozen results. If a verified number is wrong or contradictory, **flag the discrepancy and fix it only using authoritative frozen evidence**, describing exactly what changed. Do not hand-invent or silently substitute values.
4. **Prevent floating figures and tables from drifting past their scientific sections or into References**. Use sensible float placement/barriers (`placeins`, selective nonfloating material, figure selection), not brute-force blank pages. Visual inspection must check every page of the rendered PDF. Caption table titles **above** tables, figure titles/captions **below** figures; all equations numbered as required by the rubric. Ensure no overfull boxes, clipped text, oversized whitespace, or a multi-page table that violates the section allocation.
5. The previous thesis was 10pt and double spaced; **do not adopt its spacing blindly**. Use the current compact article aesthetic, adjusting only to support readable, rubric-compliant content. Do not shrink body type or figure labels unreasonably to force the page count.

## F. AI use, author responsibility, and identity details

- Provide an accurate declaration **immediately below keywords**, explicitly covering the role of both **Anthropic Claude/Claude Code and OpenAI ChatGPT** in discussions of design, implementation, testing, audits, source review, figures/tables, and **drafting the complete manuscript**. Do not copy the earlier thesis's narrower disclosure. Do not claim the student has *already* verified/approved this completed draft; use accurate forward-looking wording where necessary, for author review.
- Student number: if not evidenced in the project or available verified records, leave one **clearly visible personal-detail placeholder only**, and call it out in completion report. **Do not invent identifiers**. Use the actual author details already approved in the project.
- Do not write for or claim to bypass Turnitin/AI detectors, or imply AI writing is 'human only'. Report and cite responsibly. Avoid plagiarism, and do not copy prose from the student's prior thesis or other sources.
- The **research report PDF is a local deliverable**; do **not** upload or publish it to the public GitHub repository. Source-control decisions remain with the student.

## G. Execution sequence — finish today, without per-section approval gates

1. **Preflight (brief, read-only):** confirm rubric, source files, reported frozen hashes, Git state, figure/table assets, and authorisation. If full checks are long, do those after writing; do not spend the session replanning.
2. **Figure readiness:** perform and test the approved publication-size changes; retain immutable originals; update only derived/report assets. Avoid unnecessary re-rendering of unused secondary figures.
3. **Write the COMPLETE manuscript in `report/main.tex`**, section by section (including abstract and conclusion), using project evidence and citation checks. Draft in polished, concise academic prose with transparent negative findings. Make the scientific story coherent and intelligible to a statistics examiner. **No `[Stage 2]`, `[student-written]`, `[DRAFT]`, `\todo`, or other content placeholders in finished prose**, except the explicitly reported student-number uncertainty if not verified. Remove `\nocite{*}`.
4. **Compile early and repeatedly:** from `report/`, `latexmk -pdf main.tex` or the repository's approved build command. Fix package, citation and float issues. Do not overwrite evidence outside report/ or its own approved derived assets.
5. **Render/inspect every page**, not just LaTeX warnings. Measure actual section page occupancy against the rubric. Cut repetition and lower-priority figures before weakening scientific results or making the text unreadable. Confirm abstract word count, keywords, AI declaration location, numbering, captions, bibliography, Code Availability URL, and conclusions.
6. **Verify numerical claims** with authoritative frozen results, the preexisting 110 table checks, new/old figure provenance, and focused independent recomputations. Run `.venv/bin/python -m pytest -q`, report the *actual* count (Stage 1 had 134, not a guarantee for today), check `git diff --check`, source and artifact hashes, and absence of prohibited modifications. If one check fails, diagnose it; never silently ignore the failure.
7. Update `docs/project-status.md`, `CLAUDE.md` and the project skill only as needed to reflect the complete first draft **pending author review**. Do not mark final academic approval/submission done. Do not stage, commit, push or submit.

**Time priority:** A complete accurate first manuscript is more important than cosmetic polish of optional figures or extensive supplementary diagnostics. Do not spend the entire session implementing plot infrastructure, another plan, or unrelated methodological improvements. If a minor nonessential problem remains, document it and still deliver the best available **complete manuscript today**. Never fabricate a source or numerical result to fill a gap.

## H. Final deliverables and stopping condition

Provide the paths and status of:

1. `report/main.tex` — fully written, editable manuscript.
2. `report/main.pdf` — compiled complete manuscript (state actual page count).
3. Report figures and generated tables, with provenance of any plotting-only adjustments.
4. Per-section **rubric compliance table**, with actual page locations and violations remaining.
5. Abstract word count, keyword count, AI declaration status and personal-detail placeholders.
6. Verified figure/table/citation/LaTeX checks and **actual** automated-test results, with complete failures/warnings (not expected counts).
7. Key **frozen evidence trace** for the main numbers and claims, kept outside the paper.
8. Files changed/created; Git status; confirmation that the 17 production files, SPY snapshot and frozen runs were unchanged.
9. Top author-review priorities: methods/estimands, contrast interpretation and multiplicity, SPY caveats, references, student ID and final declaration.

**Stop after delivering the COMPLETE compiled research draft for student scientific review. No further scientific experiments, submission or Git writes.**

**Required final line:** `STC 720 COMPLETE MANUSCRIPT DRAFT — READY FOR AUTHOR REVIEW`
