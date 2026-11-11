"""Slow, independent pure-Python Baby JubJub reference used to cross-check the bindings.

Nothing here calls into babyjubjub_py. Points are (x, y) tuples of ints.
"""

import hashlib

P = 21888242871839275222246405745257275088548364400416034343698204186575808495617
L = 2736030358979909402780800718157159386076813972158567259200215660948447373041
A = 168700
D = 168696
IDENTITY = (0, 1)

# Generator of the prime-order subgroup (circomlib "Base8").
B8 = (
    5299619240641551281634865583518297030282874472190772894086521144482721001553,
    16950150798460657717958625567821834550301663161624707787222815936182638968203,
)
# circomlib "Generator": generates the full group of order 8*L, and 8*G0 == B8.
G0 = (
    995203441582195749578291179787384436505546430278305826713579947235728471134,
    5472060717959818805561601436314318772137091100104008585924551046643952123905,
)

HASH_TO_POINT_DST = b"babyjubjub-py/v1/hash_to_point/SHA-256/try-and-increment"


def on_curve(pt):
    x, y = pt
    return (A * x * x + y * y - 1 - D * x * x * y * y) % P == 0


def add(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    t = D * x1 * x2 * y1 * y2 % P
    x3 = (x1 * y2 + y1 * x2) * pow(1 + t, -1, P) % P
    y3 = (y1 * y2 - A * x1 * x2) * pow(1 - t, -1, P) % P
    return (x3, y3)


def neg(pt):
    return ((-pt[0]) % P, pt[1])


def mul(k, pt):
    """k * pt for k >= 0 by double-and-add."""
    assert k >= 0
    result = IDENTITY
    while k:
        if k & 1:
            result = add(result, pt)
        pt = add(pt, pt)
        k >>= 1
    return result


def sqrt(a):
    """A square root of a mod P (Tonelli-Shanks), or None."""
    a %= P
    if a == 0:
        return 0
    if pow(a, (P - 1) // 2, P) != 1:
        return None
    q, s = P - 1, 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = 2
    while pow(z, (P - 1) // 2, P) != P - 1:
        z += 1
    m, c, t, r = s, pow(z, q, P), pow(a, q, P), pow(a, (q + 1) // 2, P)
    while t != 1:
        i, t2 = 0, t
        while t2 != 1:
            t2 = t2 * t2 % P
            i += 1
        b = pow(c, 1 << (m - i - 1), P)
        m, c, t, r = i, b * b % P, t * b * b % P, r * b % P
    return r


def compress(pt):
    x, y = pt
    out = bytearray(y.to_bytes(32, "little"))
    if x > (P - 1) // 2:
        out[31] |= 0x80
    return bytes(out)


def recover_x(y, negative):
    x2 = (1 - y * y) * pow(A - D * y * y, -1, P) % P
    x = sqrt(x2)
    if x is None or (x == 0 and negative):
        return None
    if (x > (P - 1) // 2) != negative:
        x = (-x) % P
    return x


def hash_to_point(data):
    """Same construction as ECPoint.hash_to_point, written independently."""
    for counter in range(256):
        digest = hashlib.sha256(
            bytes([len(HASH_TO_POINT_DST)])
            + HASH_TO_POINT_DST
            + data
            + counter.to_bytes(4, "big")
        ).digest()
        value = int.from_bytes(digest, "little")
        negative = bool(value >> 255)
        y = value & ((1 << 254) - 1)
        if y >= P:
            continue
        x = recover_x(y, negative)
        if x is None:
            continue
        pt = mul(8, (x, y))
        if pt != IDENTITY:
            return pt
    raise AssertionError("unreachable")
