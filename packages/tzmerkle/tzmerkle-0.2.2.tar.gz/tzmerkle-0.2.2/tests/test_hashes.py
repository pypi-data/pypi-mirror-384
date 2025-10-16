"""Tests for hash functions."""

from tzmerkle.hashes import blake2b, sha256, sha512, sha3, keccak, ALL_HASHES


def test_hash_functions_exist():
    """Test that all hash functions are available."""
    assert blake2b is not None
    assert sha256 is not None
    assert sha512 is not None
    assert sha3 is not None
    assert keccak is not None


def test_hash_returns_bytes():
    """Test that hash functions return bytes."""
    data = b"Tezos"
    assert isinstance(blake2b(data), bytes)
    assert isinstance(sha256(data), bytes)
    assert isinstance(sha512(data), bytes)
    assert isinstance(sha3(data), bytes)
    assert isinstance(keccak(data), bytes)


def test_hash_digest_sizes():
    """Test that hash functions return correct digest sizes."""
    data = b"Tezos"
    assert len(blake2b(data)) == 32
    assert len(sha256(data)) == 32
    assert len(sha512(data)) == 64
    assert len(sha3(data)) == 32
    assert len(keccak(data)) == 32


def test_hexdigest():
    """Test hexdigest method returns hex string."""
    data = b"Tezos"
    hex_result = sha256.hexdigest(data)
    assert isinstance(hex_result, str)
    assert len(hex_result) == 64  # 32 bytes * 2 hex chars


def test_hash_deterministic():
    """Test that hash functions are deterministic."""
    data = b"Tezos"
    assert sha256(data) == sha256(data)
    assert blake2b(data) == blake2b(data)


def test_all_hashes_dict():
    """Test ALL_HASHES dictionary contains all hash functions."""
    assert "blake2b" in ALL_HASHES
    assert "sha256" in ALL_HASHES
    assert "sha512" in ALL_HASHES
    assert "sha3" in ALL_HASHES
    assert "keccak" in ALL_HASHES
    assert len(ALL_HASHES) == 5


def test_hash_repr():
    """Test hash function __repr__ method."""
    assert "sha256" in repr(sha256)
    assert "TezosHash" in repr(sha256)
