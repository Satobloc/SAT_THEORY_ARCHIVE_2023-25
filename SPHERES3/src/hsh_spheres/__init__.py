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

__all__ = [
    "ConstraintSystem",
    "ContractError",
    "QuadraticShell",
    "TraceResult",
    "analytic_equal_s3_carrier",
    "equal_s3_system",
    "load_equation_packet",
    "run_roundtrip",
    "trace_closed_carrier",
    "validate_equation_packet",
]
