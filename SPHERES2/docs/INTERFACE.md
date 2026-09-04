# Equation-system to H(s)H backend interface

## Responsibility boundary

The standard-equation system owns:

- accepted equations and source provenance;
- variable definitions and dimensions;
- assumptions, symmetries, and domains;
- initial and boundary data;
- known solutions, limiting cases, and empirical anchors.

This backend owns:

- geometric object and operator maps;
- constraint realization;
- numerical execution of that realization;
- readout into the packet's observable quantities;
- residuals, diagnostics, and mapping status.

The backend must not silently repair an input packet. Invalid or incomplete packets fail validation.

## Round-trip relation

The intended pipeline is:

`standard equation -> equation packet -> H(s)H mapping -> geometric solver -> readout -> standard observable`.

For observable `O`, the backend reports

`Delta_map = O_HsH - O_standard`.

## Required status values

- `exact_identity`
- `exact_identity_with_numerical_verification`
- `coordinate_rewrite`
- `controlled_approximation`
- `calibrated_representation`
- `candidate_extension`
- `failed_mapping`

## Nesting boundary

Superhelical nesting and braid nesting are separate operations:

- a superhelix operator acts on one carrier and changes its path geometry;
- a braid operator acts on several carriers or bundles and changes their relational topology.

Neither operation is implemented in v0.1. Their future packet fields and code modules must remain separately typed.

## Current geometric backend

Each deformable quadratic shell is

`F_a(x, lambda) = (x-c_a)^T A_a(lambda) (x-c_a) - R_a(lambda)^2 = 0`.

For three independent constraints in `R^4`, the carrier tangent spans the one-dimensional nullspace of the Jacobian `J`.

For moving constraints,

`J x_dot = -partial_lambda F`,

so

`x_dot = -J^+ partial_lambda F + u t`.

The pseudoinverse term is surface-forced motion. The `u t` term is internal motion along the carrier.

## v0.2 deformation operation

Packets may set `mapping_request.operation` to `one_shell_shape_oscillation`. The first shell then uses

`A_1(phi) = diag(1, 1, exp(-2 epsilon), exp(2 epsilon))`

with

`epsilon(phi) = amplitude sin(phi)`.

The determinant of `A_1` remains one. This is a controlled volume-preserving anisotropic deformation in the plane of the regular carrier, not a physical claim about a particular medium.

The phase parameter is dimensionless. Reported surface-forced velocity is therefore displacement per unit phase unless a separate physical phase rate is supplied by an authoritative packet.

The operation reports the minimum singular value of the constraint Jacobian over every traced carrier. A value tending toward zero signals loss of regularity; v0.2 does not infer a physical event label from that diagnostic.

## Future dynamics boundary

The two current force mechanisms should be added as separate backends:

- Electrogravity: nonlocal BEC-medium response to worldtube motion;
- Interbraid: direct contact, braid, exclusion, reconnection, and history tension.

Observed gravity may combine outputs from both, but that does not merge their primitive operators.
