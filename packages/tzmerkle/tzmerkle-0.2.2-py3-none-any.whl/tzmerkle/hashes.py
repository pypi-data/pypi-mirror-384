"""
Tezos-compatible hash functions.

Provides callable hash objects with a uniform interface matching SmartPy-style
usage (e.g., `sp.blake2b`). Each hasher returns raw bytes when called and offers
a `.hexdigest()` method for hex output.

Example:
    from tzmerkle.hashes import blake2b

    digest = blake2b(b"Tezos!")
    hex_digest = blake2b.hexdigest(b"Tezos!")
"""

import hashlib
from typing import Callable
from Crypto.Hash import keccak as keccak_

__all__ = ["blake2b", "sha512", "sha256", "sha3", "keccak", "ALL_HASHES"]


class TezosHash:
    """Callable hash object with consistent Tezos-compatible interface."""

    def __init__(self, name: str, func: Callable[[bytes], bytes], digest_size: int):
        self.name = name
        self._func = func
        self.digest_size = digest_size

    def __call__(self, data: bytes) -> bytes:
        """Return the hash digest as raw bytes."""
        return self._func(data)

    def hexdigest(self, data: bytes) -> str:
        """Return the hash digest as a hex string."""
        return self._func(data).hex()

    def __repr__(self) -> str:
        return f"<TezosHash {self.name}>"


# --- Hash function implementations ---


def _blake2b(data: bytes) -> bytes:
    """Compute BLAKE2b hash."""
    return hashlib.blake2b(data, digest_size=32).digest()


def _sha512(data: bytes) -> bytes:
    """Compute SHA-512 hash."""
    return hashlib.sha512(data).digest()


def _sha256(data: bytes) -> bytes:
    """Compute SHA-256 hash."""
    return hashlib.sha256(data).digest()


def _sha3(data: bytes) -> bytes:
    """Compute SHA3-256 hash."""
    return hashlib.sha3_256(data).digest()


def _keccak(data: bytes) -> bytes:
    """Compute Keccak-256 hash."""
    return keccak_.new(data=data, digest_bits=256).digest()


# --- Public callable instances ---

blake2b = TezosHash("blake2b", _blake2b, 32)
sha512 = TezosHash("sha512", _sha512, 64)
sha256 = TezosHash("sha256", _sha256, 32)
sha3 = TezosHash("sha3", _sha3, 32)
keccak = TezosHash("keccak", _keccak, 32)

ALL_HASHES = {
    "blake2b": blake2b,
    "sha512": sha512,
    "sha256": sha256,
    "sha3": sha3,
    "keccak": keccak,
}
