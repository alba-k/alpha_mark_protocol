# akm/core/services/merkle_tree_builder.py
'''
class MerkleTreeBuilder:
    Servicio de dominio encargado de generar la Raíz de Merkle.

    Methods::
        build(transaction_hashes) -> str:
            Calcula la raíz recursivamente usando Doble SHA-256.
'''

from typing import List
from akm.core.utils.crypto_utility import CryptoUtility

class MerkleTreeBuilder:

    @staticmethod
    def build(transaction_hashes: List[str]) -> str:

        if not transaction_hashes:
            return CryptoUtility.double_sha256("")

        if len(transaction_hashes) == 1:
            return transaction_hashes[0]

        new_level: List[str] = []

        for i in range(0, len(transaction_hashes), 2):
            left = transaction_hashes[i]
            
            if i + 1 < len(transaction_hashes):
                right = transaction_hashes[i + 1]
            else:
                right = left

            combined = left + right
            new_hash = CryptoUtility.double_sha256(combined)
            new_level.append(new_hash)

        return MerkleTreeBuilder.build(new_level)