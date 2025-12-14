# akm/core/builders/genesis_block_factory.py

import logging
from dataclasses import dataclass

# Modelos
from akm.core.models.block import Block
from akm.core.models.transaction import Transaction
from akm.core.models.tx_output import TxOutput
from akm.core.models.tx_input import TxInput

# Servicios y Utilidades
from akm.core.services.block_hasher import BlockHasher
from akm.core.services.merkle_tree_builder import MerkleTreeBuilder
from akm.core.services.transaction_hasher import TransactionHasher
from akm.core.utils.difficulty_utils import DifficultyUtils

# Configuraciones
from akm.core.config.genesis_config import GenesisConfig
from akm.core.config.consensus_config import ConsensusConfig

logger = logging.getLogger(__name__)

class GenesisBlockFactory:
    @dataclass
    class _GenesisCandidate:
        index: int
        timestamp: int
        previous_hash: str
        bits: str
        merkle_root: str
        nonce: int = 0

    @staticmethod
    def create_genesis_block() -> Block:
        
        try:
            consensus_conf = ConsensusConfig()
            gen_conf = GenesisConfig()

            logger.info("🌌 Iniciando creación del Bloque Génesis...")

            coinbase_script = gen_conf.coinbase_message.encode('utf-8')
            
            tx_input = TxInput(
                previous_tx_hash=gen_conf.coinbase_input_prev_tx,
                output_index=gen_conf.coinbase_input_index,
                script_sig=coinbase_script
            )

            tx_output = TxOutput(
                value_alba=consensus_conf.initial_subsidy,
                script_pubkey=gen_conf.miner_address.encode('utf-8')
            )

            genesis_tx = Transaction(
                tx_hash="", 
                timestamp=gen_conf.timestamp,
                inputs=[tx_input],
                outputs=[tx_output],
                fee=0
            )
            
            genesis_tx.tx_hash = TransactionHasher.calculate(genesis_tx)
            logger.info(f"TX Génesis sellada: {genesis_tx.tx_hash[:8]}...")

            merkle_root = MerkleTreeBuilder.build([genesis_tx.tx_hash])
            bits = consensus_conf.initial_difficulty_bits
            target = DifficultyUtils.bits_to_target(bits)
            
            candidate = GenesisBlockFactory._GenesisCandidate(
                index=gen_conf.index,
                timestamp=gen_conf.timestamp,
                previous_hash=gen_conf.previous_hash,
                bits=bits,
                merkle_root=merkle_root,
                nonce=gen_conf.nonce 
            )

            logger.info(f"🔨 Minando Génesis (Dificultad: {bits})...")
            
            while True:
                block_hash = BlockHasher.calculate(candidate)
                hash_int = int(block_hash, 16)

                if hash_int <= target:
                    logger.info(f"✅ ¡Génesis Minado! Hash: {block_hash[:10]}... | Nonce: {candidate.nonce}")
                    
                    return Block(
                        index=gen_conf.index,
                        timestamp=gen_conf.timestamp,
                        previous_hash=gen_conf.previous_hash,
                        bits=bits,
                        merkle_root=merkle_root,
                        nonce=candidate.nonce,
                        block_hash=block_hash,
                        transactions=[genesis_tx]
                    )

                candidate.nonce += 1
                
                if candidate.nonce > consensus_conf.max_nonce:
                    logger.warning("Rango de nonce agotado en Génesis. Reiniciando...")
                    candidate.nonce = 0

        except Exception:
            logger.exception("Error fatal creando el Bloque Génesis")
            raise