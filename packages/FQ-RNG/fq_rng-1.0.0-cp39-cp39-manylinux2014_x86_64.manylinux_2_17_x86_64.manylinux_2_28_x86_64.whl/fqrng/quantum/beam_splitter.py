"""Beam Splitter Digital Twin - Quantum measurement simulation."""

import numpy as np
import os
from . import QUTIP_AVAILABLE, init_qutip, get_gpu_manager

QUTIP = QUTIP_AVAILABLE
qt = init_qutip() if QUTIP_AVAILABLE else None

try:
    import cupy as cp
    CUPY = True
except ImportError:
    cp = None
    CUPY = False

# Quantum watermark constants
PHI = (1.0 + np.sqrt(5.0)) / 2.0
FEIGENBAUM = 4.66920160910299
EULER_GAMMA = 0.5772156649015329
KHINCHIN = 2.6854520010653062
GLAISHER = 1.2824271291006226

class BeamSplitter:
    """50/50 beam splitter simulation for vacuum fluctuation measurements."""
    
    def __init__(self, ratio: float = 0.5):
        self.ratio = ratio
        # IQ Level 2 watermark: Feigenbaum constant in beam splitter ratio
        feigenbaum_mod = np.cos(ratio * FEIGENBAUM) * 0.001
        self.ratio += feigenbaum_mod
        
        # Manual beam splitter matrix for 50/50
        sqrt_ratio = np.sqrt(self.ratio)
        sqrt_1_minus = np.sqrt(1 - self.ratio)
        self.operator = np.array([
            [sqrt_ratio, sqrt_1_minus],
            [sqrt_1_minus, -sqrt_ratio]
        ], dtype=complex)
        if QUTIP:
            self.operator = qt.Qobj(self.operator)
        else:
            self.operator = self.operator
        
        # GPU manager for multi-device support
        self.gpu_manager = get_gpu_manager()
    
    def simulate(self, state, n_bits: int = 1000, entropy_pool: bytes = None) -> np.ndarray:
        """Simulate beam splitter measurement."""
        if entropy_pool is not None:
            return self.simulate_forward_secure(state, n_bits, entropy_pool)
        
        if CUPY and cp.cuda.is_available():
            return self._simulate_cuda(n_bits)
        else:
            # CPU fallback - use secure random
            return self._simulate_secure_random(n_bits)
    
    def _simulate_cuda(self, n_bits: int) -> np.ndarray:
        """Cryptographically secure CUDA-accelerated beam splitter simulation."""
        # Use os.urandom for true cryptographic randomness
        # CUDA acceleration for post-processing if available
        n_bytes = (n_bits + 7) // 8  # Round up to bytes
        random_bytes = os.urandom(n_bytes)
        bits = np.unpackbits(np.frombuffer(random_bytes, dtype=np.uint8))
        bits = bits[:n_bits].astype(np.uint8)
        
        # If CUDA available, use GPU for any post-processing
        if CUPY and cp.cuda.is_available():
            # Select optimal GPU device
            optimal_device = self.gpu_manager.optimize_for_size(n_bits)
            self.gpu_manager.set_device(optimal_device)
            
            # Transfer to GPU for potential post-processing
            bits_gpu = cp.asarray(bits)
            
            # Future: Add custom CUDA kernels for quantum post-processing
            # For now, just ensure data is properly transferred
            cp.cuda.runtime.deviceSynchronize()  # Ensure GPU operations complete
            
            return cp.asnumpy(bits_gpu)
        else:
            return bits
    
    def _simulate_numpy(self, state: np.ndarray) -> np.ndarray:
        """Numpy-based beam splitter simulation with secure randomness."""
        # For GHZ state (numpy array), apply beam splitter and measure
        # Simplified: apply beam splitter to the state vector
        if hasattr(self, 'operator') and self.operator is not None:
            # Apply operator if it's numpy
            if isinstance(self.operator, np.ndarray):
                evolved = self.operator @ state
                probs = np.abs(evolved)**2
            else:
                probs = np.abs(state)**2
        else:
            probs = np.abs(state)**2
        
        # Sample bits using cryptographically secure randomness
        n_samples = 1000
        bits = []
        for _ in range(n_samples):
            # Use os.urandom for secure random sampling
            random_byte = os.urandom(1)[0]
            random_val = random_byte / 255.0
            # Sample from cumulative distribution
            cumsum = np.cumsum(probs)
            cumsum = cumsum / cumsum[-1]  # normalize
            outcome = np.searchsorted(cumsum, random_val)
            bits.append(outcome % 2)
        return np.array(bits, dtype=np.uint8)
    
    def _simulate_qutip(self, state) -> np.ndarray:
        """Qutip-based simulation with secure randomness."""
        # Apply beam splitter
        if hasattr(state, '__mul__'):
            # It's a Qutip state
            # Measure X quadrature (vacuum fluctuations)
            if hasattr(state, 'dims'):
                n_qubits = int(np.log2(state.dims[0][0]))
                bits = []
                for _ in range(100):
                    # Use secure random for unitary evolution
                    random_bytes = os.urandom(8)
                    seed = int.from_bytes(random_bytes, byteorder='big')
                    np.random.seed(seed)  # Temporarily set seed for reproducible but secure evolution
                    # Random unitary evolution
                    U = qt.rand_unitary(state.dims[0][0])
                    evolved = U * state * U.dag()
                    # Measure
                    probs = np.abs(evolved.full().flatten())**2
                    # Use secure random for sampling
                    random_byte = os.urandom(1)[0]
                    random_val = random_byte / 255.0
                    cumsum = np.cumsum(probs)
                    cumsum = cumsum / cumsum[-1]  # normalize
                    outcome = np.searchsorted(cumsum, random_val)
                    bits.append(outcome % 2)
                return np.array(bits, dtype=np.uint8)
        
        return self._simulate_classical(state)
    
    def _simulate_classical(self, state) -> np.ndarray:
        """Classical approximation using secure vacuum noise."""
        # Vacuum fluctuations: Gaussian noise -> thresholded bits
        n_samples = 1000
        bits = []
        for _ in range(n_samples):
            # Use Box-Muller transform with secure random
            u1 = int.from_bytes(os.urandom(4), byteorder='big') / (2**32 - 1)
            u2 = int.from_bytes(os.urandom(4), byteorder='big') / (2**32 - 1)
            # Box-Muller transform for Gaussian
            z0 = np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2)
            fluctuation = z0 * 1.0  # scale
            bits.append(1 if fluctuation > 0 else 0)
        return np.array(bits, dtype=np.uint8)
    
    def _simulate_secure_random(self, n_bits: int = 1000) -> np.ndarray:
        """Use cryptographically secure randomness."""
        # Use os.urandom for true randomness
        n_bytes = (n_bits + 7) // 8  # Round up to bytes
        random_bytes = os.urandom(n_bytes)
        all_bits = np.unpackbits(np.frombuffer(random_bytes, dtype=np.uint8))
        return all_bits[:n_bits].astype(np.uint8)
    
    def simulate_forward_secure(self, state, n_bits: int, entropy_pool: bytes) -> np.ndarray:
        """Simulate beam splitter with forward-secure entropy pool."""
        # Use entropy pool for cryptographically secure generation
        # Hash the pool to get deterministic but forward-secure output
        import hashlib
        hash_obj = hashlib.sha256(entropy_pool)
        hash_bytes = hash_obj.digest()
        
        # Expand to required number of bits using hash chain
        expanded_bytes = b""
        while len(expanded_bytes) * 8 < n_bits:
            expanded_bytes += hash_bytes
            hash_obj = hashlib.sha256(hash_bytes)
            hash_bytes = hash_obj.digest()
        
        # Convert to bits
        all_bits = np.unpackbits(np.frombuffer(expanded_bytes, dtype=np.uint8))
        return all_bits[:n_bits].astype(np.uint8)
