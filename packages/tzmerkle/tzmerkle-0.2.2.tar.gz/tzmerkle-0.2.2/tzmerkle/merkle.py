from pathlib import Path
from typing import Any, List, Mapping, Optional, Union
from collections.abc import Mapping as AbstractMapping
import smartpy as sp
import json
from pytezos.michelson.parse import michelson_to_micheline
from pytezos.michelson.types import MichelsonType
from .hashes import TezosHash, blake2b, ALL_HASHES


class MerkleTreeError(Exception):
    """Base exception for MerkleTree errors."""

    pass


class TreeNotBuiltError(MerkleTreeError):
    """Raised when trying to access tree data before building."""

    pass


class EmptyTreeError(MerkleTreeError):
    """Raised when trying to build a tree with no leaves."""

    pass


class LeafNotFoundError(MerkleTreeError):
    """Raised when a leaf is not found in the tree."""

    pass


class InvalidLeafError(MerkleTreeError):
    """Raised when a leaf has invalid format or type."""

    pass


class MerkleTree:
    """Tezos-compatible Merkle tree implementation.

    A Merkle tree is a hash-based data structure that allows efficient
    verification of data integrity. This implementation is optimized
    for use with Tezos blockchain, supporting Michelson types and
    multiple hash functions.

    Args:
        leaf_type: Michelson type representation (e.g., "nat", "string")
            or micheline dict (e.g. {'prim': 'nat'})
        hash_fn: Hash function to use (default: blake2b). Must be a
            TezosHash instance from tzmerkle.hashes

    Example:
        >>> from tzmerkle import MerkleTree
        >>> from tzmerkle.hashes import blake2b
        >>> tree = MerkleTree("nat", blake2b)
        >>> tree.add_leaves([1, 2, 3, 4])
        >>> tree.build()
        >>> root = tree.merkle_root
        >>> proof = tree.get_proof(tree.encode_raw_leaf(1))
    """

    def __init__(self, leaf_type: str | Mapping[str, Any], hash_fn: TezosHash = blake2b):
        if not isinstance(hash_fn, TezosHash):
            raise ValueError(
                f"hash_fn must be a TezosHash instance, got {type(hash_fn)}"
            )

        self._hash_fn = hash_fn
        self._leaves: List[bytes] = []
        try:
            match leaf_type:
                case str():
                    self._leaf_type_micheline = michelson_to_micheline(leaf_type)
                case AbstractMapping():
                    self._leaf_type_micheline = leaf_type
                case _:
                    raise InvalidLeafError(
                        f"leaf_type must be a string or Mapping, got {type(leaf_type)}"
                    )
            self._leaf_type = MichelsonType.match(self._leaf_type_micheline)
        except Exception as e:
            raise InvalidLeafError(f"Invalid leaf type '{leaf_type}': {e}") from e

        self._built = False
        self._levels: List[List[bytes]] = []

    def encode_raw_leaf(self, leaf: Any) -> bytes:
        """Encode a Python object as a Michelson-packed byte string.

        Args:
            leaf: Python object compatible with the tree's leaf_type

        Returns:
            Packed bytes representation of the leaf

        Raises:
            InvalidLeafError: If the leaf cannot be encoded
        """
        try:
            return self._leaf_type.from_python_object(leaf).pack()
        except Exception as e:
            raise InvalidLeafError(f"Failed to encode leaf {leaf}: {e}") from e

    def encode_raw_leaf_spy(self, leaf: Any) -> sp.bytes:
        """Encode a leaf for SmartPy contracts.

        Args:
            leaf: Python object compatible with the tree's leaf_type

        Returns:
            SmartPy bytes object with hex-encoded leaf
        """
        return sp.bytes("0x" + self.encode_raw_leaf(leaf).hex())

    def add_leaf(self, leaf: Any) -> None:
        """Add a single leaf to the tree (will be encoded automatically).

        Args:
            leaf: Python object compatible with the tree's leaf_type

        Raises:
            InvalidLeafError: If the leaf cannot be encoded
        """
        encoded = self.encode_raw_leaf(leaf)
        self._built = False
        self._leaves.append(encoded)

    def add_encoded_leaf(self, leaf: bytes) -> None:
        """Add a pre-encoded leaf to the tree.

        Args:
            leaf: Already encoded leaf as bytes

        Raises:
            InvalidLeafError: If leaf is not bytes
        """
        if not isinstance(leaf, bytes):
            raise InvalidLeafError(f"Encoded leaf must be bytes, got {type(leaf)}")
        self._built = False
        self._leaves.append(leaf)

    def add_leaves(self, leaves: List[Any]) -> None:
        """Add multiple leaves to the tree (will be encoded automatically).

        Args:
            leaves: List of Python objects compatible with leaf_type

        Raises:
            InvalidLeafError: If any leaf cannot be encoded
        """
        if not isinstance(leaves, (list, tuple)):
            raise InvalidLeafError(
                f"leaves must be a list or tuple, got {type(leaves)}"
            )
        encoded = [self.encode_raw_leaf(leaf) for leaf in leaves]
        self._built = False
        self._leaves.extend(encoded)

    def add_encoded_leaves(self, leaves: List[bytes]) -> None:
        """Add multiple pre-encoded leaves to the tree.

        Args:
            leaves: List of already encoded leaves as bytes

        Raises:
            InvalidLeafError: If leaves is not a list or any item not bytes
        """
        if not isinstance(leaves, (list, tuple)):
            raise InvalidLeafError(
                f"leaves must be a list or tuple, got {type(leaves)}"
            )
        for i, leaf in enumerate(leaves):
            if not isinstance(leaf, bytes):
                raise InvalidLeafError(
                    f"Encoded leaf at index {i} must be bytes, " f"got {type(leaf)}"
                )
        self._built = False
        self._leaves.extend(leaves)

    def build(self) -> None:
        """Build the Merkle tree from added leaves.

        Computes all intermediate hash levels up to the root.
        For odd-numbered levels, the unpaired leaf is carried forward.

        Raises:
            EmptyTreeError: If no leaves have been added
        """
        if len(self._leaves) == 0:
            raise EmptyTreeError(
                "Cannot build tree: no leaves added. "
                "Use add_leaf() or add_leaves() first."
            )

        self._levels = [[self._hash_fn(leaf) for leaf in self._leaves]]

        while (num_nodes := len(self._levels[-1])) > 1:
            new_level: List[bytes] = []
            solo_leaf: Optional[bytes] = None

            if num_nodes % 2 == 1:
                solo_leaf = self._levels[-1][-1]
                num_nodes -= 1

            pairs = zip(
                self._levels[-1][0:num_nodes:2], self._levels[-1][1:num_nodes:2]
            )
            for left, right in pairs:
                combined = left + right if (left < right) else right + left
                new_level.append(self._hash_fn(combined))

            if solo_leaf is not None:
                new_level.append(solo_leaf)

            self._levels.append(new_level)
        self._built = True

    @property
    def merkle_root(self) -> bytes:
        """Get the Merkle root hash.

        Returns:
            Root hash as bytes

        Raises:
            TreeNotBuiltError: If build() hasn't been called
        """
        if not self._built:
            raise TreeNotBuiltError("Tree not built. Call build() first.")
        return self._levels[-1][0]

    @property
    def merkle_root_spy(self) -> sp.bytes:
        """Get the Merkle root as a SmartPy bytes object.

        Returns:
            Root hash as SmartPy bytes (hex-encoded)

        Raises:
            TreeNotBuiltError: If build() hasn't been called
        """
        return sp.bytes("0x" + self.merkle_root.hex())

    def get_proof(self, leaf: Any) -> List[bytes]:
        """Generate a Merkle proof for a given unencoded leaf.

        The proof is a list of sibling hashes needed to verify that
        the leaf is part of the tree. This method accepts raw Python
        values and handles encoding automatically.

        Args:
            leaf: The unencoded leaf value (must match tree's leaf_type)

        Returns:
            List of sibling hashes forming the proof path

        Raises:
            TreeNotBuiltError: If build() hasn't been called
            InvalidLeafError: If leaf cannot be encoded
            LeafNotFoundError: If leaf is not in the tree
        """
        try:
            return self.get_proof_from_encoded(
                self._leaf_type.from_python_object(leaf).pack()
            )
        except (TreeNotBuiltError, LeafNotFoundError):
            raise
        except Exception as e:
            raise InvalidLeafError(f"Failed to encode leaf {leaf}: {e}") from e

    def get_proof_from_encoded(self, leaf: bytes) -> List[bytes]:
        """Generate a Merkle proof for a given leaf.

        The proof is a list of sibling hashes needed to verify that
        the leaf is part of the tree.

        Args:
            leaf: The encoded leaf to generate proof for

        Returns:
            List of sibling hashes forming the proof path

        Raises:
            TreeNotBuiltError: If build() hasn't been called
            InvalidLeafError: If leaf is not bytes
            LeafNotFoundError: If leaf is not in the tree
        """
        if not isinstance(leaf, bytes):
            raise InvalidLeafError(
                f"Leaf must be bytes (encoded), got {type(leaf)}. "
                "Use encode_raw_leaf() first."
            )
        if not self._built:
            raise TreeNotBuiltError("Tree not built. Call build() first.")
        if leaf not in self._leaves:
            raise LeafNotFoundError(
                "Leaf not found in tree. " "Ensure the leaf was added before building."
            )

        current_hash = self._hash_fn(leaf)
        proof: List[bytes] = []

        for i, level in enumerate(self._levels[:-1]):
            ch_index = level.index(current_hash)
            ch_index_even = ch_index % 2 == 0

            # Skip if this is the last node and unpaired
            if ch_index == len(level) - 1 and ch_index_even:
                continue

            # Get the sibling hash
            pair_idx = ch_index + 1 if ch_index_even else ch_index - 1
            proof.append(level[pair_idx])
            current_hash = self._levels[i + 1][ch_index // 2]

        return proof

    def get_proof_spy(self, leaf: Any) -> List[sp.bytes]:
        """Generate a Merkle proof for SmartPy contracts.

        Args:
            leaf: The unencoded leaf to generate proof for

        Returns:
            List of SmartPy bytes objects forming the proof path

        Raises:
            TreeNotBuiltError: If build() hasn't been called
            InvalidLeafError: If leaf cannot be encoded
            LeafNotFoundError: If leaf is not in the tree
        """
        return [
            sp.bytes("0x" + proof_element.hex())
            for proof_element in self.get_proof(leaf)
        ]

    def get_proof_from_encoded_spy(self, leaf: bytes) -> List[sp.bytes]:
        """Generate a Merkle proof for SmartPy contracts from encoded leaf.

        Args:
            leaf: The encoded leaf to generate proof for

        Returns:
            List of SmartPy bytes objects forming the proof path

        Raises:
            TreeNotBuiltError: If build() hasn't been called
            InvalidLeafError: If leaf is not bytes
            LeafNotFoundError: If leaf is not in the tree
        """
        return [
            sp.bytes("0x" + proof_element.hex())
            for proof_element in self.get_proof_from_encoded(leaf)
        ]

    def serialise(
        self,
        path: Union[Path, str],
        include_tree: bool = False,
        include_proofs: bool = False,
    ) -> None:
        """Serialize the Merkle tree to a JSON file.

        Args:
            path: File path to save the tree
            include_tree: If True, include all hash levels
            include_proofs: If True, include proofs for all leaves

        Raises:
            TreeNotBuiltError: If build() hasn't been called
        """
        if not self._built:
            raise TreeNotBuiltError("Tree not built. Call build() first.")

        data = {
            "leaf_type_micheline": self._leaf_type_micheline,
            "hash_fn": self._hash_fn.name,
            "leaves_hex": [leaf.hex() for leaf in self._leaves],
        }

        if include_tree:
            data["tree_hex"] = [[h.hex() for h in level] for level in self._levels]

        if include_proofs:
            data["proofs_hex"] = {
                leaf.hex(): [
                    proof_element.hex()
                    for proof_element in self.get_proof_from_encoded(leaf)
                ]
                for leaf in self._leaves
            }

        path = Path(path)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def from_file(cls, file_path: Union[Path, str]) -> "MerkleTree":
        """Load a Merkle tree from a JSON file.

        Args:
            file_path: Path to the serialized tree file

        Returns:
            Reconstructed MerkleTree instance

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is invalid
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path) as f:
                raw_data = json.load(f)

            if "leaf_type_micheline" not in raw_data:
                raise ValueError("Missing 'leaf_type_micheline' in file")
            if "hash_fn" not in raw_data:
                raise ValueError("Missing 'hash_fn' in file")
            if "leaves_hex" not in raw_data:
                raise ValueError("Missing 'leaves_hex' in file")

            hash_fn_name = raw_data["hash_fn"]
            if hash_fn_name not in ALL_HASHES:
                raise ValueError(
                    f"Unknown hash function: {hash_fn_name}. "
                    f"Available: {list(ALL_HASHES.keys())}"
                )

            mt = cls(
                leaf_type=raw_data["leaf_type_micheline"],
                hash_fn=ALL_HASHES[hash_fn_name],
            )

            leaves = [bytes.fromhex(leaf_hex) for leaf_hex in raw_data["leaves_hex"]]
            mt.add_encoded_leaves(leaves)

            if "tree_hex" in raw_data:
                mt._levels = [
                    [bytes.fromhex(h) for h in level] for level in raw_data["tree_hex"]
                ]
                mt._built = True

            return mt
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to load tree from file: {e}") from e
