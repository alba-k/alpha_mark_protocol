# akm/core/builders/block_builder.py

import time
import logging
import threading 
from typing import List, Optional
from dataclasses import dataclass 

# Modelos y Config
from akm.core.models.block import Block
from akm.core.models.transaction import Transaction
from akm.core.config.consensus_config import ConsensusConfig

# Servicios
from akm.core.services.merkle_tree_builder import MerkleTreeBuilder
from akm.core.services.block_hasher import BlockHasher
from akm.core.utils.difficulty_utils import DifficultyUtils

logger = logging.getLogger(__name__)

class BlockBuilder:

    @dataclass
    class _MiningCandidate:
        index: int
        timestamp: int
        previous_hash: str
        bits: str
        merkle_root: str
        nonce: int = 0

    @staticmethod
    def build(
        transactions: List[Transaction],
        previous_hash: str,
        bits: str,
        index: int,
        interrupt_event: Optional[threading.Event] = None
    ) -> Optional[Block]:
        try:
            config = ConsensusConfig()
            max_nonce = config.max_nonce
            timestamp = int(time.time())
            
            tx_hashes = [tx.tx_hash for tx in transactions]
            merkle_root = MerkleTreeBuilder.build(tx_hashes)
            target = DifficultyUtils.bits_to_target(bits)
            
            logger.info(f"Minería iniciada: Bloque #{index} (Diff: {bits})")

            candidate = BlockBuilder._MiningCandidate(
                index=index,
                timestamp=timestamp,
                previous_hash=previous_hash,
                bits=bits,
                merkle_root=merkle_root
            )

            nonce = 0
            start_time = time.time()

            while nonce <= max_nonce:
                
                if interrupt_event and interrupt_event.is_set():
                    logger.info(f"Minería interrumpida en bloque #{index}.")
                    return None  

                candidate.nonce = nonce
                block_hash = BlockHasher.calculate(candidate)
                
                if int(block_hash, 16) <= target:
                    elapsed = time.time() - start_time
                    hash_power = nonce / elapsed if elapsed > 0 else 0

                    logger.info(
                        f"Bloque #{index} minado. "
                        f"Hash: {block_hash[:10]}... | "
                        f"Nonce: {nonce} | "
                        f"Vel: {hash_power:.0f} h/s"
                    )
                    
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
            
            logger.info(f"Minería fallida: Rango de nonce agotado en bloque #{index}.")
            return None

        except Exception:
            logger.exception(f"Bug detectado en el constructor del bloque #{index}")
            return None