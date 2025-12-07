# akm/core/validators/block_validator.py
'''
class BlockValidator:
    Especialista en la validación estructural y criptográfica del bloque (Stateless).
    Verifica la integridad del encabezado, la Raíz de Merkle y la Prueba de Trabajo (PoW).

    Methods::
        validate_structure(block) -> bool:
            Verifica hash del bloque y consistencia del Merkle Root.
        validate_pow(block) -> bool:
            Verifica que el hash cumpla con la dificultad (bits) declarada.
'''

import logging

# Dependencias de Dominio
from akm.core.models.block import Block
from akm.core.services.block_hasher import BlockHasher
from akm.core.services.merkle_tree_builder import MerkleTreeBuilder
from akm.core.utils.difficulty_utils import DifficultyUtils

logging.basicConfig(level=logging.INFO, format='[BlockValidator] %(message)s')

class BlockValidator:

    @staticmethod
    def validate_structure(block: Block) -> bool:

        calculated_hash = BlockHasher.calculate(block)
        if calculated_hash != block.hash:
            logging.error(f"Integridad Fallida: Hash calculado {calculated_hash[:8]} != declarado {block.hash[:8]}")
            return False

        if not block.transactions:
            logging.error("Estructura Fallida: El bloque no tiene transacciones.")
            return False

        tx_hashes = [tx.tx_hash for tx in block.transactions]
        calculated_root = MerkleTreeBuilder.build(tx_hashes)
        
        if calculated_root != block.merkle_root:
            logging.error(f"Merkle Root Fallida: Calculada {calculated_root[:8]} != Declarada {block.merkle_root[:8]}")
            return False

        return True

    @staticmethod
    def validate_pow(block: Block) -> bool:

        try:
            target = DifficultyUtils.bits_to_target(block.bits)
            block_hash_int = int(block.hash, 16)

            if block_hash_int > target:
                logging.error(f"PoW Fallido: Hash {block.hash[:8]} excede el target.")
                return False

            return True

        except Exception as e:
            logging.error(f"Error validando PoW: {e}")
            return False