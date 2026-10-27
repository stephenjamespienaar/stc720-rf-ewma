# Literature, Zotero and citation caveats

The authoritative bibliography, with what may and may not be claimed for each source, is [`docs/references.md`](../../../../docs/references.md). This file records how to access the sources and the literature state as of 13 Oct 2026.

## Zotero setup

- **Zotero Desktop** runs on Windows. Claude Code runs in **Ubuntu WSL2**.
- **MCP server `zotero`** (user scope; `uvx zotero-mcp@latest`, `ZOTERO_LOCAL`) is **read-only**. Its tools are `zotero_search_items`, `zotero_item_metadata` and `zotero_item_fulltext`. It **cannot create items or assign collections**. If the library needs changing, ask the user to add items via Zotero's *Add Item by Identifier*.
- **Collection membership is not exposed by the MCP.** Use the read-only Zotero local API from WSL:
  - `curl -s "http://localhost:23119/api/users/0/collections?limit=100"`
  - `curl -s "http://localhost:23119/api/users/0/collections/K7HN6JFW/items/top?format=json"`

  Only GET requests are used; this never writes.
- PDFs live at `C:\Users\steph\Zotero\storage\<attachmentKey>\`, which is `/mnt/c/Users/steph/Zotero/storage/...` from WSL.
- **Scanned PDFs have no text layer**, so `zotero_item_fulltext` returns 404. Read them page by page with the Read tool (it renders pages as images). tesseract is not installed.
- Equations are often garbled by PDF text extraction. Mark any reconstructed equation as a reconstruction.

## Collection `STC-720-lib` (key K7HN6JFW): 10 items, no duplicates (checked 13 Oct 2026)

| # | Reference | Zotero key | Evidence status |
|---|---|---|---|
| 1 | Roberts (1959), *Technometrics* 1(3):239–250 | S3A6LVHU | Full text. The PDF is the **2000 reprint** (42(1):97–101); equations reconstructed |
| 2 | Alwan & Roberts (1988), *JBES* 6(1):87–95 | M7G7QD2C | Full text |
| 3 | Bollerslev (1986), *J. Econometrics* 31(3):307–327 | 79MXQ32R | Full text; some equations garbled |
| 4 | Breiman (2001), *Machine Learning* 45(1):5–32 | 8IBZX7F6 | Full text |
| 5 | Dumičić & Žmuk (2015), *Bus. Syst. Res.* 6(1):22–35 | 5VI85G6N | Full text; a cautionary precedent (charts applied to price levels) |
| 6 | Schipper & Schmid (2001), *Nonlinear Analysis TMA* 47(3):2049–2060, doi:10.1016/S0362-546X(01)00332-7 | FIXUEAWI | **Full text from page images** (scanned PDF read visually). Our fault model is their eq. 3; our GARCH–EWMA is their residual chart (§3.5). Their setting: ARL₀ = 60, τ = 1, known parameters, normal innovations; residual chart with λ = 0.1 best "in nearly all cases" |
| 7 | MacGregor & Harris (1993), *JQT* 25(2):106–118, doi:10.1080/00224065.1993.11979433 | FR3PG7SM | **Metadata only** (no PDF; not obtainable via UP). Cite at title level only |
| 8 | Patton (2011), *J. Econometrics* 160(1):246–256, doi:10.1016/j.jeconom.2010.03.034 | X6MRG2UH | Full text: QLIKE and MSE are robust losses |
| 9 | Christensen, Siggaard & Veliyev (2023), *JFEC* 21(5):1680–1727, doi:10.1093/jjfinec/nbac020 | SA4UZ9NE | Full text of the **arXiv preprint** (2601.13014v1), not the typeset journal article. Target is realized variance, not r² |
| 10 | Lu & Reynolds (1999), *JQT* 31(2):166–188, doi:10.1080/00224065.1999.11979913 | AYZH39D9 | **Metadata only** (no PDF; not obtainable via UP). Cite at title level only |

**Rules for citing:**
- Items 7 and 10: no equations, results, ARL values or methodological conclusions may be attributed to them. This holds unless the user later obtains the PDFs; if so, read them and update `docs/references.md`.
- Item 9: check page-specific quotes against the published version.

## Literature discussed but not in the collection

| Reference | Status |
|---|---|
| Schipper & Schmid (2001), *Sequential Analysis* 20(4):235–262, doi:10.1081/SQA-100107647 | Crossref metadata verified; not added; content not read |
| Andreou & Ghysels (2006), *J. Econometrics* 135(1–2):77–124, doi:10.1016/j.jeconom.2005.07.023 | Crossref metadata and abstract summary only; not added |
| Corsi (2009), *JFEC* 7(2):174–196, doi:10.1093/jjfinec/nbp001 (HAR) | Crossref metadata only; not added. The HAR structure is cited via Christensen et al. |
| Jensen, Jones-Farmer, Champ & Woodall (2006), *JQT* 38(4):349–364, doi:10.1080/00224065.2006.11918623 | Crossref metadata only; not added |
| Lucas & Saccucci (1990), *Technometrics* 32(1):1–12, doi:10.1080/00401706.1990.10484583 | Crossref metadata only; not added |
| Crowder & Hamilton (1992), *JQT* 24(1):12–21, doi:10.1080/00224065.1992.11979369 | Crossref metadata only; not added |
| Lazariv, Schmid & Zabolotska (2012), arXiv:1209.4678 | Abstract level only |
| Montgomery & Mastrangelo (1991), *JQT* 23(3):179–193 | In the wider library (JJZE5AS3), outside the collection, no PDF |
| Mukhtiar, Zaman & Butt (2025), *EAAI* 157:111227; Abossedgh, Yeganeh & Johannssen (2026), *Appl. Soft Comput.* 188:114382 | In the wider library with PDFs; possible ML–SPC citations for the Introduction; not reviewed in detail |
| **Lee, Park & Baek (2020)** | Named by the user in the session-closing prompt as discussed. **No discussion of it appears in this session's record, and it is not in the Zotero library** (a search for "Baek" only matched a different citation inside the Abossedgh PDF). **No bibliographic details are verified.** Ask the user for the full reference before using it |

## Rubric requirements relevant to literature

- Read at least 3 articles. Citations and references count for 5 + 5 + 5 marks.
- The Introduction (about 1 page) must include a literature review of SPC and/or ML.
- Similarity must stay ≤ 20%, and AI use must be declared.

## Variance-targeting references (27 Oct 2026; not in Zotero; bibliographic only)

- Francq, C., Horváth, L., & Zakoïan, J.-M. (2011). Merits and drawbacks of variance targeting in GARCH models. *Journal of Financial Econometrics*, 9(4), 619–656. https://doi.org/10.1093/jjfinec/nbr004. The main reference for variance targeting (SPY model B).
- Engle, R. F., & Mezrich, J. (1996). GARCH for groups. *Risk*, 9(8), 36–40. The conventional attribution only.
- Both bibliographic records were verified by the student. **Full texts have not been reviewed**, and neither is in Zotero: cite at title level only (`docs/references.md` [11], [12]).
