# Development Snapshots Rename Manifest

Created: 2026-05-31
Purpose: working manifest for renaming poorly named development snapshot files after reading them for topic, version, and earliest visible date.

## Naming Rule

Proposed format:

`Topic_Version_Date.ext`

Where:

- `Topic` is a concise human-readable subject inferred from the document title and contents.
- `Version` is the latest SAT version or branch explicitly mentioned in the file, normalized where possible.
- `Date` is the earliest explicit date visible in the file, formatted like `31Aug2025`.
- If no explicit date is visible, use `NoDate` until a better date is found.
- If the version is ambiguous, use the most specific visible label and note uncertainty.
- CSV files should be inspected separately before renaming, because they may be data tables supporting a neighboring text snapshot.

## First-Pass Read Files

| Original | Topic | Version | Earliest visible date | Proposed name | Confidence | Notes |
|---|---|---|---|---|---|---|
| `ASDF.txt` | Current Status Overview | SAT_4D | No explicit date (`[auto-generated]`) | `Current_Status_Overview_SAT4D_NoDate.txt` | High topic / Low date | Active 4D redevelopment snapshot; mentions CoMast v2 and O1.4D/O3.4D/O4.4D baseline. |
| `SD.txt` | Predictions and Retrodictions Concise List | SAT Quantum | 31Aug2025 | `Predictions_Retrodictions_Concise_SATQuantum_31Aug2025.txt` | High | Generated 2025-08-31 America/New_York. |
| `WV.txt` | NotebookLM Question Pack | SAT_4D | No explicit date | `NotebookLM_Question_Pack_SAT4D_NoDate.txt` | High topic / Low date | Prompt pack for mining 45+ summaries and prediction/retrodiction lists. |
| `EF.txt` | Ultra-Hostile Critic-Hardened Overview | SAT 20 | No explicit date | `Ultra_Hostile_Critic_Hardened_Overview_SAT20_NoDate.txt` | High topic / Low date | Stages 0-11 overview; older formal/gauge/cohomology-heavy formulation. |
| `AFD.txt` | Current Summary Working Notes | SAT / SATxy / QMC | 31Aug2025 | `Current_Summary_Working_Notes_SATxy_QMC_31Aug2025.txt` | Medium | Plain-language overview; SATxy/QMC/HoloJesu Activator references. |
| `QWEF.txt` | Current Overview | SAT.4D | Aug2025 | `Current_Overview_SAT4D_Aug2025.txt` | High | Modular O1-O8 + D1-D8 overview; exact day not visible. |
| `AWGR.txt` | Predictions and Retrodictions | Scalar-Angular Theory | Jun2025 | `Predictions_Retrodictions_ScalarAngularTheory_Jun2025.txt` | Medium | Earlier prediction/retrodiction list; may duplicate or be superseded by AWEG/ASDE. |
| `AWEG.txt` | Predictions and Retrodictions | Scalar-Angular Theory | Jun2025 | `Predictions_Retrodictions_ToleranceBound_ScalarAngularTheory_Jun2025.txt` | Medium | Similar to AWGR, but with more explicit tolerances; check for duplicate/supersession before renaming. |
| `SDFA.txt` | Status Overview / Scattering Amplitude Benchmark | SAT | 31Aug2025 | `Scattering_Amplitude_Status_Overview_SAT_31Aug2025.txt` | High | Reports 2-bundle to 2-bundle toy amplitude, UV damping, reconnection rule, Python skeleton. |
| `ASDE.txt` | Predictions and Retrodictions with Tolerances | SAT_4D | No explicit date | `Predictions_Retrodictions_With_Tolerances_SAT4D_NoDate.txt` | High topic / Low date | Class A/B/C prediction framework; post-redevelopment SAT_4D tolerances. |
| `WFEW.txt` | SAT Quantum Framework Full Overview | SAT Quantum | No explicit date | `Quantum_Framework_Full_Overview_SATQuantum_NoDate.txt` | High topic / Low date | Modular O1-O8 and D1-D8 overview with older citation-marker artifacts embedded. |

## Files discovered but not yet read/classified

- `WF32.txt`
- `QWEF.csv`
- `ADFA.txt`
- `QWFE.csv`
- `SDFAD.txt`
- `RGQEF.txt`
- `ASFEF.csv`
- `EFAFQ.csv`
- `G3QGF.txt`
- `WFEWF.txt`
- `QWEFF.txt`
- `AWDSFE.txt`
- `QWFEFE.txt`
- `QWFEFW.txt`
- `QWEFEF.txt`
- `QWWEFW.txt`
- `AWEFEF.txt`
- `QWEFWF.txt`
- `AEFQWFE.txt`
- `WQEFEWF.csv`
- `WQFWEFE.txt`
- `QWQFWEF.txt`
- `WEFEWFF.txt`
- `QWEFWEF.txt`
- `QWEFQWF.csv`
- `WQWDFEW.txt`
- `QWFEFWE.txt`
- Additional files may exist beyond the current search-result truncation.

## Rename Execution Notes

- Do not rename CSVs until paired text context is known.
- Do not rename apparent duplicates until the supersession relationship is clear.
- For files with `NoDate`, perform a second-pass search inside the file for dates, version headers, generated timestamps, commit history, or nearby CSV metadata.
- If renaming through GitHub contents API, preserve original content exactly; prefer a move/rename workflow where possible, or use manifest confirmation before create/delete replacement.
