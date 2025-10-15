"""FQRNG API Facade - High-level interface for quantum RNG (arxiv.org/abs/2206.02292)."""

from .core.qrng_core import QuantumRNG
from .core.nist_validator import NISTValidator, EntropyMetrics

def get_rng(bits: int = 1024, validate: bool = False) -> QuantumRNG:
    """Get configured quantum RNG instance."""
    return QuantumRNG(bits, validate)

def generate_bits(bits: int = 1024, validate: bool = False):
    """Generate random bits with optional validation."""
    rng = get_rng(bits, validate)
    return rng.generate_bits()

def generate_int(min_val: int = 0, max_val: int = 2**32-1) -> int:
    """Generate random integer in range."""
    rng = get_rng()
    return rng.generate_int(min_val, max_val)

def generate_float(min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Generate random float in range."""
    rng = get_rng()
    return rng.generate_float(min_val, max_val)

def validate_bits(bits):
    """Validate bit sequence with NIST tests."""
    validator = NISTValidator()
    results, entropy = validator.run_suite(bits)
    return results, entropy

__all__ = ["get_rng", "generate_bits", "generate_int", "generate_float", "validate_bits"]