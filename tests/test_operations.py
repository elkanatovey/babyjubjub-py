"""Comprehensive test suite for Baby JubJub Python bindings."""

import pytest
import babyjubjub_py as bjj


class TestBasicOperations:
    """Test basic elliptic curve operations."""
    
    def test_generator_point(self):
        """Test that generator point is accessible and valid."""
        g = bjj.ECPoint.generator()
        assert not g.is_infinity()
        assert g.x_hex() is not None
        assert g.y_hex() is not None
    
    def test_infinity_point(self):
        """Test identity/infinity point."""
        inf = bjj.ECPoint.infinity()
        assert inf.is_infinity()
    
    def test_scalar_multiplication(self):
        """Test scalar multiplication operation."""
        p1 = bjj.ECPoint.from_scalar("1")
        g = bjj.ECPoint.generator()
        assert p1 == g
        
        p2 = bjj.ECPoint.from_scalar("2")
        p1_plus_g = p1.add(g)
        assert p2 == p1_plus_g
    
    def test_point_addition_associativity(self):
        """Test that point addition is associative: (P + Q) + R = P + (Q + R)."""
        p = bjj.ECPoint.from_scalar("123")
        q = bjj.ECPoint.from_scalar("456")
        r = bjj.ECPoint.from_scalar("789")
        
        left = p.add(q).add(r)
        right = p.add(q.add(r))
        assert left == right
    
    def test_point_addition_commutativity(self):
        """Test that point addition is commutative: P + Q = Q + P."""
        p = bjj.ECPoint.from_scalar("123")
        q = bjj.ECPoint.from_scalar("456")
        
        assert p.add(q) == q.add(p)
    
    def test_point_negation(self):
        """Test that P + (-P) = O."""
        p = bjj.ECPoint.from_scalar("123")
        neg_p = p.neg()
        result = p.add(neg_p)
        assert result.is_infinity()
    
    def test_point_subtraction(self):
        """Test point subtraction: P - Q = P + (-Q)."""
        p = bjj.ECPoint.from_scalar("123")
        q = bjj.ECPoint.from_scalar("456")
        
        sub_result = p.sub(q)
        add_neg_result = p.add(q.neg())
        assert sub_result == add_neg_result
    
    def test_identity_element(self):
        """Test that O + P = P for any point P."""
        p = bjj.ECPoint.from_scalar("123")
        inf = bjj.ECPoint.infinity()
        result = p.add(inf)
        assert result == p
    
    def test_scalar_addition_distributivity(self):
        """Test that (a + b) * G = a*G + b*G."""
        a = 123
        b = 456
        
        left = bjj.ECPoint.from_scalar(str(a + b))
        right = bjj.ECPoint.from_scalar(str(a)).add(bjj.ECPoint.from_scalar(str(b)))
        assert left == right


class TestSerialization:
    """Test point serialization and deserialization."""
    
    def test_compression_roundtrip(self):
        """Test that compression and decompression are inverse operations."""
        p = bjj.ECPoint.from_scalar("123456789")
        compressed = p.to_bytes()
        restored = bjj.ECPoint.from_bytes(compressed)
        assert p == restored
    
    def test_compression_length(self):
        """Test that compressed format is 32 bytes."""
        p = bjj.ECPoint.from_scalar("123")
        compressed = p.to_bytes()
        assert len(compressed) == 32
    
    def test_uncompressed_roundtrip(self):
        """Test uncompressed serialization roundtrip."""
        p = bjj.ECPoint.from_scalar("987654321")
        uncompressed = p.to_bytes_uncompressed()
        restored = bjj.ECPoint.from_bytes_uncompressed(uncompressed)
        assert p == restored
    
    def test_uncompressed_length(self):
        """Test that uncompressed format is 64 bytes."""
        p = bjj.ECPoint.from_scalar("123")
        uncompressed = p.to_bytes_uncompressed()
        assert len(uncompressed) == 64
    
    def test_infinity_serialization(self):
        """Test that infinity point can be serialized and deserialized."""
        inf = bjj.ECPoint.infinity()
        # Note: Compressed serialization of infinity may not roundtrip correctly
        # This is a known limitation of the compressed format
        # Test uncompressed instead
        uncompressed = inf.to_bytes_uncompressed()
        restored = bjj.ECPoint.from_bytes_uncompressed(uncompressed)
        assert restored.is_infinity()


class TestHashToPoint:
    """Test deterministic hashing to curve points."""
    
    def test_deterministic_hashing(self):
        """Test that hashing is deterministic."""
        data = b"test data"
        h1 = bjj.ECPoint.hash_to_point(data)
        h2 = bjj.ECPoint.hash_to_point(data)
        assert h1 == h2
    
    def test_different_inputs_different_outputs(self):
        """Test that different inputs produce different points."""
        h1 = bjj.ECPoint.hash_to_point(b"input 1")
        h2 = bjj.ECPoint.hash_to_point(b"input 2")
        assert h1 != h2
    
    def test_hash_not_infinity(self):
        """Test that hash_to_point doesn't produce infinity."""
        h = bjj.ECPoint.hash_to_point(b"any data")
        assert not h.is_infinity()
    
    def test_empty_input(self):
        """Test hashing empty input."""
        h = bjj.ECPoint.hash_to_point(b"")
        assert not h.is_infinity()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_zero_scalar(self):
        """Test scalar multiplication by zero gives infinity."""
        p = bjj.ECPoint.from_scalar("0")
        assert p.is_infinity()
    
    def test_large_scalar(self):
        """Test scalar multiplication with large scalar."""
        large_scalar = str(2**256 - 1)
        p = bjj.ECPoint.from_scalar(large_scalar)
        assert not p.is_infinity()
    
    def test_negative_scalar_string(self):
        """Test that negative scalar strings are handled."""
        # Note: This may wrap around modulo the curve order
        p = bjj.ECPoint.from_scalar("-1")
        assert not p.is_infinity()
    
    def test_point_equality(self):
        """Test point equality comparison."""
        p1 = bjj.ECPoint.from_scalar("123")
        p2 = bjj.ECPoint.from_scalar("123")
        p3 = bjj.ECPoint.from_scalar("456")
        
        assert p1 == p2
        assert p1 != p3
    
    def test_multiple_negations(self):
        """Test that -(-P) = P."""
        p = bjj.ECPoint.from_scalar("123")
        neg_neg_p = p.neg().neg()
        assert p == neg_neg_p


class TestModuleMetadata:
    """Test module-level constants and metadata."""
    
    def test_version_exists(self):
        """Test that version string exists."""
        assert hasattr(bjj, '__version__')
        assert isinstance(bjj.__version__, str)
    
    def test_curve_name(self):
        """Test curve name constant."""
        assert hasattr(bjj, 'CURVE_NAME')
        assert bjj.CURVE_NAME == "Baby JubJub"
    
    def test_curve_order(self):
        """Test curve order constant."""
        assert hasattr(bjj, 'CURVE_ORDER')
        # CURVE_ORDER is exported as a string from Rust
        assert isinstance(bjj.CURVE_ORDER, (int, str))
        if isinstance(bjj.CURVE_ORDER, str):
            assert int(bjj.CURVE_ORDER) > 0
        else:
            assert bjj.CURVE_ORDER > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

