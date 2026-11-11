"""Known-answer vectors, point validation and hashing to the curve."""

import hashlib
import random

import pytest

from babyjubjub_py import ECPoint

from . import reference as ref

L = ref.L
G = ECPoint.generator()


def from_ints(x, y):
    return ECPoint(hex(x), hex(y))


def coords(pt):
    return (int(pt.x_hex(), 16), int(pt.y_hex(), 16))


def unchecked(pt):
    """Build an ECPoint from reference coordinates without validation."""
    x, y = pt
    return ECPoint.from_bytes_uncompressed_unchecked(
        x.to_bytes(32, "little") + y.to_bytes(32, "little")
    )


# Vectors from the babyjubjub-rs 0.0.11 test suite (shared with circomlib's babyjub
# tests). Each one is also recomputed with the pure-Python reference below, so it is
# checked two independent ways.
P1 = (
    17777552123799933955779906779655732241715742912184938656739573121738514868268,
    2626589144620713026669568689430873010625803728049924121243784502389097019475,
)
P2 = (
    16540640123574156134436876038791482806971768689494387082833631921987005038935,
    20819045374670962167435360035096875258406992893633759881276124905556507972311,
)
P1_PLUS_P1 = (
    6890855772600357754907169075114257697580319025794532037257385534741338397365,
    4338620300185947561074059802482547481416142213883829469920100239455078257889,
)
P1_PLUS_P2 = (
    7916061937171219682591368294088513039687205273691143098332585753343424131937,
    14035240266687799601661095864649209771790948434046947201833777492504781204499,
)
THREE_P1 = (
    19372461775513343691590086534037741906533799473648040012278229434133483800898,
    9458658722007214007257525444427903161243386465067105737478306991484593958249,
)
N = 14035240266687799601661095864649209771790948434046947201833777492504781204499
N_P1 = (
    17070357974431721403481313912716834497662307308519659060910483826664480189605,
    4014745322800118607127020275658861516666525056516280575712425373174125159339,
)
P1_COMPRESSED = "53b81ed5bffe9545b54016234682e7b2f699bd42a5e9eae27ff4051bc698ce85"
# circomlib EdDSA test key: public key = scalar_key * B8.
SCALAR_KEY = 6466070937662820620902051049739362987537906109895538826186780010858059362905
PUBLIC_KEY = (
    0x1D5AC1F31407018B7D413A4F52C8F74463B30E6AC2238220AD8B254DE4EAA3A2,
    0x1E1DE8A908826C3F9AC2E0CEEE929ECD0CAF3B99B3EF24523AAAB796A6F733C4,
)
# (compressed point, little-endian x) pairs from babyjubjub-rs test_point_decompress{0,1}.
DECOMPRESS_VECTORS = [
    (
        "b5328f8791d48f20bec6e481d91c7ada235f1facf22547901c18656b6c3e042f",
        "b86cc8d9c97daef0afe1a4753c54fb2d8a530dc74c7eee4e72b3fdf2496d2113",
    ),
    (
        "70552d3ff548e09266ded29b33ce75139672b062b02aa66bb0d9247ffecf1d0b",
        "30f1635ba7d56f9cb32c3ffbe6dca508a68c7f43936af11a23c785ce98cb3404",
    ),
]
# Computed with tests/reference.py (not taken from a published source).
TWO_B8 = (
    10031262171927540148667355526369034398030886437092045105752248699557385197826,
    633281375905621697187330766174974863687049529291089048651929454608812697683,
)
# Pinned hash_to_point outputs (v1 construction), computed with tests/reference.py.
HASH_VECTORS = {
    b"": (
        6928535635951237861049503537415516876640328183090078777918023014319728650529,
        18841141940652591938750391057817054289174787520714117841910799257782782236086,
    ),
    b"abc": (
        15503089785997261300643626425350478464601166171473333224645446165742498757881,
        12277605667095479852048682703865544462516745451312924595158386180372624277559,
    ),
}


class TestKnownAnswers:
    def test_vectors_agree_with_reference(self):
        assert ref.add(P1, P1) == P1_PLUS_P1
        assert ref.add(P1, P2) == P1_PLUS_P2
        assert ref.mul(3, P1) == THREE_P1
        assert ref.mul(N, P1) == N_P1
        assert ref.compress(P1).hex() == P1_COMPRESSED
        assert ref.mul(SCALAR_KEY, ref.B8) == PUBLIC_KEY
        assert ref.add(ref.B8, ref.B8) == TWO_B8

    def test_doubling(self):
        p = from_ints(*P1)
        assert coords(p + p) == P1_PLUS_P1

    def test_addition(self):
        assert coords(from_ints(*P1) + from_ints(*P2)) == P1_PLUS_P2

    def test_scalar_multiplication(self):
        p = from_ints(*P1)
        assert coords(p.scalar_mult(3)) == THREE_P1
        assert N > L  # exercises scalar reduction
        assert coords(p.scalar_mult(N)) == N_P1
        assert coords(p.scalar_mult(str(N))) == N_P1

    def test_two_b8(self):
        assert coords(ECPoint.from_scalar(2)) == TWO_B8

    def test_circomlib_public_key(self):
        assert coords(ECPoint.from_scalar(SCALAR_KEY)) == PUBLIC_KEY

    def test_compress(self):
        assert from_ints(*P1).to_bytes().hex() == P1_COMPRESSED
        assert coords(ECPoint.from_bytes(bytes.fromhex(P1_COMPRESSED))) == P1

    @pytest.mark.parametrize("compressed, x_le", DECOMPRESS_VECTORS)
    def test_decompress(self, compressed, x_le):
        p = ECPoint.from_bytes(bytes.fromhex(compressed))
        assert int(p.x_hex(), 16) == int.from_bytes(bytes.fromhex(x_le), "little")
        assert p.to_bytes().hex() == compressed


class TestValidation:
    def test_off_curve_rejected(self):
        assert not ref.on_curve((1, 2))
        with pytest.raises(ValueError, match="not on the Baby JubJub curve"):
            ECPoint("0x1", "0x2")
        with pytest.raises(ValueError, match="not on the Baby JubJub curve"):
            ECPoint.from_bytes_uncompressed(
                (1).to_bytes(32, "little") + (2).to_bytes(32, "little")
            )
        x, y = coords(G)
        with pytest.raises(ValueError):
            ECPoint(hex(x), hex(y + 1))

    def test_non_canonical_coordinates_rejected(self):
        x, y = coords(G)
        with pytest.raises(ValueError, match="canonical"):
            ECPoint(hex(x + ref.P), hex(y))
        with pytest.raises(ValueError):
            ECPoint("-0x1", "0x1")
        with pytest.raises(ValueError):
            ECPoint("0xzz", "0x1")
        with pytest.raises(ValueError):
            ECPoint.from_bytes_uncompressed(
                (x + ref.P).to_bytes(32, "little") + y.to_bytes(32, "little")
            )
        with pytest.raises(ValueError):
            ECPoint.from_bytes_uncompressed_unchecked(b"\xff" * 64)

    def test_full_group_generator_rejected(self):
        # G0 is on the curve and has order 8*l, so it is not in the prime subgroup.
        assert ref.on_curve(ref.G0)
        assert ref.mul(8, ref.G0) == ref.B8
        with pytest.raises(ValueError, match="not in the prime-order subgroup"):
            from_ints(*ref.G0)
        with pytest.raises(ValueError, match="not in the prime-order subgroup"):
            ECPoint.from_bytes(ref.compress(ref.G0))
        x, y = ref.G0
        with pytest.raises(ValueError, match="not in the prime-order subgroup"):
            ECPoint.from_bytes_uncompressed(
                x.to_bytes(32, "little") + y.to_bytes(32, "little")
            )

    def test_low_order_points_rejected(self):
        order2 = (0, ref.P - 1)
        assert ref.on_curve(order2)
        with pytest.raises(ValueError, match="not in the prime-order subgroup"):
            from_ints(*order2)
        with pytest.raises(ValueError, match="not in the prime-order subgroup"):
            ECPoint.from_bytes(ref.compress(order2))
        # Subgroup point plus a torsion point.
        with pytest.raises(ValueError, match="not in the prime-order subgroup"):
            from_ints(*ref.add(ref.B8, order2))
        # y = 0 gives the order-4 points.
        with pytest.raises(ValueError, match="not in the prime-order subgroup"):
            ECPoint.from_bytes(bytes(32))

    def test_bad_compressed_encodings_rejected(self):
        # y >= p
        with pytest.raises(ValueError):
            ECPoint.from_bytes((ref.P).to_bytes(32, "little"))
        # y for which no x exists
        y = next(
            y for y in range(2, 100) if ref.recover_x(y, False) is None
        )
        with pytest.raises(ValueError):
            ECPoint.from_bytes(y.to_bytes(32, "little"))
        # identity with the sign bit set is a non-canonical encoding of x = 0
        with pytest.raises(ValueError):
            ECPoint.from_bytes(b"\x01" + bytes(30) + b"\x80")

    def test_unchecked_skips_validation(self):
        g0 = unchecked(ref.G0)
        assert g0.is_on_curve()
        assert not g0.is_in_subgroup()
        off = unchecked((1, 2))
        assert not off.is_on_curve()
        assert not off.is_in_subgroup()

    def test_scalar_mult_outside_subgroup(self):
        # scalar_mult reduces modulo CURVE_ORDER = 8*l, which keeps it correct for
        # points of order 8*l obtained through the unchecked path.
        g0 = unchecked(ref.G0)
        assert g0.scalar_mult(-1) == g0.neg()
        assert coords(g0.scalar_mult(8)) == ref.B8
        assert not g0.scalar_mult(L).is_infinity()
        assert g0.scalar_mult(8 * L).is_infinity()
        assert g0.scalar_mult(-L) == g0.scalar_mult(7 * L)
        assert coords(g0.scalar_mult(L + 1)) == ref.mul(L + 1, ref.G0)


class TestHashToPoint:
    def test_matches_reference(self):
        for data, expected in HASH_VECTORS.items():
            assert ref.hash_to_point(data) == expected
            assert coords(ECPoint.hash_to_point(data)) == expected

    def test_random_inputs_match_reference(self):
        rng = random.Random(7)
        for n in range(8):
            data = bytes(rng.randrange(256) for _ in range(n * 9))
            assert coords(ECPoint.hash_to_point(data)) == ref.hash_to_point(data)

    def test_deterministic(self):
        assert ECPoint.hash_to_point(b"test data") == ECPoint.hash_to_point(b"test data")

    def test_different_inputs(self):
        assert ECPoint.hash_to_point(b"input 1") != ECPoint.hash_to_point(b"input 2")

    def test_output_in_subgroup_and_not_identity(self):
        for i in range(20):
            h = ECPoint.hash_to_point(i.to_bytes(2, "big"))
            assert not h.is_infinity()
            assert h.is_on_curve()
            assert h.is_in_subgroup()
            assert ECPoint.from_bytes(h.to_bytes()) == h

    def test_not_the_old_construction(self):
        for data in [b"", b"abc", b"Hello, World!"]:
            assert ECPoint.hash_to_point(data) != ECPoint.hash_to_scalar_times_generator(data)

    def test_old_construction_kept(self):
        for data in [b"", b"abc", b"Hello, World!"]:
            k = int.from_bytes(hashlib.sha256(data).digest(), "big")
            assert ECPoint.hash_to_scalar_times_generator(data) == ECPoint.from_scalar(k)
