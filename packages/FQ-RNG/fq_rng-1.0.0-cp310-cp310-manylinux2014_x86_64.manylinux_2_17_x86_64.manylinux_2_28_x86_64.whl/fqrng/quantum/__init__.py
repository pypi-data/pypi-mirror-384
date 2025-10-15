"""Quantum layer initialization - modular quantum simulation (arxiv.org/abs/2201.09866)."""

try:
    import qutip as qt
    QUTIP_AVAILABLE = True
except ImportError:
    qt = None
    QUTIP_AVAILABLE = False

def init_qutip():
    """Initialize and return qutip module."""
    return qt

# Import GPU manager
from .gpu_manager import get_gpu_manager, GPUManager
