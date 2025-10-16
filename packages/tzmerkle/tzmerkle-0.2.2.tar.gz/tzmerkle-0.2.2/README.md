# tzmerkle

A Merkle tree implementation for Tezos blockchain applications.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🔐 **Multiple hash functions** (SHA256, SHA512, SHA3, BLAKE2b, Keccak)
- 🎯 **Tezos-native** support with Michelson type encoding
- 🔗 **SmartPy integration** for on-chain verification
- 💾 **Serialization** support for tree persistence
- ✅ **Fully typed** with comprehensive type hints

## Installation

```bash
pip install tzmerkle
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from tzmerkle import MerkleTree
from tzmerkle.hashes import blake2b

# Create a tree for natural numbers
tree = MerkleTree("nat", hash_fn=blake2b)

# Add leaves
tree.add_leaves([1, 2, 3, 4, 5])

# Build the tree
tree.build()

# Get the root hash
root = tree.merkle_root
print(f"Root: {root.hex()}")

# Generate a proof for a leaf (automatically encodes the leaf)
proof = tree.get_proof(3)
print(f"Proof length: {len(proof)}")
```

## Usage Examples

### Working with Different Types

```python
from tzmerkle import MerkleTree

# String type
tree = MerkleTree("string")
tree.add_leaves(["alice", "bob", "charlie"])
tree.build()

# Complex types (pairs)
tree = MerkleTree("pair nat string")
tree.add_leaves([
    (1, "alice"),
    (2, "bob"),
    (3, "charlie")
])
tree.build()
```

### Using Different Hash Functions

```python
from tzmerkle import MerkleTree
from tzmerkle.hashes import blake2b, sha512, keccak

# BLAKE2b
tree = MerkleTree("nat", hash_fn=blake2b)

# SHA512
tree = MerkleTree("nat", hash_fn=sha512)

# Keccak (Ethereum-compatible)
tree = MerkleTree("nat", hash_fn=keccak)
```

### Proof Generation and Verification

```python
from tzmerkle import MerkleTree

tree = MerkleTree("nat")
tree.add_leaves(list(range(100)))
tree.build()

# Get proof for a specific leaf (unencoded)
leaf_value = 42
proof = tree.get_proof(leaf_value)

print(f"Proof size: {len(proof)} hashes")
print(f"Root: {tree.merkle_root.hex()}")

# Or use pre-encoded leaf
encoded_leaf = tree.encode_raw_leaf(leaf_value)
proof = tree.get_proof_from_encoded(encoded_leaf)
```

### SmartPy Integration

```python
import smartpy as sp
from tzmerkle import MerkleTree
from tzmerkle.hashes import blake2b
from tzmerkle.smartpy.merkle_utils import verify_merkle_proof

# Use in SmartPy contract
@sp.module
def my_module():
    import verify_merkle_proof

    class MyContract(sp.Contract):
        def __init__(self, merkle_root):
            self.data.merkle_root = merkle_root

        @sp.entrypoint
        def verify(self, leaf: sp.bytes, proof: sp.list[sp.bytes]):
            assert self.data.merkle_root == verify_merkle_proof.blake2b(sp.record(
                leaf=leaf,
                proof=proof
            ))

@sp.add_test()
def _():
    s = sp.test_scenario("/tmp/test")

    # Create and build tree
    tree = MerkleTree("nat", hash_fn=blake2b)
    tree.add_leaves([1, 2, 3, 4])
    tree.build()

    c = my_module.MyContract(tree.merkle_root_spy)

    s += c

    leaf_raw = 1
    proof_spy = tree.get_proof_spy(leaf_raw)
    c.verify(sp.record(leaf=tree.encode_raw_leaf_spy(leaf_raw), proof=proof_spy))
```

### Serialization and Persistence

```python
from tzmerkle import MerkleTree
from pathlib import Path

# Create and save tree
tree = MerkleTree("nat")
tree.add_leaves(range(1000))
tree.build()

# Save with tree structure for fast loading
tree.serialise("tree.json", include_tree=True, include_proofs=True)

# Load from file
loaded_tree = MerkleTree.from_file("tree.json")
print(f"Loaded {len(loaded_tree._leaves)} leaves")
print(f"Root matches: {loaded_tree.merkle_root == tree.merkle_root}")
```

### Error Handling

```python
from tzmerkle import (
    MerkleTree,
    EmptyTreeError,
    TreeNotBuiltError,
    LeafNotFoundError,
    InvalidLeafError
)

tree = MerkleTree("nat")

# Proper error handling
try:
    tree.build()
except EmptyTreeError:
    print("Add leaves before building!")

try:
    root = tree.merkle_root
except TreeNotBuiltError:
    print("Build tree first!")

tree.add_leaves([1, 2, 3])
tree.build()

try:
    proof = tree.get_proof(999)
except LeafNotFoundError:
    print("Leaf not in tree!")
```

## API Reference

### MerkleTree

#### Constructor

```python
MerkleTree(leaf_type: str, hash_fn: TezosHash = blake2b)
```

Create a new Merkle tree.

- `leaf_type`: Michelson type string (e.g., "nat", "string", "pair nat string")
- `hash_fn`: Hash function from `tzmerkle.hashes`

#### Methods

- `add_leaf(leaf)` - Add a single leaf (auto-encoded)
- `add_leaves(leaves)` - Add multiple leaves (auto-encoded)
- `add_encoded_leaf(leaf: bytes)` - Add pre-encoded leaf
- `add_encoded_leaves(leaves: List[bytes])` - Add pre-encoded leaves
- `encode_raw_leaf(leaf) -> bytes` - Encode a leaf to bytes
- `build()` - Build the Merkle tree
- `get_proof(leaf) -> List[bytes]` - Generate proof for an unencoded leaf
- `get_proof_from_encoded(leaf: bytes) -> List[bytes]` - Generate proof for an encoded leaf
- `get_proof_spy(leaf) -> List[sp.bytes]` - Generate SmartPy proof for an unencoded leaf
- `get_proof_from_encoded_spy(leaf: bytes) -> List[sp.bytes]` - Generate SmartPy proof for an encoded leaf
- `serialise(path, include_tree=False, include_proofs=False)` - Save to file
- `from_file(path) -> MerkleTree` - Load from file (class method)

#### Properties

- `merkle_root: bytes` - Get the root hash
- `merkle_root_spy: sp.bytes` - Get root for SmartPy

### Hash Functions

All hash functions follow the same interface:

```python
from tzmerkle.hashes import sha256, sha512, sha3, blake2b, keccak

# Use as function
digest = blake2b(b"data")

# Get hex digest
hex_digest = blake2b.hexdigest(b"data")

# Properties
print(blake2b.name)          # "blake2b"
print(blake2b.digest_size)   # 32
```

## Exceptions

- `MerkleTreeError` - Base exception
- `EmptyTreeError` - Tree has no leaves
- `TreeNotBuiltError` - Tree not calculated yet
- `LeafNotFoundError` - Leaf not in tree
- `InvalidLeafError` - Invalid leaf data or encoding

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/objkt-com/tzmerkle.git
cd tzmerkle

# Install with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=tzmerkle --cov-report=html

# Verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black tzmerkle tests

# Lint
flake8 tzmerkle tests
```

## Performance

Benchmark results for various tree sizes:

| Operation    | 100 leaves | 1,000 leaves | 10,000 leaves |
| ------------ | ---------- | ------------ | ------------- |
| Build tree   | 5ms        | 50ms         | 520ms         |
| Get proof    | <1ms       | <1ms         | <1ms          |
| Verify proof | <1ms       | <1ms         | <1ms          |

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Credits

Developed by [objkt.com](https://objkt.com) for the Tezos ecosystem.

## Links

- [GitHub Repository](https://github.com/objkt-com/tzmerkle)
- [Issue Tracker](https://github.com/objkt-com/tzmerkle/issues)
- [PyPI Package](https://pypi.org/project/tzmerkle/)
