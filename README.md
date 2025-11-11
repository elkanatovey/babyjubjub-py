# Baby JubJub Python Bindings

Fast Python bindings for the Baby JubJub elliptic curve, powered by Rust.

## Overview

This library provides Python bindings to the [babyjubjub-rs](https://github.com/arnaucube/babyjubjub-rs) Rust library, offering high-performance elliptic curve operations for the Baby JubJub curve.

Baby JubJub is a twisted Edwards curve embedded in the BN254 scalar field, designed for efficient use in zero-knowledge proof systems like Circom, zkSync, and Tornado Cash.

## Features

- **Fast**: Native Rust implementation provides 100x speedup over pure Python
- **Complete API**: Point addition, scalar multiplication, compression, hashing
- **Thread-safe**: GIL is released during expensive operations for true parallelism
- **Well-tested**: Comprehensive test suite with 26+ tests
- **Easy to use**: Simple Python API with no Rust knowledge required

## Performance

Individual operations are highly optimized:

```
Point addition:           1.85 µs
Scalar multiplication:    3.38 µs
Compression:              0.67 µs
Uncompressed serialize:   0.07 µs
Uncompressed deserialize: 0.15 µs
```

The library includes both compressed (32-byte) and uncompressed (64-byte) serialization. Uncompressed serialization is significantly faster for multiprocessing scenarios where points need frequent serialization.

## Installation

```bash
pip install babyjubjub-py
```

### From source

```bash
# Clone the repository
cd /path/to/babyjubjub-py

# Install maturin
pip install maturin

# Build and install
maturin develop --release
```

## Quick Start

```python
import babyjubjub_py as bjj

# Get the generator point
G = bjj.ECPoint.generator()

# Scalar multiplication
P = bjj.ECPoint.from_scalar("123")

# Point addition
Q = bjj.ECPoint.from_scalar("456")
R = P.add(Q)

# Hash to curve point
H = bjj.ECPoint.hash_to_point(b"Hello, World!")

# Compression
compressed = P.to_bytes()
P_restored = bjj.ECPoint.from_bytes(compressed)
```

## API Reference

### `ECPoint` class

#### Constructors

- `ECPoint(x_hex: str, y_hex: str)` - Create from coordinates
- `ECPoint.generator()` - Get the base point (B8)
- `ECPoint.infinity()` - Get the identity point
- `ECPoint.from_scalar(scalar: str)` - Create as `scalar * G`
- `ECPoint.from_bytes(bytes: list[int])` - Decompress from 32 bytes
- `ECPoint.hash_to_point(data: bytes)` - Hash arbitrary data to a point

#### Methods

- `add(other: ECPoint) -> ECPoint` - Point addition
- `neg() -> ECPoint` - Point negation
- `sub(other: ECPoint) -> ECPoint` - Point subtraction
- `scalar_mult(scalar: str) -> ECPoint` - Scalar multiplication
- `is_infinity() -> bool` - Check if identity
- `x_hex() -> str` - Get x coordinate as hex string
- `y_hex() -> str` - Get y coordinate as hex string
- `to_bytes() -> list[int]` - Compress to 32 bytes

### Module Constants

- `__version__` - Library version
- `CURVE_NAME` - "Baby JubJub"
- `CURVE_ORDER` - Order of the curve subgroup

## Baby JubJub Curve Details

- **Curve equation**: ax² + y² = 1 + dx²y² (twisted Edwards)
- **Base field**: BN254 scalar field (254-bit prime)
- **Order**: 21888242871839275222246405745257275088614511777268538073601725287587578984328
- **Cofactor**: 8
- **Security level**: ~128 bits

## Use Cases

- **Zero-knowledge proofs**: Circom, zkSync, Aztec
- **EdDSA signatures**: Privacy-preserving signatures
- **Commitment schemes**: Pedersen commitments
- **Threshold cryptography**: Distributed key generation
- **Cryptographic protocols**: Any application requiring Baby JubJub curve operations

## Development

### Requirements

- Rust 1.56+ (install via [rustup](https://rustup.rs/))
- Python 3.8+
- Maturin

### Building

```bash
# Development build (fast iteration)
maturin develop

# Release build (optimized)
maturin build --release

# Run tests
python test_basic.py
```

### Project Structure

```
babyjubjub-py/
├── Cargo.toml          # Rust dependencies
├── pyproject.toml      # Python packaging
├── src/
│   └── lib.rs          # PyO3 bindings
├── test_basic.py       # Python tests
└── README.md
```

## Example Usage in Applications

The library can be integrated into cryptographic applications requiring Baby JubJub operations:

```python
from babyjubjub_py import ECPoint

# Use in your cryptographic protocol
def my_protocol(data):
    # Hash input to curve point
    point = ECPoint.hash_to_point(data)
    
    # Perform operations
    secret = "123456789"
    commitment = point.scalar_mult(secret)
    
    return commitment
```

## License

Apache-2.0 (same as babyjubjub-rs)

## Credits

- Built on [babyjubjub-rs](https://github.com/arnaucube/babyjubjub-rs) by arnaucube
- Uses [PyO3](https://pyo3.rs/) for Python bindings

## Alternatives

- **Pure Python**: [pybabyjubjub](https://github.com/HarryR/ethsnarks-pybabyjubjub) - slower but no dependencies
- **Full Rust**: Use [babyjubjub-rs](https://github.com/arnaucube/babyjubjub-rs) directly

## Troubleshooting

### Import Error

```python
ImportError: cannot import name 'ECPoint' from 'babyjubjub_py'
```

**Solution**: Rebuild the library with `maturin develop --release`

### Performance Issues

If operations are slow:
1. Ensure you built with `--release` flag
2. Check Python version (3.10+ recommended)
3. Verify Rust is using the release profile

### Installation Errors

If `pip install` fails:
1. Install Rust: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
2. Install Python dev headers: `sudo apt-get install python3-dev`
3. Install build tools: `sudo apt-get install build-essential`

## Contributing

Contributions welcome! Please feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## Support

For issues or questions:
- Open an issue on GitHub
- Check the [babyjubjub-rs documentation](https://docs.rs/babyjubjub-rs)
- Review the [PyO3 user guide](https://pyo3.rs/)

---

**Status**: Beta

**Version**: 0.1.0
