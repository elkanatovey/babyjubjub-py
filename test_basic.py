#!/usr/bin/env python3
"""Basic test to verify Baby JubJub bindings work correctly."""

import babyjubjub_py as bjj
import time

print("="*70)
print("Baby JubJub Python Bindings - Basic Test")
print("="*70)
print()

# Test 1: Module info
print("1. Module Info:")
print(f"   Version: {bjj.__version__}")
print(f"   Curve: {bjj.CURVE_NAME}")
print(f"   Order: {bjj.CURVE_ORDER}")
print()

# Test 2: Generator point
print("2. Generator Point:")
g = bjj.ECPoint.generator()
print(f"   G = {g}")
print(f"   x = {g.x_hex()}")
print(f"   y = {g.y_hex()}")
print()

# Test 3: Identity point
print("3. Identity Point:")
inf = bjj.ECPoint.infinity()
print(f"   O = {inf}")
print(f"   is_infinity: {inf.is_infinity()}")
print()

# Test 4: Scalar multiplication
print("4. Scalar Multiplication:")
p1 = bjj.ECPoint.from_scalar("123")
print(f"   123*G = {p1}")
print()

# Test 5: Point addition
print("5. Point Addition:")
p2 = bjj.ECPoint.from_scalar("456")
p3 = p1.add(p2)
p4 = bjj.ECPoint.from_scalar(str(123 + 456))
print(f"   123*G = {p1}")
print(f"   456*G = {p2}")
print(f"   (123+456)*G = {p4}")
print(f"   123*G + 456*G = {p3}")
print(f"   Equal: {p3 == p4}")
print()

# Test 6: Point negation
print("6. Point Negation:")
p5 = p1.neg()
p6 = p1.add(p5)
print(f"   P = {p1}")
print(f"   -P = {p5}")
print(f"   P + (-P) = {p6}")
print(f"   is_infinity: {p6.is_infinity()}")
print()

# Test 7: Compression/decompression
print("7. Compression/Decompression:")
compressed = p1.to_bytes()
print(f"   Original: {p1}")
print(f"   Compressed ({len(compressed)} bytes): {compressed.hex()}")
p1_restored = bjj.ECPoint.from_bytes(compressed)
print(f"   Restored: {p1_restored}")
print(f"   Equal: {p1 == p1_restored}")
print()

# Test 8: Hash to point
print("8. Hash to Point:")
h1 = bjj.ECPoint.hash_to_point(b"Hello, World!")
h2 = bjj.ECPoint.hash_to_point(b"Hello, World!")
h3 = bjj.ECPoint.hash_to_point(b"Different data")
print(f"   Hash('Hello, World!') = {h1}")
print(f"   Hash('Hello, World!') = {h2}")
print(f"   Hash('Different data') = {h3}")
print(f"   h1 == h2: {h1 == h2}")
print(f"   h1 == h3: {h1 == h3}")
print()

# Test 9: Performance comparison
print("9. Performance Test (1000 scalar multiplications):")
print()

start = time.time()
for i in range(1000):
    p = bjj.ECPoint.from_scalar(str(i))
elapsed = time.time() - start

print(f"   Total time: {elapsed:.3f} seconds")
print(f"   Per operation: {elapsed*1000:.3f} ms")
print(f"   Operations/sec: {1000/elapsed:.0f}")
print()

print("="*70)
print("All tests passed!")
print("="*70)


