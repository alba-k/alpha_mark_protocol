# akm/core/builders/block_builder.py
'''
class BlockBuilder:
    Construye un bloque válido encontrando un nonce que satisfaga la dificultad.

    Methods::
        build(transactions, previous_hash, bits, height) -> Block:
            Ejecuta la minería (búsqueda de hash) y retorna el bloque sellado.
'''

import time
import logging
from typing import List

# Modelos y Configuración
from akm.core.models.block import Block
from akm.core.models.transaction import Transaction
from akm.core.config.config_manager import ConfigManager

# Servicios de Dominio
from akm.core.services.merkle_tree_builder import MerkleTreeBuilder
from akm.core.services.block_hasher import BlockHasher
from akm.core.utils.difficulty_utils import DifficultyUtils

# Configuración de log
logging.basicConfig(level=logging.INFO, format='[BlockBuilder] %(message)s')

class BlockBuilder:

    @staticmethod
    def build(
        transactions: List[Transaction],
        previous_hash: str,
        bits: str,
        index: int
    ) -> Block:
        
        config = ConfigManager()
        max_nonce_limit = config.max_nonce

        logging.info(f"Iniciando minería de Bloque #{index} con {len(transactions)} transacciones...")
        logging.info(f"Dificultad objetivo (Bits): {bits}")

        timestamp = int(time.time())
        tx_hashes = [tx.tx_hash for tx in transactions]
        merkle_root = MerkleTreeBuilder.build(tx_hashes)
        target = DifficultyUtils.bits_to_target(bits)
        nonce = 0
        start_time = time.time()
        while nonce <= max_nonce_limit:
            candidate_block = Block(
                index=index,
                timestamp=timestamp,
                previous_hash=previous_hash,
                bits=bits,
                merkle_root=merkle_root,
                nonce=nonce,
                block_hash="",
                transactions=transactions
            )
            block_hash = BlockHasher.calculate(candidate_block)

            hash_int = int(block_hash, 16)

            if hash_int <= target:
                elapsed = time.time() - start_time
                logging.info(f"\t¡BLOQUE MINADO! Nonce: {nonce} | Hash: {block_hash[:16]}... ({elapsed:.2f}s)")
                
                return Block(
                    index=index,
                    timestamp=timestamp,
                    previous_hash=previous_hash,
                    bits=bits,
                    merkle_root=merkle_root,
                    nonce=nonce,
                    block_hash=block_hash,
                    transactions=transactions
                )

            nonce += 1

        raise TimeoutError("BlockBuilder: No se encontró solución dentro del rango de Nonce (Mining Failed).")