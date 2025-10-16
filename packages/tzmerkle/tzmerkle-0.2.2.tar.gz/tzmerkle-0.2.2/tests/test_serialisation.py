from tzmerkle import MerkleTree
from tzmerkle.hashes import sha256


def test_serialisation(tmp_path):
    """Test that MerkleBuilder can be instantiated and add a leaf."""
    # Create a simple Michelson type (e.g., nat)

    # Instantiate MerkleBuilder
    mt = MerkleTree(leaf_type="nat", hash_fn=sha256)
    mt.add_leaves([i for i in range(1000)])
    mt.build()

    path = tmp_path / "tree.json"

    mt.serialise(path)
    restored = MerkleTree.from_file(path)

    assert restored._leaves == mt._leaves
    assert restored._leaf_type_micheline == mt._leaf_type_micheline
    assert restored._levels == []
    assert restored._built is False

    mt.serialise(path, include_tree=True)
    restored = MerkleTree.from_file(path)

    assert restored._leaves == mt._leaves
    assert restored._leaf_type_micheline == mt._leaf_type_micheline
    assert restored._levels == mt._levels
    assert restored._built is True
