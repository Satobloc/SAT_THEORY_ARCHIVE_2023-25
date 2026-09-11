# XW-017 — O8 transverse-scale vs O9 wavefront-thickness collision

## Scope
Bounded provenance waypoint for the live finite-core discrimination program. This run follows XW-016 and advances the Phase VIII → O8 → O9 family without promoting any historical scale into the forward build.

## Checkpoint consumed
`.[⚙️_AI_FILES]/LLM_WORKSPACES/Argus/XW-016_LF_SYMBOL_COLLISION_AND_PRE_O9_SCALE_LINEAGE.md`

XW-016 established that `ℓ_f` had pre-O9 carrier/correlation meanings and that O9 reused `ℓ_f` for wavefront thickness. This run asks whether the O8 family supplies an explicit object-identification bridge.

## Lightweight repository change check
- `Satobloc/SAT_THEORY_ARCHIVE_2023-25`: newest substantive human addition before this waypoint remains XW-016; intervening commit `99accf7...` is archive-admin maintenance.
- `Satobloc/HsH`: newest sampled commits remain conversation-viewer/date-index maintenance, latest `7b8b2d6...` at 2026-09-11T06:15:20Z.
- `Satobloc/HSH_RESOURCES`: newest substantive sampled commit remains `ddbce31...` (`Refresh extracted corpus and bibliography intake`) at 2026-09-11T06:07:59Z.

## Source family advanced
### 1. `SAT_O8.txt`
Repository history first places this file in commit `85074dd...` (`Still the living foundation (Older Versions).`) at 2025-10-27T01:24:42Z. The file itself is an undated formal module.

It defines the filament transverse scale as

`ℓ_f ~ (2A/T)^(1/3)`

and uses it in the core mass relation

`m_ψ^(0) ~ T ℓ_f / c^2`.

It further reports a historical calibration `ℓ_f ~ 10^-5 m`; this numerical value is quarantined and not promoted.

### 2. `EARLY LOGGED/Module_O8_Audit_Combined 3.txt`
The module-specific glossary is explicit:

`ℓ_f: Filament transverse scale defined by ℓ_f = (2A/T)^(1/3), where A is rigidity and T is tension.`

The O8 audit instructions themselves repeatedly call `ℓ_f` a **transverse scale** and demand one-symbol/one-meaning consistency.

### 3. `SAT O Derivations/SAT_D5_GAUGE_TOPOLOGY.txt`
D5 also uses

`ℓ_f = (2A/T)^(1/3)`

inside gauge-coupling scalings, again as a filament scale. This confirms that the O8 meaning is inherited from a broader SAT.O derivation family, not an isolated glossary gloss.

### 4. `EARLY LOGGED/2025-10-24_00 SAT O.txt` — SAT.O9
O9 instead defines

`ℓ_f = ℓ_P`

as **wavefront thickness fixed to one Planck length**, with `τ` the coordinate through the `ℓ_P`-thick time-wavefront and a Liouville field encoding local thickness fluctuations.

No equation or sentence in this file identifies the pre-existing filament transverse scale `(2A/T)^(1/3)` with the wavefront thickness.

### 5. `EARLY LOGGED/2025-10-24_1312_SAT_GLOSSARY_FINAL.txt`
This filename carries a same-day timestamp-like label later than the O9 filename; treat that ordering as filename chronology, not repository-public chronology. The document itself is titled `SAT.4D Glossary (Final Clean Edition)`, dated internally `July 2025`, and explicitly states:

- `Σ_t`: propagating 3D wavefront (resolving surface);
- `A`: filament rigidity (determines transverse scale);
- `ℓ_f = (2A/T)^(1/3)`: emergent transverse scale of filament structure;
- policy: `One symbol, one meaning: enforced throughout SAT.O framework.`

Repository ingest for this logged copy is much later (`5b1a838...`, 2026-09-07), so the 2025 filename/internal dates are internal provenance markers rather than public GitHub timestamps.

## Finite-core fact / conflict recovered
The O8/O9 transition does **not** currently supply a source-secure identification between carrier thickness and resolver thickness. Instead, the archive contains an explicit same-family semantic conflict:

`ℓ_f = (2A/T)^(1/3)` = filament transverse scale

versus

`ℓ_f = ℓ_P` = time-wavefront thickness.

Moreover, the SAT.4D glossary explicitly maintains the transverse-scale definition while separately defining `Σ_t` as the resolving wavefront and declaring one-symbol/one-meaning policy.

Therefore O9's reuse of `ℓ_f` cannot be treated as continuous genealogy absent an unrecovered bridge source.

## Representation / object type
- O8/D5/glossary `ℓ_f`: carrier/material transverse scale of filament structure.
- O9 `ℓ_f`: resolver/interface thickness of the time-wavefront.
- `Σ_t` in the glossary: a propagating 3D resolving surface, separately named from `ℓ_f`.

This directly supports keeping present candidate degrees of freedom distinct during finite-core discrimination:

`a_core` or other carrier width `!=_provenance` `h_resolver`.

It does not select B^3, B^2, S^2-boundary, slab-only, or layered architecture.

## Independently useful equations / limiting maps
Historical only:

`ℓ_f = (2A/T)^(1/3)`

is the strongest recovered pre-O9 object-defining relation for filament transverse scale.

`m_ψ^(0) ~ T ℓ_f / c^2`

and D5 gauge-coupling scalings use that same carrier-scale `ℓ_f`.

No independently sourced limiting map equating this scale with O9 wavefront thickness was recovered.

## Provenance / chronology impact
XW-016 left three possibilities open: intentional identification, symbol reuse, or missing intermediate bridge. This run materially disfavors treating intentional identification as source-secure because O8/D5/glossary repeatedly define `ℓ_f` as filament transverse scale, while O9 simply redefines it as wavefront thickness with no bridge.

The strongest current classification is:

**O9 `ℓ_f` wavefront usage = source-unsecured repurposing / semantic collision unless an intermediate development conversation explicitly identifies the two object types.**

## Historical prediction / target status
Historical candidate:

`ℓ_f ~ (2A/T)^(1/3)`

with O8's later numerical calibration `~10^-5 m`.

Status: historical formal relation plus historical calibration claim; not a current prediction, not released to forward builders, and upstream dimensional/provenance support remains unresolved.

O9's `ℓ_f = ℓ_P` remains a separate historical imposed scale choice, likewise quarantined.

## Paper provenance packet
No new bounded paper packet created. Update future finite-core/resolver packet warning:

- do not cite historical `ℓ_f` as a single continuous parameter across SAT.O8 and O9;
- O8/D5/glossary define a carrier transverse scale;
- O9 reuses the same symbol for resolver thickness without a recovered bridge.

## Earliest unsupported edge
The live unsupported dependency is now:

`filament transverse scale ℓ_f = (2A/T)^(1/3)`
→ **missing object-identification step**
`time-wavefront thickness ℓ_f = ℓ_P`.

A second unsupported edge lies upstream of the O8 relation itself: why `(2A/T)^(1/3)` is the correct finite transverse scale, and whether D5 genuinely derives it or imports it by dimensional/closure reasoning.

## Bidirectional provenance pointers
Backward:
- `SAT O Derivations/SAT_D5_GAUGE_TOPOLOGY.txt`;
- `SAT_O8.txt`;
- `EARLY LOGGED/Module_O8_Audit_Combined 3.txt`;
- `EARLY LOGGED/2025-10-24_1312_SAT_GLOSSARY_FINAL.txt`.

Forward:
- `EARLY LOGGED/2025-10-24_00 SAT O.txt` (O9 wavefront-thickness repurposing);
- XW-016/XW-015;
- later finite swept-slab and H(s)H `h_Σ` lineage from XW-014/XW-013.

## Coverage limit
This run inspected the bounded O8/D5/glossary/O9 source family and exact repository-history anchors above. It did not exhaust every October 2025 conversation export, duplicate, or generated audit artifact.

## Next quarry target
Advance upstream into the development conversation that first introduces `ℓ_f = (2A/T)^(1/3)`, prioritizing D5/O2 source provenance and any firsthand discussion of what geometric object `A` and `T` are supposed to determine. The key question is whether this was actually derived from a finite filament cross-section, adopted by dimensional closure, or imported from an analogy.