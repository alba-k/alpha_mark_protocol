# akm/core/managers/mining_manager.py
import logging
import threading
from typing import List, Optional

from akm.core.models.block import Block
from akm.core.models.blockchain import Blockchain
from akm.core.models.transaction import Transaction
from akm.core.services.mempool import Mempool
from akm.core.config.config_manager import ConfigManager
from akm.core.consensus.difficulty_adjuster import DifficultyAdjuster
from akm.core.builders.block_builder import BlockBuilder
from akm.core.factories.transaction_factory import TransactionFactory

logging.basicConfig(level=logging.INFO, format='[Miner] %(message)s')

class MiningManager:

    def __init__(
        self,
        blockchain: Blockchain,
        mempool: Mempool,
        difficulty_adjuster: DifficultyAdjuster
    ):
        self._blockchain = blockchain
        self._mempool = mempool
        self._difficulty_adjuster = difficulty_adjuster
        self._config = ConfigManager()

    # ⚡ CAMBIO: Se añade argumento opcional interrupt_event
    # ⚡ CAMBIO: Return type es Optional[Block] porque puede devolver None si se cancela
    def mine_block(self, miner_address: str, interrupt_event: Optional[threading.Event] = None) -> Optional[Block]:
        """
        Orquesta la creación de un nuevo bloque.
        """
        logging.info(f"🔨 Iniciando minería para wallet: {miner_address[:10]}...")

        last_block = self._blockchain.last_block
        
        if not last_block:
            raise ValueError("MiningManager: No se puede minar sobre una cadena vacía. Falta el Génesis.")

        height = last_block.index + 1
        previous_hash = last_block.hash
            
        # 2. Calcular Dificultad Dinámica
        interval = self._config.difficulty_adjustment_interval
        
        if height % interval == 0:
            prev_idx = max(0, height - interval)
            prev_adjustment_block = self._blockchain.get_block_by_index(prev_idx)
            
            if not prev_adjustment_block:
                prev_adjustment_block = last_block

            bits = self._difficulty_adjuster.calculate_new_bits(prev_adjustment_block, last_block)
            logging.info(f"⚖️ Ajuste de Dificultad: Nuevo target bits {bits}")
        else:
            bits = last_block.bits

        # 3. Seleccionar Transacciones
        pending_txs = self._mempool.get_transactions_for_block(
            max_count=self._config.mempool_max_size 
        )

        # 4. Crear Coinbase
        coinbase_tx = self._create_coinbase_tx(miner_address, height, pending_txs)

        block_transactions = [coinbase_tx] + pending_txs

        # 5. Delegar a BlockBuilder
        logging.info(f"Delegando a BlockBuilder. Height: {height}, TXs: {len(block_transactions)}, Bits: {bits}")
        
        # ⚡ CAMBIO: Pasamos el evento de interrupción al Builder
        new_block = BlockBuilder.build(
            transactions=block_transactions,
            previous_hash=previous_hash,
            bits=bits,
            index=height,
            interrupt_event=interrupt_event
        )

        if new_block:
            logging.info(f"\nBloque minado exitosamente: {new_block.hash[:16]}... (Nonce: {new_block.nonce})")
        
        return new_block

    def _create_coinbase_tx(self, miner_address: str, height: int, txs: List[Transaction]) -> Transaction:
        # A. Calcular Subsidio Base
        base_subsidy = self._difficulty_adjuster.calculate_block_subsidy(height)

        # B. Sumar Comisiones
        total_fees = sum(tx.fee for tx in txs)

        total_reward = base_subsidy + total_fees

        logging.info(f"💰 Construyendo Coinbase: Subsidio={base_subsidy} + Fees={total_fees} = Total={total_reward}")

        return TransactionFactory.create_coinbase(
            miner_pubkey_hash=miner_address,
            block_height=height,
            total_reward=total_reward
        )