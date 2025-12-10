# akm/core/services/merkle_tree_builder.py

from typing import List, Optional
from akm.core.utils.crypto_utility import CryptoUtility

class MerkleTreeBuilder:
    """
    Servicio de dominio para la integridad de datos.
    Calcula raíces y pruebas de inclusión (Merkle Proofs).
    """

    @staticmethod
    def build(transaction_hashes: List[str]) -> str:
        """Construye la raíz de Merkle recursivamente."""
        if not transaction_hashes:
            return CryptoUtility.double_sha256("")

        # Copia de seguridad para no mutar la lista original
        hashes = transaction_hashes[:]

        if len(hashes) == 1:
            return hashes[0]

        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])

        # Tipado explícito para la lista del siguiente nivel
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
        """
        [FullNode] Genera la ruta de hashes necesaria para probar que target_tx_hash existe.
        Retorna una lista de strings con formato "L|HASH" o "R|HASH".
        """
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
                
            # Lógica de hermano (Merkle Sibling)
            is_right_child = (idx % 2 != 0)
            sibling_idx = idx - 1 if is_right_child else idx + 1
            
            sibling_hash = current_level[sibling_idx]
            
            # Guardamos dirección para reconstruir: L|HASH o R|HASH
            # Si soy hijo derecho, necesito concatenar con mi hermano IZQUIERDO (L)
            # Si soy hijo izquierdo, necesito concatenar con mi hermano DERECHO (R)
            direction = "L" if is_right_child else "R" 
            proof.append(f"{direction}|{sibling_hash}")
            
            # Subir de nivel
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
        """
        [SPVNode] Recalcula la raíz usando la prueba y la compara con la esperada.
        """
        current_hash = tx_hash
        
        for item in proof:
            direction, sibling_hash = item.split('|')
            
            if direction == "L": # El hermano está a la Izquierda
                combined = sibling_hash + current_hash
            else:                # El hermano está a la Derecha
                combined = current_hash + sibling_hash
                
            current_hash = CryptoUtility.double_sha256(combined)
            
        return current_hash == merkle_root