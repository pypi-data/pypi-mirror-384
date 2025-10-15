"""FQRNG - NIST-certified Quantum Random Number Generator.

Bell fractal RNG with auto NIST SP 800-22 validation.
"""

__version__ = "1.0.0"

# Import main classes once Cython is compiled
try:
    from .core.qrng_core import QuantumRNG
    from .core.nist_validator import NISTValidator, EntropyMetrics
    from .qrng import get_rng, generate_bits, generate_int, generate_float, validate_bits
    __all__ = ["QuantumRNG", "NISTValidator", "EntropyMetrics", "get_rng", "generate_bits", "generate_int", "generate_float", "validate_bits"]
except ImportError:
    # Not yet compiled
    __all__ = []
