# akm/core/validators/block_validator.py

import logging

# Dependencias del Proyecto
from akm.core.models.block import Block
from akm.core.services.block_hasher import BlockHasher
from akm.core.services.merkle_tree_builder import MerkleTreeBuilder
from akm.core.utils.difficulty_utils import DifficultyUtils

logger = logging.getLogger(__name__)

class BlockValidator:

    @staticmethod
    def validate_structure(block: Block) -> bool: 
        try:
            calculated_hash = BlockHasher.calculate(block)
            if calculated_hash != block.hash: 
                logger.info(f"Fallo Integridad: {block.hash[:8]} (Calculado: {calculated_hash[:8]})")
                return False

            if not block.transactions:
                logger.info(f"Fallo Estructura: Bloque {block.hash[:8]} sin transacciones.")
                return False

            tx_hashes = [tx.tx_hash for tx in block.transactions]
            calculated_root = MerkleTreeBuilder.build(tx_hashes)
            
            if calculated_root != block.merkle_root:
                logger.info(f"Fallo Merkle: {block.merkle_root[:8]} (Calculada: {calculated_root[:8]})")
                return False

            return True

        except Exception:
            logger.exception(f"Bug en validación estructural del bloque {block.index}")
            return False

    @staticmethod
    def validate_pow(block: Block) -> bool:
        try:
            target = DifficultyUtils.bits_to_target(block.bits)
            block_hash_int = int(block.hash, 16)

            if block_hash_int > target:
                logger.info(f"Fallo PoW: Hash {block.hash[:]} por encima del target.")
                return False

            return True

        except Exception:
            logger.exception(f"Bug en validación de PoW para bloque {block.index}")
            return False