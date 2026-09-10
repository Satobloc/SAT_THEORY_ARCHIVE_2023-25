# XW-004 — CKM / Jarlskog closure audit

Status: working audit artifact; not canonical theory text.

## Source inspected

Primary focused document:

- `Satobloc/SAT_THEORY_ARCHIVE_2023-25/CP CLOSURE.txt`

Repository chronology recovered in this audit:

- first surviving Git ingest of `CP CLOSURE.txt`: `2026-06-29T10:18:39Z`, commit `ec6ff6182340346b649f905653fd5f74886d1502`.
- this Git date is an archive-ingest bound, not necessarily the composition date.

The current dashboard derivation map places the Dirac CP phase/homecoming machinery under M14 and already flags a phase-count mismatch risk; it does not presently isolate the arithmetic inconsistency below.

## What the focused document claims

`CP CLOSURE.txt` states:

- `B ≈ 0.2387`
- `S ≈ 0.2621`
- `theta12 = B(1-B^2) ≈ 0.2251`
- `theta23 = B^2(1-S) ≈ 0.0420`
- `theta13 = B^3 S ≈ 0.00356`
- `delta_CP = 270°`
- `J_eff = (3/4) theta12 S(1-S) ≈ 0.03265`
- `J_obs = J_eff B^5 ≈ 2.53e-5`
- `J_CKM = theta12 theta23 theta13 sin(delta_CP) ≈ -2.53e-5`

It then says the last two quantities are two independent matching derivations.

## Direct arithmetic audit

Using the document's own stated definitions with `B = 3/(4*pi)` and `S = 0.2621` gives approximately:

- `theta12 = 0.2251263`
- `theta23 = 0.0420553`
- `theta13 = 0.00356616`
- `J_eff = 0.0326552`
- `J_eff B^5 = 2.53226e-5`
- `theta12 theta23 theta13 sin(270°) = -3.37635e-5`

Therefore the claimed equality between the latter two routes does **not** follow from the formulas printed in the document. Their magnitudes differ by about 33% relative to the `2.53e-5` value.

The exact standard-parameterization Jarlskog expression also contains cosine factors,

`J = c12 c23 c13^2 s12 s23 s13 sin(delta)`.

For these small angles, those cosine factors only reduce the magnitude slightly; they do not bring `~3.38e-5` down to `2.53e-5`. Thus this is not explained by the document's use of the small-angle product approximation.

## Sector-label issue

The document also mixes two distinct flavor-sector conventions:

- its angle values `~0.225, ~0.042, ~0.00356` are CKM/quark-like;
- `delta_CP = 270°` is a value historically discussed as a leptonic/PMNS phase target, not the observed CKM phase.

The 2024 Particle Data Group CKM review gives the quark-sector Jarlskog invariant at about `3.12e-5`, and the standard CKM parametrization uses the quark CP phase `delta`; the quark phase is not 270°. The SAT archive's own later `SAT-TO-STANDARD 2.txt` already warns that `J_eff` should be called a Jarlskog-like CP-odd geometric invariant rather than silently identified with the Standard Model Jarlskog invariant.

## Classification

**Observation:** `CP CLOSURE.txt` contains an internal arithmetic mismatch between its `J_obs` route and its stated CKM-product route.

**Inference:** the phrase “two independent derivations now match” is unsupported as written.

**Further issue:** the document conflates a CKM-like angle triplet with a 270° CP phase associated in SAT material with a different sector. A valid comparison requires an explicit declaration of whether the construction is intended to model CKM, PMNS, or a SAT-internal invariant that is only analogous to either.

**Current mathematical status:** `FRACTURED / UNDERDEFINED` for the claimed CP-sector closure. The individual angle formulas are numerically reproducible; the closure claim is not.

This does **not** imply that a geometric CP mechanism is impossible or that every later use of `J_eff` is invalid. It means the specific equivalence asserted in `CP CLOSURE.txt` must not be treated as a closed derivation.

## Prior-art / standard-comparison boundary

The Jarlskog invariant and CKM standard parametrization are established Standard Model machinery. SAT cannot claim novelty for the invariant itself, the existence of a three-angle-plus-phase parametrization, or the general fact that CP violation can be expressed through a rephasing-invariant combination.

Any potentially distinctive SAT/H(s)H result would have to be narrower: e.g. a genuinely derived geometric mechanism that fixes a specific mixing matrix or invariant from independently specified H(s)H structure without importing the empirical target. That narrower derivation has not been established by the source inspected here.

## Provenance / crosswalk status

No exact `DEVELOPMENT_FULL_CONVOS` source conversation for the creation of `CP CLOSURE.txt` was recovered in this pass. Search-index silence in HsH is not treated as absence. The focused document's first surviving Git ingest is secure, but the composition date and source conversation remain unresolved.

Candidate downstream/related family already visible in the main archive includes:

- `Filament onto.txt`
- `_AUTO_EXTRACTED_TEXT/SCALAR_ANGULAR_TORSION___PHYS_D_FINAL-8.txt`
- `FINAL.pdf` / `_AUTO_EXTRACTED_TEXT/FINAL.txt`
- `SAT PRE-H(s)H TIGHTENING.txt`
- `SAT-TO-STANDARD 2.txt`

These should be treated as related reformulation/audit material until exact textual chronology is recovered.

## HSH_RESOURCES bibliography status

Repository code searches for `Jarlskog` and `CKM` in `Satobloc/HSH_RESOURCES` returned no hits in this pass. Because HSH_RESOURCES contains opaque filenames and machine extraction layers, this is **not** an absence determination. The PDG CKM review and the original Jarlskog literature are bibliography-gap candidates pending path/title verification against the human/provisional bibliography.

## Recommended next actions

1. Add a reviewer note under M14 in `..[🎛️_NATHAN_DASH]/..Derivation_Index.md` when a safe non-destructive edit path is available: arithmetic mismatch; sector-label ambiguity; status `FRACTURED / UNDERDEFINED`.
2. Locate the source-development conversation where `J_obs = J_eff B^5` and the claimed independent CKM route were first joined.
3. Separate three objects explicitly in future formalization: SAT-internal `J_eff`, quark `J_CKM`, and leptonic `J_PMNS`.
4. If a geometric mixing derivation is retained, construct the full unitary matrix and compute its rephasing invariant directly rather than multiplying approximate target angles.

## Coverage limits

- `CP CLOSURE.txt`: full direct read (short file).
- `..Derivation_Index.md`: direct read of the current machinery map including M14.
- `SAT-TO-STANDARD 2.txt`: partial direct read sufficient to verify its terminology warning around `J_eff`.
- `FINAL.pdf`: inspected through committed extracted text, not visual PDF layout in this pass.
- HsH FULL CONVOS: targeted code-search only; no exact source conversation recovered.
- HSH_RESOURCES: targeted code-search only for `Jarlskog` / `CKM`; no absence claim.