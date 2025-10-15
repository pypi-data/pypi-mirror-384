"""Setup script for FQRNG with Cython extensions."""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np
import platform

# Apple Silicon optimizations
extra_compile_args = ["-O3"]
extra_link_args = []
libraries = []

if platform.system() == 'Darwin' and platform.machine() == 'arm64':
    # Apple Silicon (M-series) optimizations
    extra_compile_args.extend([
        "-march=armv8.4-a+simd",  # NEON SIMD support
        "-mcpu=apple-m1",  # Specific to M1/M2, but works for newer
        "-ftree-vectorize",  # Enable vectorization
        "-funsafe-math-optimizations",  # For performance
    ])
    extra_link_args.extend([
        "-framework", "Accelerate"  # Apple vector library
    ])
    libraries.append('m')
else:
    extra_compile_args.append("-march=native")

# CUDA support if available
try:
    import cupy as cp
    # Check if CUDA is actually available
    if cp.cuda.is_available():
        # Add CUDA libraries
        libraries.extend(['cudart', 'cufft'])
        
        # Auto-detect GPU architecture
        device_props = cp.cuda.runtime.getDeviceProperties(0)
        compute_capability = device_props['computeCapabilityMajor'] * 10 + device_props['computeCapabilityMinor']
        
        # Map compute capability to architecture
        arch_map = {
            60: 'sm_60',  # Pascal
            61: 'sm_61',  # Pascal
            70: 'sm_70',  # Volta
            75: 'sm_75',  # Turing
            80: 'sm_80',  # Ampere
            86: 'sm_86',  # Ampere
            89: 'sm_89',  # Ada Lovelace
            90: 'sm_90',  # Hopper
        }
        
        arch = arch_map.get(compute_capability, 'sm_80')  # Default to Ampere
        extra_compile_args.extend([f'-arch={arch}'])
        print(f"CUDA detected: Compute capability {compute_capability}, using {arch}")
    else:
        # Fallback for systems with CuPy but no GPU
        extra_compile_args.extend(['-arch=sm_80'])
        print("CuPy available but no CUDA GPU detected")
        
except (ImportError, RuntimeError) as e:
    print(f"CUDA support disabled: {e}")

extensions = [
    Extension(
        "fqrng.core.qrng_core",
        ["src/fqrng/core/qrng_core.pyx"],
        include_dirs=[np.get_include()],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        libraries=libraries,
    ),
    Extension(
        "fqrng.core.nist_validator",
        ["src/fqrng/core/nist_validator.pyx"],
        include_dirs=[np.get_include()],
        libraries=['m'],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
]

setup(
    ext_modules=cythonize(extensions, language_level="3", compiler_directives={"embedsignature": True}),
)
