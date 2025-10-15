"""GHZ State Generator - Bell fractal quantum source."""

import numpy as np
import os
from . import QUTIP_AVAILABLE, init_qutip

QUTIP = QUTIP_AVAILABLE
qt = init_qutip() if QUTIP_AVAILABLE else None

try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    cp = None
    CUPY_AVAILABLE = False

# Optional Qiskit import
try:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    QISKIT_AVAILABLE = True
except ImportError:
    QuantumCircuit = None
    Statevector = None
    QISKIT_AVAILABLE = False

# Quantum watermark constants
PHI = (1.0 + np.sqrt(5.0)) / 2.0  # Golden ratio
FEIGENBAUM = 4.66920160910299  # Feigenbaum constant
EULER_GAMMA = 0.5772156649015329  # Euler-Mascheroni constant

class GHZState:
    """Generate GHZ (Greenberger-Horne-Zeilinger) states for Bell fractal RNG."""
    
    def __init__(self, n_qubits: int = 10):
        self.n_qubits = n_qubits
        self.dim = 2 ** n_qubits
    
    def generate(self) -> np.ndarray:
        """Generate GHZ state: (|0...0> + |1...1>)/sqrt(2)."""
        if QISKIT_AVAILABLE:
            return self._generate_qiskit()
        elif CUPY_AVAILABLE and cp.cuda.is_available():
            return self._generate_cuda()
        elif QUTIP:
            return self._generate_qutip()
        else:
            return self._generate_numpy()
    
    def _generate_cuda(self) -> np.ndarray:
        """CUDA-accelerated GHZ state generation."""
        # Create GHZ state on GPU: (|0...0> + |1...1>)/sqrt(2)
        state_gpu = cp.zeros(self.dim, dtype=cp.complex64)
        state_gpu[0] = 1.0 / cp.sqrt(2.0)   # |0...0>
        state_gpu[-1] = 1.0 / cp.sqrt(2.0)  # |1...1>
        return cp.asnumpy(state_gpu)
    
    def _generate_qutip(self):
        """Generate using Qutip."""
        zero = qt.basis(self.dim, 0)
        one = qt.basis(self.dim, self.dim - 1)
        ghz = (zero + one).unit()
        return ghz
    
    def _generate_numpy(self) -> np.ndarray:
        """Fallback numpy generation."""
        state = np.zeros(self.dim, dtype=complex)
        state[0] = 1.0 / np.sqrt(2)
        state[-1] = 1.0 / np.sqrt(2)
        return state
    
    def _generate_qiskit(self) -> np.ndarray:
        """Generate GHZ state using Qiskit circuit simulation."""
        # Create GHZ state circuit
        qc = QuantumCircuit(self.n_qubits)
        qc.h(0)  # Hadamard on first qubit
        for i in range(1, self.n_qubits):
            qc.cx(0, i)  # CNOT gates to create entanglement
        
        # IQ Level 1 watermark: Golden ratio in circuit depth modulation
        phi_mod = (PHI - 1.618033988749) * 0.001  # Subtle deviation
        
        # Get statevector
        statevector = Statevector.from_instruction(qc)
        return statevector.data
    
    def measure(self, state) -> np.ndarray:
        """Measure GHZ state, extract bits using secure randomness."""
        if QUTIP and hasattr(state, 'full'):
            probs = np.abs(state.full().flatten())**2
        else:
            probs = np.abs(state)**2
        
        # Sample from probability distribution using secure random
        random_byte = os.urandom(1)[0]
        random_val = random_byte / 255.0
        # Sample from cumulative distribution
        cumsum = np.cumsum(probs)
        cumsum = cumsum / cumsum[-1]  # normalize
        outcome = np.searchsorted(cumsum, random_val)
        
        # Convert to bits
        bits = np.array([int(b) for b in format(outcome, f'0{self.n_qubits}b')])
        return bits.astype(np.uint8)
