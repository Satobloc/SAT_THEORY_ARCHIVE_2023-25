# XW-016 — ℓ_f symbol collision and pre-O9 scale lineage

## Scope
Bounded provenance waypoint for the live finite-core discrimination program. This run follows XW-015 and asks whether the SAT.O9 assignment `ℓ_f = ℓ_P` as **wavefront thickness** was Nathan's prior construction, a generated closure, or inherited from earlier SAT.O notation. No historical numerical scale is promoted into the current forward build.

## Checkpoint consumed
`.[⚙️_AI_FILES]/LLM_WORKSPACES/Argus/XW-015_PLANCK_THICK_WAVEFRONT_ANCESTOR.md`

XW-015 recovered `EARLY LOGGED/2025-10-24_00 SAT O.txt`, where SAT.O9 defines `ℓ_f = ℓ_P` as wavefront thickness, but left the antecedent reason for that assignment unresolved.

## Lightweight repository change check
- `Satobloc/SAT_THEORY_ARCHIVE_2023-25`: no new substantive human construction source after XW-015; newest commit before this waypoint is archive-admin maintenance following XW-015.
- `Satobloc/HsH`: newest sampled changes remain conversation-viewer/date-index maintenance, latest 2026-09-11 06:15 UTC.
- `Satobloc/HSH_RESOURCES`: newest substantive sampled change remains `Refresh extracted corpus and bibliography intake` (`ddbce31...`, 2026-09-11 06:07:59 UTC).

## Source family advanced
Primary source:
`SAT-O Theory Work/SAT_PHASE_VIII_GAUGE_BUILDOUT.txt`

Internal document date: `2025-06-18`.
Repository ingest/commit history: first present in commit `d3f5fa0...` (`SAT-O Detailed Buildouts`, 2025-10-27T01:15:21Z). Therefore June 18 is an internal chronology claim, not a GitHub publication date.

The document defines:

`g_G^{-2}(x) ~ ρ_G(x) · ℓ_f²`

and explicitly glosses:

`ℓ_f: Filament correlation length (Planck-scale unit)`.

This is materially earlier in the internal SAT.O genealogy than O9 and gives `ℓ_f` a **filament/correlation-scale** meaning, not a time-wavefront-thickness meaning.

Secondary source:
`2025-8-24 STATUS OVERVIEW.txt`

The file content itself is headed `SAT STATUS OVERVIEW — 2025-08-31`, creating a filename/content date conflict that must be preserved. It defines:

`w(e) = exp[-T ℓ_f²] × α_top(x_e)`

with

`ℓ_f` = `the loop/segment length scale implicated by the reconnection`.

It later glosses `ℓ_f` as `filament/loop length scale entering reconnection cost`.

Thus, before O9, at least two source families use `ℓ_f` for a carrier/correlation/segment scale.

## Finite-core fact / conflict recovered
XW-015's O9 notation is now source-securely identified as a **semantic collision / repurposing**:

- 2025-06-18 internal SAT.O Phase VIII: `ℓ_f` = filament correlation length, Planck-scale unit;
- 2025-08/31 status overview: `ℓ_f` = filament/loop or reconnection segment length scale;
- 2025-10-24 SAT.O9: `ℓ_f = ℓ_P` = wavefront thickness.

Therefore the symbol identity `ℓ_f` does **not** establish object identity across these documents.

Do not infer:

`filament correlation length = reconnection segment length = wavefront thickness`

without an explicit bridging source.

## Representation / object type
Earlier `ℓ_f` uses belong to carrier/topological geometry:
- filament correlation scale;
- loop/segment scale at reconnection.

O9's `ℓ_f` belongs to the resolver/interface geometry:
- finite thickness of the time-wavefront.

This is directly relevant to the present architecture discrimination because it prevents a notation-only collapse of **core/material scale** and **resolving-interface thickness**.

## Independently useful equations / limiting maps
Historical equations only:

`g_G^{-2}(x) ~ ρ_G(x) ℓ_f²`

from the Phase VIII gauge buildout, where `ℓ_f` is a filament correlation length.

`w(e) = exp[-T ℓ_f²] α_top(x_e)`

from the 2025-08/31 status overview, where `ℓ_f` is a reconnection loop/segment scale.

Neither equation is promoted into current H(s)H construction; both are provenance markers for the meaning of `ℓ_f`.

## Provenance / chronology impact
The unresolved edge in XW-015 is sharpened. The archive does not currently show that SAT.O9 inherited an already established **wavefront thickness** `ℓ_f`. Instead it shows that `ℓ_f` already carried a different filament-scale meaning before O9.

The likely historical possibilities remain open:
1. O9 intentionally identified filament correlation scale with wavefront thickness;
2. O9 reused the symbol while changing its referent;
3. an intermediate source supplied the identification but has not yet been recovered.

No choice among these is justified yet.

## Historical prediction / target status
`Planck-scale` appears already in the June-18 internal buildout as a characterization of the filament correlation unit. This predates O9's explicit `ℓ_f = ℓ_P` wavefront-thickness assignment.

Classification:
- Phase VIII: historical scale characterization / assumption (`Planck-scale unit`), not recovered as an independent derivation;
- O9: later explicit equality `ℓ_f = ℓ_P`, but with a changed or at least differently described object type.

The Planckian scale remains quarantined from forward construction.

## Paper provenance packet
No new paper packet created. For any future finite-core/resolver paper, add a notation-warning entry: historical `ℓ_f` is overloaded across carrier and resolver roles and cannot be cited as a single continuous parameter without a bridge source.

## Earliest unsupported edge
The earliest live unsupported dependency is now:

`filament correlation / loop-segment scale ℓ_f (Planck-scale characterization)`
→ ?
`wavefront thickness ℓ_f = ℓ_P in O9`.

The missing item is not merely a numerical derivation; it is an **object-identification step**. We need a firsthand or development source stating whether the finite carrier scale and finite wavefront thickness were intended to be the same physical/geometric degree of freedom.

## Bidirectional provenance pointers
Backward:
- `SAT-O Theory Work/SAT_PHASE_VIII_GAUGE_BUILDOUT.txt` (internal 2025-06-18);
- `2025-8-24 STATUS OVERVIEW.txt` (content heading 2025-08-31; filename/date conflict preserved).

Forward:
- `EARLY LOGGED/2025-10-24_00 SAT O.txt` (O9 wavefront-thickness repurposing);
- XW-015;
- later finite swept-slab and `h_Σ` lineage from XW-014/XW-013.

## Next quarry target
Advance the SAT.O Phase VIII→O8→O9 transition, prioritizing development conversations around `Module_O8_Audit_Combined*.txt`, `SAT_O8_AUDIT_Results.txt`, and adjacent October logged dialogue. Search specifically for an explicit sentence/equation identifying filament correlation length or segment scale with time-wavefront thickness. If none appears, classify O9's symbol reuse as generated/not-source-secure rather than continuous genealogy.