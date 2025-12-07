# akm/core/factories/genesis_block_factory.py
'''
class GenesisBlockFactory:
    Fábrica especializada en la creación del Bloque Génesis.
    Ensambla el bloque y, si es necesario, realiza PoW para garantizar su validez.
'''

import logging
from akm.core.models.block import Block
from akm.core.models.transaction import Transaction
from akm.core.models.tx_output import TxOutput
from akm.core.models.tx_input import TxInput
from akm.core.services.block_hasher import BlockHasher
from akm.core.services.merkle_tree_builder import MerkleTreeBuilder
from akm.core.services.transaction_hasher import TransactionHasher
from akm.core.config.config_manager import ConfigManager
from akm.core.config.genesis_config import GenesisConfig
# ⚡ IMPORTACIÓN REQUERIDA: Fuente de la verdad monetaria
from akm.core.config.consensus_config import ConsensusConfig
from akm.core.utils.difficulty_utils import DifficultyUtils 

class GenesisBlockFactory:

    @staticmethod
    def create_genesis_block() -> Block:
        # 1. Cargar Configuraciones
        sys_conf = ConfigManager()
        gen_conf = GenesisConfig()
        # ⚡ CORRECCIÓN MONETARIA: Obtenemos el subsidio inicial directamente del consenso
        consensus_conf = ConsensusConfig()
        initial_subsidy_albas = consensus_conf.initial_subsidy # Valor entero (Albas)

        # 2. Construir la Transacción Coinbase
        coinbase_input = TxInput(
            previous_tx_hash=gen_conf.coinbase_input_prev_tx,
            output_index=gen_conf.coinbase_input_index,
            script_sig=gen_conf.coinbase_message
        )

        coinbase_output = TxOutput(
            # ⚡ CORRECCIÓN: Usamos el valor entero seguro de ConsensusConfig
            value_alba=initial_subsidy_albas,
            script_pubkey=gen_conf.miner_address
        )

        # Hash de la TX
        temp_tx = Transaction(
            tx_hash=gen_conf.empty_hash_placeholder,
            timestamp=gen_conf.timestamp,
            inputs=[coinbase_input],
            outputs=[coinbase_output],
            fee=gen_conf.tx_fee
        )
        
        tx_hash_calc = TransactionHasher.calculate(temp_tx)

        genesis_tx = Transaction(
            tx_hash=tx_hash_calc,
            timestamp=gen_conf.timestamp,
            inputs=[coinbase_input],
            outputs=[coinbase_output],
            fee=gen_conf.tx_fee
        )

        # 3. Construir el Bloque
        transactions = [genesis_tx]
        merkle_root = MerkleTreeBuilder.build([tx.tx_hash for tx in transactions])
        # Usamos sys_conf para la dificultad (asumiendo que ConfigManager lo expone)
        bits = sys_conf.initial_difficulty_bits 
        target = DifficultyUtils.bits_to_target(bits)
        
        # Intentamos primero con el nonce configurado
        nonce = gen_conf.nonce
        
        # --- MINERÍA AUTOMÁTICA DEL GÉNESIS ---
        logging.info("🔨 Validando PoW del Génesis...")
        
        while True:
            temp_block = Block(
                index=gen_conf.index,
                timestamp=gen_conf.timestamp,
                previous_hash=gen_conf.previous_hash,
                bits=bits,
                merkle_root=merkle_root,
                nonce=nonce,
                block_hash=gen_conf.empty_hash_placeholder,
                transactions=transactions
            )

            block_hash = BlockHasher.calculate(temp_block)
            hash_int = int(block_hash, 16)

            if hash_int <= target:
                # ¡Encontrado!
                return Block(
                    index=gen_conf.index,
                    timestamp=gen_conf.timestamp,
                    previous_hash=gen_conf.previous_hash,
                    bits=bits,
                    merkle_root=merkle_root,
                    nonce=nonce, # Usamos el nonce ganador
                    block_hash=block_hash,
                    transactions=transactions
                )
            
            # Si el nonce configurado falló, probamos el siguiente
            nonce += 1
            
            # Evitar bucle infinito en configs rotas
            if nonce > sys_conf.max_nonce:
                nonce = 0