# akm/core/services/merkle_tree_builder.py

import logging
from typing import List, Optional

from akm.core.utils.crypto_utility import CryptoUtility

logger = logging.getLogger(__name__)

class MerkleTreeBuilder:

    @staticmethod
    def build(transaction_hashes: List[str]) -> str:

        if not transaction_hashes:
            return CryptoUtility.double_sha256("")

        hashes = transaction_hashes[:]

        if len(hashes) == 1: return hashes[0]

        if len(hashes) % 2 != 0: hashes.append(hashes[-1])

        new_level: List[str] = []

        for i in range(0, len(hashes), 2):
            left = hashes[i]
            right = hashes[i+1]
            combined = left + right
            new_hash = CryptoUtility.double_sha256(combined)
            new_level.append(new_hash)

        return MerkleTreeBuilder.build(new_level)

    @staticmethod
    def get_proof(tx_hashes: List[str], target_tx_hash: str) -> Optional[List[str]]:

        if target_tx_hash not in tx_hashes:
            return None
            
        proof: List[str] = []
        
        try:
            idx = tx_hashes.index(target_tx_hash)
        except ValueError:
            return None
            
        current_level = tx_hashes[:]
        
        while len(current_level) > 1:
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1])
                
            is_right_child = (idx % 2 != 0)
            sibling_idx = idx - 1 if is_right_child else idx + 1
            
            sibling_hash = current_level[sibling_idx]
            
            direction = "L" if is_right_child else "R" 
            proof.append(f"{direction}|{sibling_hash}")
            
            next_level: List[str] = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i+1]
                combined = left + right
                new_hash = CryptoUtility.double_sha256(combined)
                next_level.append(new_hash)
            
            current_level = next_level
            idx = idx // 2
            
        return proof

    @staticmethod
    def verify_proof(tx_hash: str, merkle_root: str, proof: List[str]) -> bool:
        try:
            current_hash = tx_hash
            for item in proof:
                direction, sibling_hash = item.split('|')
                combined = sibling_hash + current_hash if direction == "L" else current_hash + sibling_hash
                current_hash = CryptoUtility.double_sha256(combined)
            
            is_valid = current_hash == merkle_root
            
            status = "válida" if is_valid else "inválida"
            logger.info(f"Merkle Proof {status} para TX {tx_hash[:8]}.")
            
            return is_valid
        except Exception:
            logger.exception("Error en verificación técnica de Merkle Proof")
            return False