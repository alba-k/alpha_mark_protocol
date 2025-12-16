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
from akm.core.config.consensus_config import ConsensusConfig

logger = logging.getLogger(__name__)

class GenesisBlockFactory:
    """
    Fábrica determinista del Bloque Génesis.
    Garantiza que todos los nodos inicien con EXACTAMENTE el mismo historial.
    """

    @dataclass
    class _GenesisCandidate:
        index: int
        timestamp: int
        previous_hash: str
        bits: str
        merkle_root: str
        nonce: int = 0

    # --- NUEVO MÉTODO AGREGADO ---
    @staticmethod
    def _build_p2pkh_script(address: str) -> bytes:
        """Crea el candado de seguridad estándar (P2PKH) que la Wallet puede leer."""
        OP_DUP = b'\x76'
        OP_HASH160 = b'\xa9'
        OP_EQUALVERIFY = b'\x88'
        OP_CHECKSIG = b'\xac'
        
        addr_bytes = address.encode('utf-8')
        push_op = bytes([len(addr_bytes)])
        
        return (
            OP_DUP + 
            OP_HASH160 + 
            push_op + addr_bytes + 
            OP_EQUALVERIFY + 
            OP_CHECKSIG
        )
    # -----------------------------

    @staticmethod
    def create_genesis_block() -> Block:
        try:
            logger.info("🌌 Generando Bloque Génesis (Modo Determinista)...")

            # -------------------------------------------------------------------------
            # 🔒 CONSTANTES DE CONSENSO
            # -------------------------------------------------------------------------
            GENESIS_TIMESTAMP = 1704067200
            GENESIS_MSG = "AKM_NETWORK_LAUNCH"
            GENESIS_NONCE_START = 0
            
            # [CAMBIO 1] ¡Aquí ponemos tu dirección para que el saldo inicial sea tuyo!
            GENESIS_MINER_ADDR = "1GQkiSucNWSVA8creoW8RaRF4jzC2vTQUp" 
            
            GENESIS_BITS = "1f00ffff" 
            # -------------------------------------------------------------------------

            consensus_conf = ConsensusConfig()

            # 1. Construir la Transacción Coinbase Estática
            coinbase_script = GENESIS_MSG.encode('utf-8')
            
            tx_input = TxInput(
                previous_tx_hash="0" * 64,
                output_index=0xFFFFFFFF,
                script_sig=coinbase_script
            )

            # [CAMBIO 2] Usamos la función de seguridad, NO .encode() directo
            script_pubkey_genesis = GenesisBlockFactory._build_p2pkh_script(GENESIS_MINER_ADDR)

            tx_output = TxOutput(
                value_alba=consensus_conf.initial_subsidy,
                script_pubkey=script_pubkey_genesis # <--- ¡CORREGIDO AQUÍ!
            )

            genesis_tx = Transaction(
                tx_hash="", 
                timestamp=GENESIS_TIMESTAMP,
                inputs=[tx_input],
                outputs=[tx_output],
                fee=0
            )
            
            # Calcular hash de la TX
            genesis_tx.tx_hash = TransactionHasher.calculate(genesis_tx)
            
            # 2. Construir la Cabecera
            merkle_root = MerkleTreeBuilder.build([genesis_tx.tx_hash])
            target = DifficultyUtils.bits_to_target(GENESIS_BITS)
            
            candidate = GenesisBlockFactory._GenesisCandidate(
                index=0,
                timestamp=GENESIS_TIMESTAMP,
                previous_hash="0" * 64,
                bits=GENESIS_BITS,
                merkle_root=merkle_root,
                nonce=GENESIS_NONCE_START
            )

            # 3. Minería Determinista
            logger.info(f"🔨 Buscando Nonce válido para hash objetivo < {target}...")
            
            while True:
                block_hash = BlockHasher.calculate(candidate) # type: ignore
                hash_int = int(block_hash, 16)

                if hash_int <= target:
                    logger.info(f"✅ ¡Génesis Oficial Encontrado!")
                    logger.info(f"   Hash:  {block_hash}")
                    
                    return Block(
                        index=0,
                        timestamp=candidate.timestamp,
                        previous_hash=candidate.previous_hash,
                        bits=candidate.bits,
                        merkle_root=candidate.merkle_root,
                        nonce=candidate.nonce,
                        block_hash=block_hash,
                        transactions=[genesis_tx]
                    )

                candidate.nonce += 1
                
                if candidate.nonce > 4_000_000_000:
                    logger.critical("❌ No se encontró nonce para el Génesis.")
                    raise ValueError("Fallo crítico en minado de Génesis")

        except Exception as e:
            logger.exception(f"Error fatal creando el Bloque Génesis: {e}")
            raise