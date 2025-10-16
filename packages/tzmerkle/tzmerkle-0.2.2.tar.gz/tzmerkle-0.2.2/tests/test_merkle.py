"""Comprehensive tests for MerkleTree."""

import pytest
from tzmerkle import (
    MerkleTree,
    EmptyTreeError,
    TreeNotBuiltError,
    LeafNotFoundError,
    InvalidLeafError,
)
from tzmerkle.hashes import blake2b


class TestMerkleTreeInit:
    """Tests for MerkleTree initialization."""

    def test_init_with_valid_type(self):
        """Test initialization with valid Michelson type."""
        tree = MerkleTree("nat")
        assert tree._leaf_type_micheline == {"prim": "nat"}
        assert tree._built is False
        assert len(tree._leaves) == 0

    def test_init_with_custom_hash(self):
        """Test initialization with custom hash function."""
        tree = MerkleTree("nat", hash_fn=blake2b)
        assert tree._hash_fn == blake2b

    def test_init_with_invalid_type_raises_error(self):
        """Test initialization with invalid Michelson type."""
        with pytest.raises(InvalidLeafError, match="Invalid leaf type"):
            MerkleTree("not_a_valid_type123!@#")

    def test_init_with_non_string_type_raises_error(self):
        """Test initialization with non-string leaf_type."""
        with pytest.raises(InvalidLeafError, match="must be a string"):
            MerkleTree(123)

    def test_init_with_invalid_hash_fn_raises_error(self):
        """Test initialization with invalid hash function."""
        with pytest.raises(ValueError, match="must be a TezosHash"):
            MerkleTree("nat", hash_fn="not_a_hash")


class TestAddLeaves:
    """Tests for adding leaves to the tree."""

    def test_add_single_leaf(self):
        """Test adding a single leaf."""
        tree = MerkleTree("nat")
        tree.add_leaf(42)
        assert len(tree._leaves) == 1

    def test_add_multiple_leaves(self):
        """Test adding multiple leaves at once."""
        tree = MerkleTree("nat")
        tree.add_leaves([1, 2, 3, 4, 5])
        assert len(tree._leaves) == 5

    def test_add_encoded_leaf(self):
        """Test adding pre-encoded leaf."""
        tree = MerkleTree("nat")
        encoded = tree.encode_raw_leaf(42)
        tree.add_encoded_leaf(encoded)
        assert len(tree._leaves) == 1

    def test_add_encoded_leaf_invalid_type_raises_error(self):
        """Test adding non-bytes encoded leaf raises error."""
        tree = MerkleTree("nat")
        with pytest.raises(InvalidLeafError, match="must be bytes"):
            tree.add_encoded_leaf("not bytes")

    def test_add_encoded_leaves(self):
        """Test adding multiple pre-encoded leaves."""
        tree = MerkleTree("nat")
        encoded = [tree.encode_raw_leaf(i) for i in range(5)]
        tree.add_encoded_leaves(encoded)
        assert len(tree._leaves) == 5

    def test_add_encoded_leaves_invalid_type_raises_error(self):
        """Test adding non-list raises error."""
        tree = MerkleTree("nat")
        with pytest.raises(InvalidLeafError, match="must be a list"):
            tree.add_encoded_leaves("not a list")

    def test_add_encoded_leaves_with_non_bytes_raises_error(self):
        """Test adding list with non-bytes items raises error."""
        tree = MerkleTree("nat")
        with pytest.raises(InvalidLeafError, match="must be bytes"):
            tree.add_encoded_leaves([b"valid", "invalid", b"valid"])

    def test_add_leaves_resets_built_flag(self):
        """Test that adding leaves resets the built flag."""
        tree = MerkleTree("nat")
        tree.add_leaves([1, 2, 3])
        tree.build()
        assert tree._built is True
        tree.add_leaf(4)
        assert tree._built is False


class TestCalculateTree:
    """Tests for tree calculation."""

    def test_build_with_empty_leaves_raises_error(self):
        """Test calculating tree with no leaves raises error."""
        tree = MerkleTree("nat")
        with pytest.raises(EmptyTreeError, match="no leaves added"):
            tree.build()

    def test_build_single_leaf(self):
        """Test calculating tree with single leaf."""
        tree = MerkleTree("nat")
        tree.add_leaf(42)
        tree.build()
        assert tree._built is True
        assert len(tree._levels) == 1

    def test_build_multiple_leaves(self):
        """Test calculating tree with multiple leaves."""
        tree = MerkleTree("nat")
        tree.add_leaves([1, 2, 3, 4])
        tree.build()
        assert tree._built is True
        assert len(tree._levels) > 1

    def test_build_odd_leaves(self):
        """Test calculating tree with odd number of leaves."""
        tree = MerkleTree("nat")
        tree.add_leaves([1, 2, 3])
        tree.build()
        assert tree._built is True

    def test_build_many_leaves(self):
        """Test calculating tree with many leaves."""
        tree = MerkleTree("nat")
        tree.add_leaves(list(range(100)))
        tree.build()
        assert tree._built is True


class TestMerkleRoot:
    """Tests for merkle root property."""

    def test_merkle_root_before_building_raises_error(self):
        """Test accessing merkle_root before building raises error."""
        tree = MerkleTree("nat")
        tree.add_leaf(1)
        with pytest.raises(TreeNotBuiltError, match="not built"):
            _ = tree.merkle_root

    def test_merkle_root_returns_bytes(self):
        """Test merkle_root returns bytes."""
        tree = MerkleTree("nat")
        tree.add_leaves([1, 2, 3])
        tree.build()
        root = tree.merkle_root
        assert isinstance(root, bytes)
        assert len(root) == 32  # SHA256 default

    def test_merkle_root_deterministic(self):
        """Test merkle_root is deterministic."""
        tree1 = MerkleTree("nat")
        tree1.add_leaves([1, 2, 3, 4])
        tree1.build()

        tree2 = MerkleTree("nat")
        tree2.add_leaves([1, 2, 3, 4])
        tree2.build()

        assert tree1.merkle_root == tree2.merkle_root

    def test_merkle_root_different_for_different_data(self):
        """Test merkle_root differs for different data."""
        tree1 = MerkleTree("nat")
        tree1.add_leaves([1, 2, 3])
        tree1.build()

        tree2 = MerkleTree("nat")
        tree2.add_leaves([4, 5, 6])
        tree2.build()

        assert tree1.merkle_root != tree2.merkle_root


class TestGetProof:
    """Tests for proof generation with unencoded leaves."""

    def test_get_proof_before_building_raises_error(self):
        """Test get_proof before building raises error."""
        tree = MerkleTree("nat")
        tree.add_leaf(1)
        with pytest.raises(TreeNotBuiltError, match="not built"):
            tree.get_proof(1)

    def test_get_proof_with_unknown_leaf_raises_error(self):
        """Test get_proof with unknown leaf raises error."""
        tree = MerkleTree("nat")
        tree.add_leaves([1, 2, 3])
        tree.build()
        with pytest.raises(LeafNotFoundError, match="not found"):
            tree.get_proof(999)

    def test_get_proof_returns_list(self):
        """Test get_proof returns list of bytes."""
        tree = MerkleTree("nat")
        tree.add_leaves([1, 2, 3, 4])
        tree.build()
        proof = tree.get_proof(1)
        assert isinstance(proof, list)
        assert all(isinstance(p, bytes) for p in proof)

    def test_get_proof_single_leaf(self):
        """Test get_proof with single leaf returns empty proof."""
        tree = MerkleTree("nat")
        tree.add_leaf(1)
        tree.build()
        proof = tree.get_proof(1)
        assert len(proof) == 0

    def test_get_proof_multiple_leaves(self):
        """Test get_proof with multiple leaves."""
        tree = MerkleTree("nat")
        tree.add_leaves([1, 2, 3, 4])
        tree.build()
        proof = tree.get_proof(1)
        assert len(proof) > 0

    def test_get_proof_with_string_type(self):
        """Test get_proof with string type."""
        tree = MerkleTree("string")
        tree.add_leaves(["alice", "bob", "charlie"])
        tree.build()
        proof = tree.get_proof("bob")
        assert isinstance(proof, list)
        assert all(isinstance(p, bytes) for p in proof)

    def test_get_proof_with_invalid_leaf_raises_error(self):
        """Test get_proof with invalid leaf type raises error."""
        tree = MerkleTree("nat")
        tree.add_leaves([1, 2, 3])
        tree.build()
        with pytest.raises(InvalidLeafError, match="Failed to encode"):
            tree.get_proof("not a nat")


class TestGetProofFromEncoded:
    """Tests for proof generation with encoded leaves."""

    def test_get_proof_from_encoded_before_building_raises_error(self):
        """Test get_proof_from_encoded before building raises error."""
        tree = MerkleTree("nat")
        tree.add_leaf(1)
        encoded = tree.encode_raw_leaf(1)
        with pytest.raises(TreeNotBuiltError, match="not built"):
            tree.get_proof_from_encoded(encoded)

    def test_get_proof_from_encoded_with_non_bytes_raises_error(self):
        """Test get_proof_from_encoded with non-bytes raises error."""
        tree = MerkleTree("nat")
        tree.add_leaf(1)
        tree.build()
        with pytest.raises(InvalidLeafError, match="must be bytes"):
            tree.get_proof_from_encoded(1)

    def test_get_proof_from_encoded_with_unknown_leaf_raises_error(self):
        """Test get_proof_from_encoded with unknown leaf raises error."""
        tree = MerkleTree("nat")
        tree.add_leaves([1, 2, 3])
        tree.build()
        encoded = tree.encode_raw_leaf(999)
        with pytest.raises(LeafNotFoundError, match="not found"):
            tree.get_proof_from_encoded(encoded)

    def test_get_proof_from_encoded_returns_list(self):
        """Test get_proof_from_encoded returns list of bytes."""
        tree = MerkleTree("nat")
        tree.add_leaves([1, 2, 3, 4])
        tree.build()
        encoded = tree.encode_raw_leaf(1)
        proof = tree.get_proof_from_encoded(encoded)
        assert isinstance(proof, list)
        assert all(isinstance(p, bytes) for p in proof)

    def test_get_proof_from_encoded_single_leaf(self):
        """Test get_proof_from_encoded with single leaf returns empty proof."""
        tree = MerkleTree("nat")
        tree.add_leaf(1)
        tree.build()
        encoded = tree.encode_raw_leaf(1)
        proof = tree.get_proof_from_encoded(encoded)
        assert len(proof) == 0

    def test_get_proof_from_encoded_multiple_leaves(self):
        """Test get_proof_from_encoded with multiple leaves."""
        tree = MerkleTree("nat")
        tree.add_leaves([1, 2, 3, 4])
        tree.build()
        encoded = tree.encode_raw_leaf(1)
        proof = tree.get_proof_from_encoded(encoded)
        assert len(proof) > 0

    def test_get_proof_methods_return_same_result(self):
        """Test that get_proof and get_proof_from_encoded return same result."""
        tree = MerkleTree("nat")
        tree.add_leaves([1, 2, 3, 4])
        tree.build()
        encoded = tree.encode_raw_leaf(2)
        proof1 = tree.get_proof(2)
        proof2 = tree.get_proof_from_encoded(encoded)
        assert proof1 == proof2


class TestSerialization:
    """Tests for serialization and deserialization."""

    def test_serialise_before_building_raises_error(self, tmp_path):
        """Test serialise before building raises error."""
        tree = MerkleTree("nat")
        tree.add_leaf(1)
        path = tmp_path / "tree.json"
        with pytest.raises(TreeNotBuiltError, match="not built"):
            tree.serialise(path)

    def test_serialise_basic(self, tmp_path):
        """Test basic serialization."""
        tree = MerkleTree("nat")
        tree.add_leaves([1, 2, 3])
        tree.build()
        path = tmp_path / "tree.json"
        tree.serialise(path)
        assert path.exists()

    def test_serialise_with_tree(self, tmp_path):
        """Test serialization with tree included."""
        tree = MerkleTree("nat")
        tree.add_leaves([1, 2, 3])
        tree.build()
        path = tmp_path / "tree.json"
        tree.serialise(path, include_tree=True)
        assert path.exists()

    def test_serialise_with_proofs(self, tmp_path):
        """Test serialization with proofs included."""
        tree = MerkleTree("nat")
        tree.add_leaves([1, 2, 3])
        tree.build()
        path = tmp_path / "tree.json"
        tree.serialise(path, include_proofs=True)
        assert path.exists()

    def test_from_file_basic(self, tmp_path):
        """Test loading from file."""
        tree = MerkleTree("nat")
        tree.add_leaves([1, 2, 3])
        tree.build()
        path = tmp_path / "tree.json"
        tree.serialise(path)

        loaded_tree = MerkleTree.from_file(path)
        assert loaded_tree._leaf_type_micheline == tree._leaf_type_micheline
        assert loaded_tree._leaves == tree._leaves

    def test_from_file_with_tree(self, tmp_path):
        """Test loading from file with tree included."""
        tree = MerkleTree("nat")
        tree.add_leaves([1, 2, 3])
        tree.build()
        path = tmp_path / "tree.json"
        tree.serialise(path, include_tree=True)

        loaded_tree = MerkleTree.from_file(path)
        assert loaded_tree._built is True
        assert loaded_tree.merkle_root == tree.merkle_root

    def test_from_file_nonexistent_raises_error(self):
        """Test loading from nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            MerkleTree.from_file("/nonexistent/path.json")

    def test_from_file_invalid_json_raises_error(self, tmp_path):
        """Test loading from invalid JSON raises error."""
        path = tmp_path / "invalid.json"
        path.write_text("not valid json {")
        with pytest.raises(ValueError, match="Invalid JSON"):
            MerkleTree.from_file(path)


class TestEncoding:
    """Tests for leaf encoding."""

    def test_encode_raw_leaf(self):
        """Test encoding a leaf."""
        tree = MerkleTree("nat")
        encoded = tree.encode_raw_leaf(42)
        assert isinstance(encoded, bytes)

    def test_encode_raw_leaf_invalid_raises_error(self):
        """Test encoding invalid leaf raises error."""
        tree = MerkleTree("nat")
        with pytest.raises(InvalidLeafError, match="Failed to encode"):
            tree.encode_raw_leaf("not a nat")


class TestComplexTypes:
    """Tests with complex Michelson types."""

    def test_string_type(self):
        """Test tree with string type."""
        tree = MerkleTree("string")
        tree.add_leaves(["hello", "world", "tezos"])
        tree.build()
        assert tree._built is True

    def test_pair_type(self):
        """Test tree with pair type."""
        tree = MerkleTree("pair nat string")
        tree.add_leaves([(1, "one"), (2, "two"), (3, "three")])
        tree.build()
        assert tree._built is True
