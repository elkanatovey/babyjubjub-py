#!/usr/bin/env python3
"""Micro-benchmarks for the Baby JubJub bindings.

Each line reports the best (minimum) per-call time over several repeats, which is the
least noisy estimate on a shared machine. Results depend heavily on the CPU, power
state and build flags; build with `maturin build --release` before measuring.
"""

import random
import timeit

import babyjubjub_py as bjj
from babyjubjub_py import ECPoint

REPEATS = 5


def bench(name, stmt, number):
    best = min(timeit.repeat(stmt, number=number, repeat=REPEATS)) / number
    print(f"{name:42} {best * 1e6:10.2f} µs/op")


def main():
    rng = random.Random(0)
    # Full-width scalars: uniform in [0, l) and at least 250 bits long, which is what
    # secret keys and blinding factors look like in practice.
    scalars = [
        k for k in (rng.randrange(bjj.SUBGROUP_ORDER) for _ in range(64)) if k.bit_length() >= 250
    ]
    k = scalars[0]
    k_str = str(k)

    p1 = ECPoint.from_scalar(scalars[1])
    p2 = ECPoint.from_scalar(scalars[2])
    compressed = p1.to_bytes()
    uncompressed = p1.to_bytes_uncompressed()
    x_hex, y_hex = p1.x_hex(), p1.y_hex()
    data = b"benchmark test data"

    print(f"Baby JubJub Python bindings {bjj.__version__} - micro-benchmarks")
    print(f"scalar bit length: {k.bit_length()}")
    print("-" * 56)

    bench("Point addition (p1 + p2)", lambda: p1 + p2, 20000)
    bench("Point negation", lambda: -p1, 20000)
    bench("Scalar mult, full-width int", lambda: p1.scalar_mult(k), 500)
    bench("Scalar mult, full-width str", lambda: p1.scalar_mult(k_str), 500)
    bench("Scalar mult, small scalar (42)", lambda: p1.scalar_mult(42), 5000)
    bench("from_scalar, full-width", lambda: ECPoint.from_scalar(k), 500)
    bench("Compress (to_bytes)", lambda: p1.to_bytes(), 20000)
    bench("Decompress + subgroup check (from_bytes)", lambda: ECPoint.from_bytes(compressed), 500)
    bench("to_bytes_uncompressed", lambda: p1.to_bytes_uncompressed(), 20000)
    bench("from_bytes_uncompressed (validated)", lambda: ECPoint.from_bytes_uncompressed(uncompressed), 500)
    bench("from_bytes_uncompressed_unchecked", lambda: ECPoint.from_bytes_uncompressed_unchecked(uncompressed), 20000)
    bench("ECPoint(x_hex, y_hex) (validated)", lambda: ECPoint(x_hex, y_hex), 500)
    bench("is_on_curve", lambda: p1.is_on_curve(), 20000)
    bench("hash_to_point", lambda: ECPoint.hash_to_point(data), 2000)
    bench("hash_to_scalar_times_generator (old)", lambda: ECPoint.hash_to_scalar_times_generator(data), 500)
    bench("Equality check", lambda: p1 == p2, 20000)
    bench("hash()", lambda: hash(p1), 20000)


if __name__ == "__main__":
    main()
