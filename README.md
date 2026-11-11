# Baby JubJub Python Bindings

Python bindings for the Baby JubJub elliptic curve, implemented in Rust on top of
[babyjubjub-rs](https://github.com/arnaucube/babyjubjub-rs).

## Research Prototype Warning

**This library is a research prototype and should NOT be used in production systems.**

- No security audit has been performed.
- **Scalar multiplication is not constant-time.** It walks the bits of the scalar with
  data-dependent additions, so its running time leaks information about the scalar. Do
  not use it with secret scalars where an attacker can measure timing.
- `hash_to_point` uses try-and-increment (see below). Its outputs have no known discrete
  logarithm with respect to the generator, but it is not an RFC 9380 hash-to-curve, it is
  not constant-time, and it has not been reviewed.
- `from_bytes_uncompressed_unchecked` (and unpickling) skip all point validation and must
  only be used on data you already trust.

## Changes in 0.2.0 (breaking)

- **`hash_to_point` outputs changed.** Up to 0.1.1 it returned `(SHA-256(data) mod n) * G`,
  so the discrete log of every output with respect to `G` was public, which breaks any
  protocol that needs independent generators (Pedersen commitments, etc.). It now uses a
  try-and-increment construction with an unknown discrete log. The old behaviour is still
  available as `ECPoint.hash_to_scalar_times_generator`.
- **Negative scalars are now correct.** Previously the sign was silently dropped, so
  `from_scalar("-1")` returned `G` instead of `-G`. Scalars are now reduced into range
  before multiplying (see [Scalars](#scalars)).
- **Constructors validate points.** `ECPoint(x, y)`, `from_bytes` and
  `from_bytes_uncompressed` now raise `ValueError` for points that are off the curve, not
  in the prime-order subgroup, or have non-canonical coordinates (>= the field modulus).
  `from_bytes_uncompressed_unchecked` is the explicit fast path (see
  [Validation](#validation-and-the-unchecked-fast-path)).
- **Constants are `int`s and correctly named.** `CURVE_ORDER` (previously a `str`) is the
  order of the full curve group, `8 * l`; it was documented as the subgroup order. The
  prime subgroup order is now `SUBGROUP_ORDER`. `COFACTOR` and `FIELD_MODULUS` were added.
- Scalars may be Python `int`s as well as decimal / `0x`-hex strings.
- New operators: `+`, `-`, unary `-`, `int * point`, `point * int`. Points are hashable and
  picklable.
- The identity point now round-trips through `to_bytes` / `from_bytes` (decompression
  previously failed for it).

## Features

- Point addition, negation, subtraction and scalar multiplication
- Compressed (32-byte, circomlib-compatible) and uncompressed (64-byte) serialization
- Point validation (on-curve and prime-order subgroup checks)
- Hashing to the curve
- The GIL is released during scalar multiplication, point validation and hashing, so
  these can run in parallel from several Python threads
- Linux, macOS and Windows; Python 3.10+

## Installation

```bash
pip install babyjubjub-py
```

### From source

```bash
git clone https://github.com/elkanatovey/babyjubjub-py.git
cd babyjubjub-py
pip install maturin
maturin develop --release
```

## Quick Start

```python
import babyjubjub_py as bjj
from babyjubjub_py import ECPoint

G = ECPoint.generator()

# Scalar multiplication: int or str scalars
P = ECPoint.from_scalar(123)          # 123 * G
Q = 456 * G                           # same as G.scalar_mult(456)
assert ECPoint.from_scalar("-1") == -G

# Group operations
R = P + Q
assert R - Q == P
assert (bjj.SUBGROUP_ORDER * G).is_infinity()

# Hash to a point with unknown discrete log
H = ECPoint.hash_to_point(b"my-protocol/generator-H")

# Pedersen-style commitment
C = 42 * G + 7 * H

# Serialization
assert ECPoint.from_bytes(P.to_bytes()) == P
```

## Scalars

Every method that takes a scalar accepts a Python `int` or a `str` holding a decimal or
`0x`-hex integer, optionally with a leading `-`.

- `from_scalar(k)` reduces `k` modulo `SUBGROUP_ORDER` (the order of `G`).
- `scalar_mult(k)`, `k * P` and `P * k` reduce `k` modulo `CURVE_ORDER` (`8 * l`). For
  points in the prime-order subgroup (every validated point) this gives the same result as
  reducing modulo `l`, and it stays correct for any on-curve point that came through the
  unchecked path, whose order may be a multiple of `l`.

## Validation and the unchecked fast path

`ECPoint(x_hex, y_hex)`, `from_bytes` and `from_bytes_uncompressed` check that

1. each coordinate is a canonical field element (< `FIELD_MODULUS`),
2. the point is on the curve: `168700*x^2 + y^2 == 1 + 168696*x^2*y^2 (mod p)`, and
3. the point is in the prime-order subgroup: `SUBGROUP_ORDER * P` is the identity.

The subgroup check is a full scalar multiplication, so validated decoding costs tens of
microseconds instead of a fraction of a microsecond. When you move points you created
yourself between processes (for example through `multiprocessing`), use the unchecked
pair:

```python
data = P.to_bytes_uncompressed()                       # 64 bytes: x || y, little-endian
P2 = ECPoint.from_bytes_uncompressed_unchecked(data)   # length and range checks only
```

`from_bytes_uncompressed_unchecked` only checks the length and that both coordinates are
below the field modulus. It will happily build points that are off the curve or outside
the subgroup, and the group operations give meaningless results on such points. Validate
data at the trust boundary (or call `P.is_in_subgroup()` once) and use the unchecked path
only after that. Pickling uses the unchecked path too, which is consistent with pickle
already being unsafe on untrusted input.

## Hashing to the curve

`ECPoint.hash_to_point(data)` uses try-and-increment with domain separation:

1. For `counter = 0, 1, 2, ...` compute
   `h = SHA-256(len(DST) || DST || data || counter)`, where
   `DST = b"babyjubjub-py/v1/hash_to_point/SHA-256/try-and-increment"`, `len(DST)` is one
   byte and `counter` is 4 bytes big-endian.
2. Read `h` as a little-endian 256-bit integer. Bit 255 is the sign of `x`; bits 0..253
   are a candidate `y`. Skip the candidate if `y >= FIELD_MODULUS` or no `x` satisfies the
   curve equation.
3. Multiply the decompressed point by the cofactor 8 and return it unless it is the
   identity.

It is deterministic, its outputs lie in the prime-order subgroup, and nobody knows their
discrete log with respect to `G` (assuming SHA-256 behaves like a random oracle). On
average it takes fewer than three attempts. It is not constant-time, so the running time
depends on the input.

## API Reference

### `ECPoint` class

Constructors (static methods):

- `ECPoint(x_hex: str, y_hex: str)`: from hex coordinates, validated
- `ECPoint.generator()`: the generator `B8` of the prime-order subgroup
- `ECPoint.infinity()`: the identity point `(0, 1)`
- `ECPoint.from_scalar(scalar: int | str)`: `scalar * G`
- `ECPoint.from_bytes(data: bytes)`: decode 32 compressed bytes, validated
- `ECPoint.from_bytes_uncompressed(data: bytes)`: decode 64 bytes, validated
- `ECPoint.from_bytes_uncompressed_unchecked(data: bytes)`: decode 64 bytes, not validated
- `ECPoint.hash_to_point(data: bytes)`: hash to a point with unknown discrete log
- `ECPoint.hash_to_scalar_times_generator(data: bytes)`: the pre-0.2.0 `hash_to_point`,
  `(SHA-256(data) mod l) * G`; its discrete log is public

`from_bytes*` also accept `bytearray` or a list of ints.

Methods:

- `add(other) -> ECPoint`, `sub(other) -> ECPoint`, `neg() -> ECPoint`
- `scalar_mult(scalar: int | str) -> ECPoint`
- `is_infinity() -> bool`
- `is_on_curve() -> bool`
- `is_in_subgroup() -> bool`: on the curve and `SUBGROUP_ORDER * self` is the identity
- `x_hex() -> str`, `y_hex() -> str`: `0x`-prefixed, 64 hex digits
- `to_bytes() -> bytes`: 32-byte compressed form (little-endian `y`, top bit is the sign
  of `x`), compatible with circomlib and babyjubjub-rs
- `to_bytes_uncompressed() -> bytes`: 64 bytes, little-endian `x` then little-endian `y`

Operators: `P + Q`, `P - Q`, `-P`, `k * P`, `P * k` (`k` an `int`), `P == Q`, `P != Q`,
`hash(P)`. Comparing with a non-`ECPoint` returns `NotImplemented` (so `P == 5` is
`False`). Points are immutable, hashable, and support `pickle` and `copy`.

### Module constants

All are Python `int`s except where noted.

- `__version__` (`str`): library version
- `CURVE_NAME` (`str`): `"Baby JubJub"`
- `FIELD_MODULUS`: `p`, the BN254 scalar field modulus
- `SUBGROUP_ORDER`: `l`, the prime order of `G`
- `COFACTOR`: `8`
- `CURVE_ORDER`: `COFACTOR * SUBGROUP_ORDER`, the order of the full curve group

## Baby JubJub Curve Details

- **Curve equation**: `a*x^2 + y^2 = 1 + d*x^2*y^2` (twisted Edwards), `a = 168700`,
  `d = 168696`
- **Base field**: BN254 scalar field,
  `p = 21888242871839275222246405745257275088548364400416034343698204186575808495617`
- **Prime subgroup order**:
  `l = 2736030358979909402780800718157159386076813972158567259200215660948447373041`
- **Cofactor**: 8
- **Full group order**: `8 * l = 21888242871839275222246405745257275088614511777268538073601725287587578984328`
- **Generator**: `B8` (circomlib's `Base8`), which generates the subgroup of order `l`

## Performance

`benchmark.py` reports the best per-call time over several runs. The numbers below are
from one x86-64 Linux machine (WSL2, Python 3.10, release build) and are only indicative;
run the script on your own hardware.

```
Point addition                              1.80 µs
Point negation                              0.05 µs
Scalar mult, full-width (~251-bit) scalar  76    µs
Scalar mult, small scalar (42)              3.5  µs
Compress (to_bytes)                         0.07 µs
Decompress + validation (from_bytes)       96    µs
to_bytes_uncompressed                       0.06 µs
from_bytes_uncompressed (validated)        76    µs
from_bytes_uncompressed_unchecked           0.11 µs
hash_to_point                              21    µs
```

Scalar multiplication time grows with the bit length of the scalar, so always benchmark
with full-width scalars. Validation is dominated by the subgroup check, which is one
full-width scalar multiplication.

## Development

### Requirements

- Rust 1.74+ (install via [rustup](https://rustup.rs/))
- Python 3.10+
- Maturin

### Building and testing

```bash
maturin develop --release    # build and install into the active virtualenv
pytest tests/ -v             # run the test suite
cargo fmt -- --check         # formatting (enforced in CI)
cargo clippy -- -D warnings  # lints (enforced in CI)
python benchmark.py          # micro-benchmarks
```

The tests cross-check the bindings against known-answer vectors from babyjubjub-rs and
circomlib and against a slow pure-Python reference implementation in
`tests/reference.py`.

### Project Structure

```
babyjubjub-py/
├── Cargo.toml          # Rust dependencies; the single source of the version number
├── pyproject.toml      # Python packaging (version taken from Cargo.toml)
├── src/
│   └── lib.rs          # PyO3 bindings
├── tests/
│   ├── reference.py    # pure-Python reference implementation used by the tests
│   ├── test_operations.py
│   └── test_security.py
├── benchmark.py
└── README.md
```

## License

Apache-2.0 (same as babyjubjub-rs)

## Credits

- Built on [babyjubjub-rs](https://github.com/arnaucube/babyjubjub-rs) by arnaucube
- Uses [PyO3](https://pyo3.rs/) for Python bindings

## Alternatives

- **Pure Python**: [pybabyjubjub](https://github.com/HarryR/ethsnarks-pybabyjubjub)
- **Rust**: use [babyjubjub-rs](https://github.com/arnaucube/babyjubjub-rs) directly

## Troubleshooting

### Import Error

```python
ImportError: cannot import name 'ECPoint' from 'babyjubjub_py'
```

**Solution**: Rebuild the library with `maturin develop --release`

### Performance Issues

If operations are slow:
1. Make sure you built with `--release`
2. Use `from_bytes_uncompressed_unchecked` for trusted points in hot loops; validated
   decoding performs a full scalar multiplication per call

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

**Status**: Research prototype. Not for production use; see the warning at the top of
this README.
