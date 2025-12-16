# akm/core/managers/mining_manager.py

import logging
import threading
from typing import List, Optional

# Modelos y Configuración
from akm.core.models.block import Block
from akm.core.models.blockchain import Blockchain
from akm.core.models.transaction import Transaction
from akm.core.config.consensus_config import ConsensusConfig
from akm.core.config.protocol_constants import ProtocolConstants # <--- IMPORTANTE

# Servicios del Dominio
from akm.core.services.mempool import Mempool
from akm.core.builders.block_builder import BlockBuilder
from akm.core.factories.transaction_factory import TransactionFactory

# Componentes de Lógica de Negocio
from akm.core.consensus.difficulty_adjuster import DifficultyAdjuster
from akm.core.consensus.subsidy_calculator import SubsidyCalculator

logger = logging.getLogger(__name__)

class MiningManager:
    
    def __init__(
        self,
        blockchain: Blockchain,
        mempool: Mempool,
        difficulty_adjuster: DifficultyAdjuster,
        subsidy_calculator: SubsidyCalculator
    ) -> None:
        try:
            self._blockchain = blockchain
            self._mempool = mempool
            self._difficulty_adjuster = difficulty_adjuster
            self._subsidy_calculator = subsidy_calculator
            self._consensus_config = ConsensusConfig()

            logger.info("Gestor de minería listo.")
        except Exception:
            logger.exception("Error crítico al inicializar MiningManager")

    def mine_block(self, miner_address: str, interrupt_event: Optional[threading.Event] = None) -> Optional[Block]:
        
        try:
            # 1. Obtener estado de la cadena
            last_block = self._blockchain.last_block
            if not last_block:
                raise ValueError("Cadena vacía. Se requiere bloque Génesis.")

            new_height: int = last_block.index + 1

            logger.info(f"Preparando bloque #{new_height}...")

            # 2. Ajuste de Consenso (Dificultad)
            bits = self._calculate_required_bits(last_block, new_height)

            # 3. Selección de transacciones
            # [FIX CRÍTICO]: Usamos un límite por BLOQUE, no el tamaño total del mempool.
            # Si el mempool tiene 50.000 txs, solo tomamos 2.000 para que el bloque no pese 100MB.
            max_txs_per_block = getattr(ProtocolConstants, 'MAX_TX_PER_BLOCK', 2000)
            
            pending_txs = self._mempool.get_transactions_for_block(
                max_count=max_txs_per_block
            )

            # 4. Creación de recompensa (Coinbase)
            coinbase_tx = self._create_coinbase_tx(miner_address, new_height, pending_txs)
            block_transactions = [coinbase_tx] + pending_txs

            # 5. Ejecución del minado
            new_block = BlockBuilder.build(
                transactions=block_transactions,
                previous_hash=last_block.hash, 
                bits=bits,
                index=new_height,
                interrupt_event=interrupt_event
            )

            if new_block:
                logger.info(f"Bloque #{new_height} sellado y listo.")
            
            return new_block

        except Exception:
            logger.exception("Fallo en la orquestación")
            return None

    # --- MÉTODOS PRIVADOS ---

    def _calculate_required_bits(self, last_block: Block, current_height: int) -> str:
        interval = self._consensus_config.difficulty_adjustment_interval

        if current_height % interval == 0:
            start_epoch_index = max(0, current_height - interval)
            first_block_of_epoch = self._blockchain.get_block_by_index(start_epoch_index)
            
            if not first_block_of_epoch:
                logger.info("Ajuste: Bloque de época no hallado. Usando último.")
                first_block_of_epoch = last_block

            return self._difficulty_adjuster.calculate_new_bits(first_block_of_epoch, last_block)
        
        return last_block.bits

    def _create_coinbase_tx(self, miner_address: str, height: int, txs: List[Transaction]) -> Transaction:
        
        base_subsidy = self._subsidy_calculator.get_subsidy(height)
        total_fees = sum(tx.fee for tx in txs)
        total_reward = base_subsidy + total_fees
        
        return TransactionFactory.create_coinbase(
            miner_address=miner_address,
            block_height=height,
            total_reward=total_reward
        )