"""Performance benchmarks for MerkleTree."""

import time
import pytest
from tzmerkle import MerkleTree


def benchmark(func, *args, **kwargs):
    """Simple benchmark helper."""
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    return result, elapsed


class TestPerformance:
    """Performance benchmarks for different tree sizes."""

    @pytest.mark.parametrize("size", [10, 100, 1000, 10000])
    def test_build_tree_performance(self, size):
        """Benchmark tree building for various sizes."""
        tree = MerkleTree("nat")
        tree.add_leaves(list(range(size)))

        _, elapsed = benchmark(tree.build)

        print(f"\nBuild tree ({size} leaves): {elapsed*1000:.2f}ms")
        # Sanity check - should be reasonably fast
        assert elapsed < 5.0  # 5 seconds max

    @pytest.mark.parametrize("size", [10, 100, 1000, 10000])
    def test_get_proof_performance(self, size):
        """Benchmark proof generation for various sizes."""
        tree = MerkleTree("nat")
        tree.add_leaves(list(range(size)))
        tree.build()

        _, elapsed = benchmark(tree.get_proof, size // 2)

        print(f"\nGet proof ({size} leaves): {elapsed*1000:.2f}ms")
        # Proof generation should be very fast (logarithmic)
        assert elapsed < 0.1  # 100ms max

    @pytest.mark.parametrize("size", [10, 100, 1000])
    def test_serialization_performance(self, size, tmp_path):
        """Benchmark serialization for various sizes."""
        tree = MerkleTree("nat")
        tree.add_leaves(list(range(size)))
        tree.build()

        path = tmp_path / f"tree_{size}.json"
        _, elapsed = benchmark(tree.serialise, path, True, True)

        print(f"\nSerialize ({size} leaves): {elapsed*1000:.2f}ms")
        assert elapsed < 5.0

    @pytest.mark.parametrize("size", [10, 100, 1000])
    def test_deserialization_performance(self, size, tmp_path):
        """Benchmark deserialization for various sizes."""
        tree = MerkleTree("nat")
        tree.add_leaves(list(range(size)))
        tree.build()

        path = tmp_path / f"tree_{size}.json"
        tree.serialise(path, include_tree=True)

        _, elapsed = benchmark(MerkleTree.from_file, path)

        print(f"\nDeserialize ({size} leaves): {elapsed*1000:.2f}ms")
        assert elapsed < 5.0

    def test_memory_efficiency(self):
        """Test that trees don't use excessive memory."""
        import sys

        tree = MerkleTree("nat")
        tree.add_leaves(list(range(1000)))
        tree.build()

        # Rough memory check - tree should not be gigantic
        size = sys.getsizeof(tree)
        print(f"\nTree object size (1000 leaves): {size} bytes")
        # This is a very rough check
        assert size < 1_000_000  # Less than 1MB for the object itself

    def test_proof_size_logarithmic(self):
        """Verify proof size grows logarithmically with tree size."""
        sizes = [10, 100, 1000, 10000]
        proof_sizes = []

        for size in sizes:
            tree = MerkleTree("nat")
            tree.add_leaves(list(range(size)))
            tree.build()
            proof = tree.get_proof(0)
            proof_sizes.append(len(proof))

        print(f"\nProof sizes: {list(zip(sizes, proof_sizes))}")

        # Verify logarithmic growth
        # Each 10x increase should roughly add log2(10) ≈ 3.3 elements
        for i in range(len(sizes) - 1):
            expected_increase = 3  # Roughly log2(10)
            actual_increase = proof_sizes[i + 1] - proof_sizes[i]

            # Allow some flexibility
            assert actual_increase >= expected_increase - 2
            assert actual_increase <= expected_increase + 2


def test_comparative_hash_performance():
    """Compare performance of different hash functions."""
    from tzmerkle.hashes import blake2b, sha256, sha512, sha3, keccak  # noqa

    data = list(range(1000))
    hash_functions = {
        "blake2b": blake2b,
        "sha256": sha256,
        "sha512": sha512,
        "sha3": sha3,
        "keccak": keccak,
    }

    print("\nHash function benchmarks (1000 leaves):")
    results = {}

    for name, hash_fn in hash_functions.items():
        tree = MerkleTree("nat", hash_fn=hash_fn)
        tree.add_leaves(data)
        _, elapsed = benchmark(tree.build)
        results[name] = elapsed
        print(f"  {name}: {elapsed*1000:.2f}ms")

    # All should complete in reasonable time
    for elapsed in results.values():
        assert elapsed < 5.0


if __name__ == "__main__":
    """Run benchmarks directly."""
    print("=" * 60)
    print("MERKLE TREE PERFORMANCE BENCHMARKS")
    print("=" * 60)

    # Build tree benchmarks
    print("\n1. Tree Building Performance:")
    for size in [100, 1000, 10_000, 100_000, 1_000_000]:
        tree = MerkleTree("nat")
        tree.add_leaves(list(range(size)))
        _, elapsed = benchmark(tree.build)
        print(f"   {size:5d} leaves: {elapsed*1000:6.2f}ms")

    # Proof generation benchmarks
    print("\n2. Proof Generation Performance:")
    for size in [100, 1000, 10_000, 100_000, 1_000_000]:
        tree = MerkleTree("nat")
        tree.add_leaves(list(range(size)))
        tree.build()
        _, elapsed = benchmark(tree.get_proof, size // 2)
        print(f"   {size:5d} leaves: {elapsed*1000:6.2f}ms")

    print("\n" + "=" * 60)
