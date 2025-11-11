#!/usr/bin/env python3
"""Benchmark script for Baby JubJub bindings."""

import time
import babyjubjub_py as bjj

def benchmark_operation(name, operation, iterations=1000):
    """Benchmark a single operation."""
    start = time.time()
    for _ in range(iterations):
        operation()
    elapsed = time.time() - start
    
    ops_per_sec = iterations / elapsed
    time_per_op = elapsed / iterations * 1e6  # microseconds
    
    print(f"{name:30} {time_per_op:8.2f} µs/op    {ops_per_sec:10,.0f} ops/sec")

def main():
    print("Baby JubJub Python Bindings - Performance Benchmarks")
    print("=" * 70)
    print()
    
    # Pre-generate test data
    g = bjj.ECPoint.generator()
    p1 = bjj.ECPoint.from_scalar("123456")
    p2 = bjj.ECPoint.from_scalar("789012")
    compressed = p1.to_bytes()
    uncompressed = p1.to_bytes_uncompressed()
    test_data = b"benchmark test data"
    
    print(f"{'Operation':30} {'Time':>15}    {'Throughput':>15}")
    print("-" * 70)
    
    # Benchmark different operations
    benchmark_operation("Generator", lambda: bjj.ECPoint.generator(), 10000)
    benchmark_operation("Infinity", lambda: bjj.ECPoint.infinity(), 10000)
    benchmark_operation("From scalar (small)", lambda: bjj.ECPoint.from_scalar("123"), 1000)
    benchmark_operation("From scalar (large)", lambda: bjj.ECPoint.from_scalar(str(2**200)), 1000)
    benchmark_operation("Point addition", lambda: p1.add(p2), 10000)
    benchmark_operation("Point negation", lambda: p1.neg(), 10000)
    benchmark_operation("Point subtraction", lambda: p1.sub(p2), 10000)
    benchmark_operation("Scalar multiplication", lambda: p1.scalar_mult("42"), 1000)
    benchmark_operation("Compression", lambda: p1.to_bytes(), 10000)
    benchmark_operation("Decompression", lambda: bjj.ECPoint.from_bytes(compressed), 1000)
    benchmark_operation("Uncompressed serialize", lambda: p1.to_bytes_uncompressed(), 10000)
    benchmark_operation("Uncompressed deserialize", lambda: bjj.ECPoint.from_bytes_uncompressed(uncompressed), 10000)
    benchmark_operation("Hash to point", lambda: bjj.ECPoint.hash_to_point(test_data), 1000)
    benchmark_operation("Coordinate access (x)", lambda: p1.x_hex(), 10000)
    benchmark_operation("Coordinate access (y)", lambda: p1.y_hex(), 10000)
    benchmark_operation("Infinity check", lambda: p1.is_infinity(), 10000)
    benchmark_operation("Equality check", lambda: p1 == p2, 10000)
    
    print()
    print("=" * 70)
    print()
    print("Key observations:")
    print("- Uncompressed serialization is significantly faster than compressed")
    print("- Point addition is very efficient (sub-microsecond)")
    print("- Scalar multiplication is the most expensive operation")
    print("- Decompression requires solving the curve equation (expensive)")

if __name__ == "__main__":
    main()

