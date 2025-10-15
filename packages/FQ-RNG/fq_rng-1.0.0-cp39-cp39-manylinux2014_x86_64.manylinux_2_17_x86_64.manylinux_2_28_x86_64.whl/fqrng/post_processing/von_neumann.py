"""Von Neumann Extractor - Bias removal post-processing."""

import numpy as np

def von_neumann_extractor(bits: np.ndarray) -> np.ndarray:
    """
    Von Neumann extractor: pair bits, keep when different, discard when equal.
    Removes bias from raw quantum measurements.
    """
    extracted = []
    i = 0
    while i < len(bits) - 1:
        if bits[i] != bits[i+1]:
            extracted.append(bits[i])
        i += 2
    return np.array(extracted, dtype=np.uint8)

def bias_removal(bits: np.ndarray, threshold: float = 0.5) -> np.ndarray:
    """XOR-based bias removal for highly biased sources."""
    if len(bits) < 2:
        return bits
    
    # XOR pairs
    result = []
    for i in range(0, len(bits) - 1, 2):
        result.append(bits[i] ^ bits[i+1])
    
    return np.array(result, dtype=np.uint8)
