"""FQRNG CLI - Minimal interactive interface with ASCII visualization."""

import sys
import argparse

ASCII_LOGO = """
     *
    / \\
   *   *
  FQRNG
Bell Fractal
  v1.0.0
"""

def format_results_tree(results: dict, entropy: float) -> str:
    """Format NIST results as ASCII tree."""
    lines = ["Results"]
    for test, data in results.items():
        status = "PASS" if data["passed"] else "FAIL"
        lines.append(f"├── {test}: {status} (p={data['p_value']:.3f})")
    lines.append(f"└── Entropy: {entropy:.4f}")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="FQRNG - NIST Quantum RNG")
    parser.add_argument("--bits", type=int, default=1024, help="Bits to generate")
    parser.add_argument("--validate", action="store_true", help="Run NIST validation")
    parser.add_argument("--output", choices=["bits", "int", "float"], default="bits")
    args = parser.parse_args()
    
    print(ASCII_LOGO)
    
    # Import here to show logo first
    try:
        from fqrng.core.qrng_core import QuantumRNG
    except ImportError:
        print("Error: FQRNG not installed. Run: pip install -e .")
        sys.exit(1)
    
    qrng = QuantumRNG(bits=args.bits, validate=args.validate)
    
    print(f"Generating {args.bits} bits...")
    
    if args.validate:
        bits, results, entropy = qrng.generate_bits()
        print(f"Bits: {bits[:10].tolist()}... ({len(bits)} total)")
        print()
        print(format_results_tree(results, entropy))
    else:
        bits = qrng.generate_bits()
        print(f"Bits: {bits[:10].tolist()}... ({len(bits)} total)")
    
    if args.output == "int":
        val = qrng.generate_int(0, 100)
        print(f"Random int [0-100]: {val}")
    elif args.output == "float":
        val = qrng.generate_float(0.0, 1.0)
        print(f"Random float [0-1]: {val:.6f}")

if __name__ == "__main__":
    main()
