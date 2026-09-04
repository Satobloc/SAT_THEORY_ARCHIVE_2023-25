"""H(s)H spherical constraint backend."""

from .contracts import ContractError, load_equation_packet, validate_equation_packet
from .geometry import (
    ConstraintSystem,
    QuadraticShell,
    TraceResult,
    analytic_equal_s3_carrier,
    equal_s3_system,
    trace_closed_carrier,
)
from .roundtrip import run_roundtrip
from .runner import run_packet
from .collapse import analytic_collapse_state, collapse_result, run_collapse_sweep

__all__ = [
    "ConstraintSystem",
    "ContractError",
    "QuadraticShell",
    "TraceResult",
    "analytic_equal_s3_carrier",
    "equal_s3_system",
    "load_equation_packet",
    "run_roundtrip",
    "run_packet",
    "analytic_collapse_state",
    "collapse_result",
    "run_collapse_sweep",
    "trace_closed_carrier",
    "validate_equation_packet",
]
