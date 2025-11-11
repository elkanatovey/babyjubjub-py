use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use babyjubjub_rs::{Point, Fr, decompress_point};
use num_bigint::BigInt;
use num_traits::Num;
use sha2::{Sha256, Digest};
use std::str::FromStr;
use ff_ce::{Field, PrimeField};

/// Baby JubJub Elliptic Curve Point
/// 
/// This class wraps Baby JubJub curve operations and provides a Python-friendly API
/// that matches the secp256k1 ECPoint interface used in the PaXoS implementation.
#[pyclass]
#[derive(Clone)]
struct ECPoint {
    point: Point,
}

#[pymethods]
impl ECPoint {
    /// Create a new ECPoint from coordinates
    #[new]
    fn new(x_hex: &str, y_hex: &str) -> PyResult<Self> {
        let x = parse_hex_to_fr(x_hex)?;
        let y = parse_hex_to_fr(y_hex)?;
        
        let point = Point { x, y };
        
        // TODO: Add curve validation if needed
        
        Ok(ECPoint { point })
    }
    
    /// Get the generator point (base point) of Baby JubJub
    #[staticmethod]
    fn generator() -> Self {
        // B8 base point coordinates from babyjubjub-rs source
        let x = Fr::from_str(
            "5299619240641551281634865583518297030282874472190772894086521144482721001553"
        ).unwrap();
        let y = Fr::from_str(
            "16950150798460657717958625567821834550301663161624707787222815936182638968203"
        ).unwrap();
        
        ECPoint {
            point: Point { x, y },
        }
    }
    
    /// Get the identity point (point at infinity)
    #[staticmethod]
    fn infinity() -> Self {
        ECPoint {
            point: Point {
                x: Fr::zero(),
                y: Fr::one(),
            },
        }
    }
    
    /// Create a point from a scalar value (scalar * generator)
    #[staticmethod]
    fn from_scalar(scalar: &str) -> PyResult<Self> {
        let scalar_bigint = parse_scalar(scalar)?;
        let generator = ECPoint::generator();
        
        let result = generator.point.mul_scalar(&scalar_bigint);
        
        Ok(ECPoint { point: result })
    }
    
    /// Add two points (releases GIL for parallelization)
    fn add(&self, py: Python, other: &ECPoint) -> Self {
        py.allow_threads(move || {
            let result = self.point.projective().add(&other.point.projective());
            ECPoint {
                point: result.affine(),
            }
        })
    }
    
    /// Negate a point
    fn neg(&self) -> Self {
        let mut result = self.point.clone();
        result.x.negate();
        ECPoint { point: result }
    }
    
    /// Subtract two points (releases GIL for parallelization)
    fn sub(&self, py: Python, other: &ECPoint) -> Self {
        self.add(py, &other.neg())
    }
    
    /// Scalar multiplication (scalar * point) (releases GIL for parallelization)
    fn scalar_mult(&self, py: Python, scalar: &str) -> PyResult<Self> {
        let scalar_bigint = parse_scalar(scalar)?;
        let point = self.point.clone();
        
        let result = py.allow_threads(move || {
            point.mul_scalar(&scalar_bigint)
        });
        
        Ok(ECPoint { point: result })
    }
    
    /// Check if this is the identity point
    fn is_infinity(&self) -> bool {
        self.point.x.is_zero() && self.point.y == Fr::one()
    }
    
    /// Get x coordinate as hex string
    fn x_hex(&self) -> String {
        fr_to_hex(&self.point.x)
    }
    
    /// Get y coordinate as hex string
    fn y_hex(&self) -> String {
        fr_to_hex(&self.point.y)
    }
    
    /// Serialize to bytes (compressed format)
    fn to_bytes(&self) -> Vec<u8> {
        self.point.compress().to_vec()
    }
    
    /// Serialize to uncompressed bytes (64 bytes: x || y) - FAST for pickling
    fn to_bytes_uncompressed(&self) -> Vec<u8> {
        let mut result = Vec::with_capacity(64);
        let x_repr = self.point.x.into_repr();
        let y_repr = self.point.y.into_repr();
        
        // Convert FrRepr (array of u64) to bytes
        for &limb in x_repr.as_ref() {
            result.extend_from_slice(&limb.to_le_bytes());
        }
        for &limb in y_repr.as_ref() {
            result.extend_from_slice(&limb.to_le_bytes());
        }
        result
    }
    
    /// Deserialize from bytes (compressed format)
    #[staticmethod]
    fn from_bytes(bytes: Vec<u8>) -> PyResult<Self> {
        if bytes.len() != 32 {
            return Err(PyValueError::new_err("Invalid byte length, expected 32 bytes"));
        }
        
        let mut arr = [0u8; 32];
        arr.copy_from_slice(&bytes);
        
        match decompress_point(arr) {
            Ok(point) => Ok(ECPoint { point }),
            Err(e) => Err(PyValueError::new_err(format!("Failed to decompress point: {}", e))),
        }
    }
    
    /// Deserialize from uncompressed bytes (64 bytes: x || y) - FAST for pickling
    #[staticmethod]
    fn from_bytes_uncompressed(bytes: Vec<u8>) -> PyResult<Self> {
        use ff_ce::PrimeField;
        
        if bytes.len() != 64 {
            return Err(PyValueError::new_err("Invalid byte length, expected 64 bytes"));
        }
        
        // Convert bytes to FrRepr (array of u64 limbs)
        // Get the actual type from Fr::Repr
        type FrRepr = <Fr as PrimeField>::Repr;
        
        let mut x_limbs = [0u64; 4];
        let mut y_limbs = [0u64; 4];
        
        for i in 0..4 {
            x_limbs[i] = u64::from_le_bytes([
                bytes[i*8], bytes[i*8+1], bytes[i*8+2], bytes[i*8+3],
                bytes[i*8+4], bytes[i*8+5], bytes[i*8+6], bytes[i*8+7],
            ]);
            y_limbs[i] = u64::from_le_bytes([
                bytes[32+i*8], bytes[32+i*8+1], bytes[32+i*8+2], bytes[32+i*8+3],
                bytes[32+i*8+4], bytes[32+i*8+5], bytes[32+i*8+6], bytes[32+i*8+7],
            ]);
        }
        
        // Construct FrRepr from limbs
        let x_repr: FrRepr = unsafe { std::mem::transmute(x_limbs) };
        let y_repr: FrRepr = unsafe { std::mem::transmute(y_limbs) };
        
        let x = Fr::from_repr(x_repr)
            .map_err(|_| PyValueError::new_err("Invalid x coordinate"))?;
        let y = Fr::from_repr(y_repr)
            .map_err(|_| PyValueError::new_err("Invalid y coordinate"))?;
        
        Ok(ECPoint { point: Point { x, y } })
    }
    
    /// Hash arbitrary data to a curve point (deterministic)
    #[staticmethod]
    fn hash_to_point(data: &[u8]) -> PyResult<Self> {
        // Hash the data to get a scalar, then multiply by generator
        let mut hasher = Sha256::new();
        hasher.update(data);
        let hash = hasher.finalize();
        
        // Convert hash to BigInt mod curve order
        let hash_bigint = BigInt::from_bytes_be(num_bigint::Sign::Plus, &hash);
        let order = get_curve_order();
        let scalar_bigint = hash_bigint % &order;
        
        let generator = ECPoint::generator();
        let result = generator.point.mul_scalar(&scalar_bigint);
        
        Ok(ECPoint { point: result })
    }
    
    /// Equality comparison
    fn __eq__(&self, other: &ECPoint) -> bool {
        self.point.equals(other.point.clone())
    }
    
    /// String representation
    fn __repr__(&self) -> String {
        format!(
            "ECPoint(x={}, y={})",
            fr_to_hex(&self.point.x),
            fr_to_hex(&self.point.y)
        )
    }
    
    /// String representation
    fn __str__(&self) -> String {
        self.__repr__()
    }
}

// Helper functions

fn parse_hex_to_fr(hex_str: &str) -> PyResult<Fr> {
    let hex_clean = hex_str.trim_start_matches("0x");
    let bigint = BigInt::from_str_radix(hex_clean, 16)
        .map_err(|e| PyValueError::new_err(format!("Invalid hex string: {}", e)))?;
    
    Fr::from_str(&bigint.to_string())
        .ok_or_else(|| PyValueError::new_err("Invalid field element"))
}

fn parse_scalar(s: &str) -> PyResult<BigInt> {
    if s.starts_with("0x") || s.starts_with("0X") {
        let hex_clean = s.trim_start_matches("0x").trim_start_matches("0X");
        BigInt::from_str_radix(hex_clean, 16)
            .map_err(|e| PyValueError::new_err(format!("Invalid hex scalar: {}", e)))
    } else {
        s.parse::<BigInt>()
            .map_err(|e| PyValueError::new_err(format!("Invalid scalar: {}", e)))
    }
}

fn fr_to_hex(fr: &Fr) -> String {
    // Convert Fr to string, then to BigInt, then to hex
    let fr_str = format!("{:?}", fr);
    // Parse the debug format which is like "Fr(0x...)"
    if let Some(hex_part) = fr_str.strip_prefix("Fr(0x").and_then(|s| s.strip_suffix(")")) {
        format!("0x{}", hex_part)
    } else {
        // Fallback: convert via string representation
        match Fr::to_string(fr).parse::<BigInt>() {
            Ok(bigint) => format!("0x{:x}", bigint),
            Err(_) => format!("{:?}", fr),
        }
    }
}

fn get_curve_order() -> BigInt {
    // Baby JubJub subgroup order (prime order of the main subgroup)
    BigInt::from_str(
        "21888242871839275222246405745257275088614511777268538073601725287587578984328"
    ).unwrap()
}

/// Module constants and utilities
#[pymodule]
fn babyjubjub_py(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ECPoint>()?;
    
    // Add module-level constants
    m.add("__version__", "0.1.0")?;
    
    // Curve parameters as strings (for reference)
    m.add("CURVE_ORDER", 
        "21888242871839275222246405745257275088614511777268538073601725287587578984328")?;
    m.add("CURVE_NAME", "Baby JubJub")?;
    
    Ok(())
}
