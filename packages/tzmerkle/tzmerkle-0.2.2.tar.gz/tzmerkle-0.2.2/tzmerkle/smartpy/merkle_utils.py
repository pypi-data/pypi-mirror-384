import smartpy as sp
from tzmerkle import MerkleTree
from tzmerkle.hashes import sha256, sha512, sha3, blake2b, keccak


@sp.module
def verify_merkle_proof():
    def sha256(params) -> sp.bytes:
        computed_hash = sp.sha256(params.leaf)
        for proof_element in params.proof:
            if computed_hash < proof_element:
                computed_hash = sp.sha256(computed_hash + proof_element)
            else:
                computed_hash = sp.sha256(proof_element + computed_hash)
        return computed_hash

    def sha512(params) -> sp.bytes:
        computed_hash = sp.sha512(params.leaf)
        for proof_element in params.proof:
            if computed_hash < proof_element:
                computed_hash = sp.sha512(computed_hash + proof_element)
            else:
                computed_hash = sp.sha512(proof_element + computed_hash)
        return computed_hash

    def sha3(params) -> sp.bytes:
        computed_hash = sp.sha3(params.leaf)
        for proof_element in params.proof:
            if computed_hash < proof_element:
                computed_hash = sp.sha3(computed_hash + proof_element)
            else:
                computed_hash = sp.sha3(proof_element + computed_hash)
        return computed_hash

    def blake2b(params) -> sp.bytes:
        computed_hash = sp.blake2b(params.leaf)
        for proof_element in params.proof:
            if computed_hash < proof_element:
                computed_hash = sp.blake2b(computed_hash + proof_element)
            else:
                computed_hash = sp.blake2b(proof_element + computed_hash)
        return computed_hash

    def keccak(params) -> sp.bytes:
        computed_hash = sp.keccak(params.leaf)
        for proof_element in params.proof:
            if computed_hash < proof_element:
                computed_hash = sp.keccak(computed_hash + proof_element)
            else:
                computed_hash = sp.keccak(proof_element + computed_hash)
        return computed_hash


if __name__ == "__main__":

    @sp.add_test()
    def _():
        s = sp.test_scenario(".smartpy/tests/sha256")
        mt = MerkleTree("nat", sha256)
        for i in range(13):
            mt.add_leaf(i)

        mt.build()
        for leaf in range(13):
            s.verify(
                verify_merkle_proof.sha256(
                    sp.record(
                        proof=mt.get_proof_spy(leaf),
                        leaf=mt.encode_raw_leaf_spy(leaf),
                    )
                )
                == mt.merkle_root_spy
            )

    @sp.add_test()
    def _():
        s = sp.test_scenario(".smartpy/tests/sha512")
        mt = MerkleTree("nat", sha512)
        for i in range(13):
            mt.add_leaf(i)

        mt.build()
        for leaf in range(13):
            s.verify(
                verify_merkle_proof.sha512(
                    sp.record(
                        proof=mt.get_proof_spy(leaf),
                        leaf=mt.encode_raw_leaf_spy(leaf),
                    )
                )
                == mt.merkle_root_spy
            )

    @sp.add_test()
    def _():
        s = sp.test_scenario(".smartpy/tests/sha3")
        mt = MerkleTree("nat", sha3)
        for i in range(13):
            mt.add_leaf(i)

        mt.build()
        for leaf in range(13):
            s.verify(
                verify_merkle_proof.sha3(
                    sp.record(
                        proof=mt.get_proof_spy(leaf),
                        leaf=mt.encode_raw_leaf_spy(leaf),
                    )
                )
                == mt.merkle_root_spy
            )

    @sp.add_test()
    def _():
        s = sp.test_scenario(".smartpy/tests/blake2b")
        mt = MerkleTree("nat", blake2b)
        for i in range(13):
            mt.add_leaf(i)

        mt.build()
        for leaf in range(13):
            s.verify(
                verify_merkle_proof.blake2b(
                    sp.record(
                        proof=mt.get_proof_spy(leaf),
                        leaf=mt.encode_raw_leaf_spy(leaf),
                    )
                )
                == mt.merkle_root_spy
            )

    @sp.add_test()
    def _():
        s = sp.test_scenario(".smartpy/tests/keccak")
        mt = MerkleTree("nat", keccak)
        for i in range(13):
            mt.add_leaf(i)

        mt.build()
        for leaf in range(13):
            s.verify(
                verify_merkle_proof.keccak(
                    sp.record(
                        proof=mt.get_proof_spy(leaf), leaf=mt.encode_raw_leaf_spy(leaf)
                    )
                )
                == mt.merkle_root_spy
            )
