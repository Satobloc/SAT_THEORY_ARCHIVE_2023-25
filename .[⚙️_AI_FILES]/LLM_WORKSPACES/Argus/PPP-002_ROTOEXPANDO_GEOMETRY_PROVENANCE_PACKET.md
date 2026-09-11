# PPP-002 — Rotoexpando Geometry provenance packet

## Candidate paper
`Satobloc/HSH_RESOURCES/REDISCOVERED/rotoexpando_geometry_definition.tex`

Title: `Rotoexpando Geometry: Definitions and Characterization — Nested Helices, Framed Spheres, Closure, and Equivalent Representations`
Date on manuscript: 11 September 2026
Author line: Nathan McKnight and collaborators
Current blob SHA: `5c21c6152482249e4432ded423b0040e70fc8b4f`
First public/repository upload currently located: commit `056376a1725a929f0c4017a449e29539402f2a58`, 2026-09-11T06:06:22Z.

## Claim maturity
Current status: bounded mathematical-definition manuscript / pure-geometry program.

The manuscript explicitly disclaims a physical-theory assertion and treats Hagalaz/ᚼ as optional notation rather than ontology. Physical SAT/H(s)H identifications therefore should not be backfilled into this paper without a separate derivation.

## Controlling definitions safe to cite from current manuscript
Canonical helix:

`gamma(theta) = rho cos(theta)e1 + rho sin(theta)e2 + h theta e3`

`kappa = rho/(rho^2+h^2)`

`tau = h/(rho^2+h^2)`

`tau/kappa = h/rho = tan(beta)` under the declared pitch-angle convention.

Adjacent-order measures:

`mu_n = D_(n+1)/D_n`

`nu_n = k_(n+1)/k_n`

`xi_n = ||c_(n+1)-c_n||/D_n`

plus relative phase, frame rotation, chirality, and normalized finite-core thickness.

Hagalaz/ᚼ:

`H_ij := (sigma_ij, Q_ij)`

or

`H_ij := (Delta c_ij, sigma_ij, Q_ij)`

with similarity map

`x -> c_j + sigma_ij Q_ij (x-c_i)`.

Finite-tube admissibility:

`inf_{s not≈t} ||X(s)-X(t)|| = 2a`

and schematically

`a < 1/kappa_max`.

Circular-helix separation:

`D^2(Delta) = 2 rho^2(1-cos Delta) + h^2 Delta^2`

with stationary nonlocal closest-approach candidates satisfying

`rho^2 sin Delta + h^2 Delta = 0`.

Minimal atlas:

`C_n = (mu_n, nu_n, xi_n, Delta phi_n, Q_n, chi_n, a_n/D_n)`.

## Earliest internal formulation currently linked
Hagalaz/ᚼ lineage currently points to the 2026-09-08 firsthand development conversation recorded in `XW-007_FINITE_CORE_MEASURES_H_RUNIC_LINEAGE.md`, where ᚼ is introduced as shorthand for a canonical evolution relation and deviations are separated from the standard state.

The present manuscript sharpens that notation into an adjacent-order similarity/frame tuple and explicitly states that dilation is not required within a single fixed-diameter helical order. This should be classified as a current mathematical formalization/reformulation unless earlier exact tuple notation is recovered.

Finite-thickness lineage remains split:

- historical resolving-surface thickness candidate: `C5.txt` / duplicate lineage, conditional generated proposal;
- explicit finite slab: `H(s)H Dev +/H(s)H MANIFOLDS.txt`, provenance of the `Sigma_t^(h)` formula unresolved;
- current paper: finite tube radius `a` around a centerline, used as pure geometry rather than resolving-surface ontology.

Do not conflate these three thickness notions.

## Known antecedents/prior art already present in HSH_RESOURCES
Newly uploaded in the same 2026-09-11 batch:

1. `REDISCOVERED/Fletcheretal2001.pdf`
   - Neville H. Fletcher, T. Tarnopolskaya, F. R. de Hoog.
   - `Wave Propagation on Helices and Hyperhelices: A Fractal Regression`.
   - Proceedings of the Royal Society A (2001).
   - DOI: 10.1098/rspa.2000.0654.
   - Directly relevant prior art for recursively nested helices/hyperhelices and hierarchical wave behavior.

2. `REDISCOVERED/Fletcher2004a.pdf`
   - Neville H. Fletcher.
   - `Hyperhelices: A classical analog for strings and hidden dimensions`.
   - American Journal of Physics 72(5):701–703 (2004).
   - DOI: 10.1119/1.1652038.
   - Direct prior art for a rod coiled into a helix, itself coiled repeatedly through finite or infinite order.

3. `REDISCOVERED/fuller-1971-the-writhing-number-of-a-space-curve.pdf`
   - F. Brock Fuller.
   - `The Writhing Number of a Space Curve`.
   - PNAS 68(4):815–819 (1971).
   - DOI: 10.1073/pnas.68.4.815.
   - Foundational prior art for writhe of space curves and coiled/twisted cord geometry.

## Immediate novelty/priority boundary
Do not claim novelty for:

- helices or superhelices/hyperhelices;
- recursive helix-of-helix constructions in general;
- framed/material rod descriptions in general;
- writhe/twist/linking machinery in general;
- a finite tube around a centerline in general;
- local curvature and nonlocal self-contact as tube-thickness constraints in general.

Potentially narrower claims requiring further comparison before any priority language:

- the exact selected minimal atlas and dependency structure;
- the specific Hagalaz adjacent-order tuple as a unifying conversion convention;
- a demonstrated lossless conversion among point-pair, helix, framed-sphere/UI, toroidal, ribbon, and braid representations under explicitly stated retained data;
- any special-locus classification or invariant that survives comparison with standard similarity geometry, screw theory, framed-curve/ribbon theory, knot/ropelength theory, and configuration-space braid theory.

## Unresolved conflicts / required checks
1. Recover exact development-conversation provenance for the manuscript. Generated/derived manuscript text must not become its own historical authority.
2. Check whether all claimed `equivalent representations` are truly losslessly convertible with the stated state variables; axial roll is already acknowledged as extra data for bare point pairs.
3. Replace schematic finite-tube curvature bound with the precise reach/thickness formulation appropriate to the intended regularity class before asserting a theorem-level statement.
4. Search standard literature on tube thickness, reach, ropelength, doubly-critical self-distance, and ideal knots for the exact first-contact formulation.
5. Compare framed-sphere/UI tuple against standard Euclidean similarity-group and framed-curve representations before novelty claims.
6. Keep physical H(s)H particle assignments and historical constants outside this paper unless independently regenerated after the geometry is frozen.

## Current safe characterization
A pure-geometry synthesis manuscript that collects nested helical/similarity/frame representations into a compact adjacent-order state description and explicitly includes finite-core contact geometry. Its ingredients have substantial prior art; novelty, if any, must be sought in the exact dependency/representation synthesis or newly classified residual invariants rather than in nested helices themselves.
