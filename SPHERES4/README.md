# H(s)H Spherical Constraint Backend v0.3

This is a small geometric execution backend for equations supplied by a separate standard-equation system. It does **not** declare spheres, a lattice, or a particular ontology to be fundamental. Its job is to test whether an imported equation can be represented and calculated through H(s)H-compatible curves, finite tubes, shell constraints, and readout maps.

The first round trip uses an exact standard geometry:

- three equal `S^3` hypersurfaces in `R^4`;
- centers at the vertices of an equilateral triangle of side `d`;
- regular common intersection `S^1` with radius

  `rho = sqrt(R^2 - d^2/3)`;

- carrier-collapse bifurcation at `d = sqrt(3) R`.

The implementation independently traces the carrier numerically, verifies the analytic result, and calculates the decomposition

`v_total = v_surface + v_internal`.

v0.2 adds a second, deliberately controlled experiment: one of the three shells undergoes a volume-preserving oscillatory ellipsoidal deformation while the other two remain fixed. The backend traces the evolving carrier through one complete cycle and exports:

- the full four-dimensional carrier coordinates for every frame;
- surface-forced and internal tangent motion;
- circumference and discrete curvature history;
- minimum Jacobian singular value as a bifurcation margin;
- continuation-seed return error, endpoint periodicity disclosure, and constraint residuals.

v0.3 adds an exact geometric-event benchmark. The equal-shell center separation is continued through the carrier-collapse value `d_c = sqrt(3) R`. The backend compares analytic and numerical histories for carrier radius, circumference, curvature, forced response, and all Jacobian singular values. It explicitly classifies regular, near-critical, rank-loss, and no-real-carrier states.

Carrier closure is now accepted only after departure, return-direction crossing of a local Poincare section, local re-entry, and tangent recovery. Optional singular-value adaptive stepping reduces the tracing step near rank loss.

## Status discipline

Every mapping result distinguishes the authoritative input equation from its H(s)H representation. The current status is `exact_identity_with_numerical_verification`. No physical interpretation beyond the supplied equation packet is inferred.

The spherical backend is modular. Superhelical nesting, braid nesting, Electrogravity, and Interbraid dynamics are future modules and must remain distinct.

## Run the demonstration

From this directory:

```bash
python run_demo.py
```

The result is written to `build/equal_s3_mapping_result.json` and summarized in the terminal.

Run the deformation-cycle demonstration:

```bash
python run_deformation_demo.py
```

It writes:

- `build/one_shell_deformation_result.json`
- `build/one_shell_deformation_history.csv`
- `build/one_shell_deformation_curves.npz`

Run the exact carrier-collapse demonstration:

```bash
python run_bifurcation_demo.py
```

It writes:

- `build/equal_s3_collapse_result.json`
- `build/equal_s3_collapse_history.csv`
- `build/equal_s3_collapse_curves.npz`

## Run the verification suite

```bash
python -m unittest discover -s tests -v
```

## Use the command-line interface

```bash
PYTHONPATH=src python -m hsh_spheres.cli \
  examples/equal_s3_packet.json \
  --output build/equal_s3_mapping_result.json
```

## Project layout

- `schemas/equation_packet.schema.json` — contract expected from the standard-equation system.
- `schemas/mapping_result.schema.json` — H(s)H backend result contract.
- `examples/equal_s3_packet.json` — first authoritative input packet.
- `src/hsh_spheres/contracts.py` — runtime contract validation.
- `src/hsh_spheres/geometry.py` — shells, intersections, velocity decomposition, continuation, and bifurcation diagnostics.
- `src/hsh_spheres/deformation.py` — oscillatory shell deformation and full-cycle carrier tracking.
- `src/hsh_spheres/collapse.py` — exact carrier-collapse continuation and event classification.
- `src/hsh_spheres/roundtrip.py` — exact-to-numerical round trip.
- `src/hsh_spheres/runner.py` — backward-compatible packet dispatch.
- `docs/INTERFACE.md` — integration notes and extension boundaries.
- `tests/` — analytic, numerical, invariance, contract, and bifurcation checks.

## Immediate extension path

1. Accept a packet exported by the existing standard-equation system.
2. Extend the event kernel to an asymmetric one-shell pinch/split benchmark.
3. Lift traced carriers to finite tube surfaces with a Bishop frame.
4. Add separate `SuperhelixOperator` and `BraidOperator` modules.
5. Add Interbraid energy only after the geometry passes its invariance tests.
6. Add the BEC medium-response backend separately for Electrogravity.
