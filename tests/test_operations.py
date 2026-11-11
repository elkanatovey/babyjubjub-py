"""Group law, operators, scalars, serialization and module metadata."""

import copy
import importlib.metadata
import pickle
import random

import pytest

import babyjubjub_py as bjj
from babyjubjub_py import ECPoint

from . import reference as ref

L = ref.L
G = ECPoint.generator()


def point(k):
    return ECPoint.from_scalar(k)


def coords(pt):
    return (int(pt.x_hex(), 16), int(pt.y_hex(), 16))


class TestGroupLaw:
    def test_generator(self):
        assert coords(G) == ref.B8
        assert not G.is_infinity()
        assert G.is_on_curve()
        assert G.is_in_subgroup()

    def test_infinity(self):
        inf = ECPoint.infinity()
        assert inf.is_infinity()
        assert coords(inf) == (0, 1)
        assert inf.is_in_subgroup()

    def test_one_and_two(self):
        assert point(1) == G
        assert point(2) == G.add(G)

    def test_associativity(self):
        p, q, r = point(123), point(456), point(789)
        assert p.add(q).add(r) == p.add(q.add(r))

    def test_commutativity(self):
        p, q = point(123), point(456)
        assert p.add(q) == q.add(p)

    def test_negation(self):
        p = point(123)
        assert p.add(p.neg()).is_infinity()
        assert p.neg().neg() == p
        assert ECPoint.infinity().neg() == ECPoint.infinity()

    def test_subtraction(self):
        p, q = point(123), point(456)
        assert p.sub(q) == p.add(q.neg())
        assert p.sub(p).is_infinity()

    def test_identity_element(self):
        p = point(123)
        assert p.add(ECPoint.infinity()) == p
        assert ECPoint.infinity().add(p) == p

    def test_distributivity(self):
        assert point(123 + 456) == point(123).add(point(456))
        p = point(98765)
        assert p.scalar_mult(7).add(p.scalar_mult(11)) == p.scalar_mult(18)

    def test_matches_reference_on_random_scalars(self):
        rng = random.Random(1234)
        for _ in range(5):
            k = rng.randrange(L)
            assert coords(point(k)) == ref.mul(k, ref.B8)


class TestScalars:
    def test_negative_one(self):
        assert point(-1) == G.neg()
        assert point("-1") == G.neg()
        assert G.scalar_mult(-1) == G.neg()
        assert G.scalar_mult("-1") == G.neg()

    def test_negative_scalars(self):
        for k in [2, 5, 123456789, L - 1, L + 3, 2**300]:
            assert point(-k) == point(k).neg()
            assert point(str(-k)) == point(k).neg()
            p = point(77)
            assert p.scalar_mult(-k) == p.scalar_mult(k).neg()

    def test_subgroup_order(self):
        assert point(L).is_infinity()
        assert point(str(L)).is_infinity()
        assert G.scalar_mult(L).is_infinity()
        assert point(L + 5) == point(5)
        assert point(-L).is_infinity()

    def test_zero(self):
        assert point(0).is_infinity()
        assert point("0").is_infinity()
        assert G.scalar_mult(0).is_infinity()

    def test_large_scalar(self):
        k = 2**256 - 1
        assert point(k) == point(k % L)
        assert not point(k).is_infinity()

    def test_int_and_str_agree(self):
        for k in [1, 42, 2**200 + 17, L - 1]:
            assert point(k) == point(str(k)) == point(hex(k))
            assert G.scalar_mult(k) == G.scalar_mult(str(k))

    def test_hex_strings(self):
        assert point("0x10") == point(16)
        assert point("0X10") == point(16)
        assert point("-0x10") == point(-16)
        assert point("+16") == point(16)

    def test_invalid_scalars(self):
        for bad in ["", "abc", "0x", "1.5", "0xzz", "--1", " 1"]:
            with pytest.raises(ValueError):
                point(bad)
        for bad in [1.5, None, b"1", [1]]:
            with pytest.raises(TypeError):
                point(bad)
            with pytest.raises(TypeError):
                G.scalar_mult(bad)


class TestOperators:
    def test_add_sub_neg(self):
        p, q = point(123), point(456)
        assert p + q == p.add(q)
        assert p - q == p.sub(q)
        assert -p == p.neg()

    def test_mul(self):
        p = point(123)
        assert 5 * p == p.scalar_mult(5)
        assert p * 5 == p.scalar_mult(5)
        assert -3 * p == p.scalar_mult(3).neg()
        assert L * p == ECPoint.infinity()
        assert 3 * G == G + G + G

    def test_unsupported_operands(self):
        with pytest.raises(TypeError):
            G + 1
        with pytest.raises(TypeError):
            G - 1
        with pytest.raises(TypeError):
            G * 1.5
        with pytest.raises(TypeError):
            G * G
        with pytest.raises(TypeError):
            G * "5"

    def test_equality_with_other_types(self):
        assert G.__eq__(5) is NotImplemented
        assert not (G == 5)
        assert G != 5
        assert G != "G"
        assert G != None  # noqa: E711

    def test_equality(self):
        assert point(123) == point(123)
        assert point(123) != point(456)
        assert not (point(123) != point(123))

    def test_hash(self):
        assert hash(point(123)) == hash(point(123))
        assert hash(ECPoint.infinity()) == hash(point(0))
        points = {point(1), G, point(2), G + G, -G}
        assert len(points) == 3
        lookup = {G: "g"}
        assert lookup[point(1)] == "g"


class TestSerialization:
    def test_compressed_roundtrip(self):
        p = point(123456789)
        data = p.to_bytes()
        assert isinstance(data, bytes)
        assert len(data) == 32
        assert ECPoint.from_bytes(data) == p

    def test_compressed_matches_reference(self):
        rng = random.Random(99)
        for _ in range(5):
            k = rng.randrange(L)
            assert point(k).to_bytes() == ref.compress(ref.mul(k, ref.B8))
            assert point(-k).to_bytes() == ref.compress(ref.neg(ref.mul(k, ref.B8)))

    def test_compressed_accepts_bytes_like(self):
        data = G.to_bytes()
        assert ECPoint.from_bytes(bytearray(data)) == G
        assert ECPoint.from_bytes(list(data)) == G

    def test_identity_compressed_roundtrip(self):
        inf = ECPoint.infinity()
        data = inf.to_bytes()
        assert data == b"\x01" + bytes(31)
        assert ECPoint.from_bytes(data).is_infinity()

    def test_uncompressed_roundtrip(self):
        p = point(987654321)
        data = p.to_bytes_uncompressed()
        assert isinstance(data, bytes)
        assert len(data) == 64
        x, y = coords(p)
        assert data == x.to_bytes(32, "little") + y.to_bytes(32, "little")
        assert ECPoint.from_bytes_uncompressed(data) == p
        assert ECPoint.from_bytes_uncompressed_unchecked(data) == p

    def test_identity_uncompressed_roundtrip(self):
        data = ECPoint.infinity().to_bytes_uncompressed()
        assert ECPoint.from_bytes_uncompressed(data).is_infinity()
        assert ECPoint.from_bytes_uncompressed_unchecked(data).is_infinity()

    def test_wrong_lengths(self):
        with pytest.raises(ValueError):
            ECPoint.from_bytes(bytes(31))
        with pytest.raises(ValueError):
            ECPoint.from_bytes_uncompressed(bytes(63))
        with pytest.raises(ValueError):
            ECPoint.from_bytes_uncompressed_unchecked(bytes(65))

    def test_hex_coordinates_roundtrip(self):
        p = point(31337)
        assert p.x_hex().startswith("0x") and len(p.x_hex()) == 66
        assert ECPoint(p.x_hex(), p.y_hex()) == p
        assert ECPoint(p.x_hex()[2:], p.y_hex()[2:]) == p
        assert repr(p) == f"ECPoint(x={p.x_hex()}, y={p.y_hex()})"

    @pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
    def test_pickle(self, protocol):
        for p in [G, point(-5), ECPoint.infinity(), ECPoint.hash_to_point(b"x")]:
            restored = pickle.loads(pickle.dumps(p, protocol=protocol))
            assert isinstance(restored, ECPoint)
            assert restored == p

    def test_pickle_list(self):
        points = [point(k) for k in range(10)]
        assert pickle.loads(pickle.dumps(points)) == points

    def test_copy(self):
        p = point(42)
        assert copy.copy(p) == p
        assert copy.deepcopy(p) == p


class TestModuleMetadata:
    def test_version(self):
        assert isinstance(bjj.__version__, str)
        assert bjj.__version__ == importlib.metadata.version("babyjubjub-py")

    def test_curve_name(self):
        assert bjj.CURVE_NAME == "Baby JubJub"

    def test_orders(self):
        for name in ["FIELD_MODULUS", "SUBGROUP_ORDER", "CURVE_ORDER", "COFACTOR"]:
            assert type(getattr(bjj, name)) is int
        assert bjj.FIELD_MODULUS == ref.P
        assert bjj.SUBGROUP_ORDER == ref.L
        assert bjj.COFACTOR == 8
        assert bjj.CURVE_ORDER == 8 * ref.L
        assert (
            bjj.CURVE_ORDER
            == 21888242871839275222246405745257275088614511777268538073601725287587578984328
        )
