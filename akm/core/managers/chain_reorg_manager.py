# akm/core/managers/chain_reorg_manager.py

import logging
from typing import List

# Modelos
from akm.core.models.block import Block
from akm.core.models.transaction import Transaction
from akm.core.managers.utxo_set import UTXOSet
from akm.core.models.blockchain import Blockchain
from akm.core.services.mempool import Mempool

logger = logging.getLogger(__name__)

class ChainReorgManager:
    
    def __init__(self, blockchain: Blockchain, utxo_set: UTXOSet, mempool: Mempool):
        self._blockchain = blockchain
        self._utxo_set = utxo_set
        self._mempool = mempool
        logger.info("Gestor de reorgs activo.")

    def handle_reorg(self, new_chain_blocks: List[Block]) -> bool:
        if not new_chain_blocks:
            return False

        try:
            # 1. Detectar dónde se separaron las cadenas
            fork_index = self._find_fork_index_optimized(new_chain_blocks)
            
            if fork_index == -1:
                logger.info("Reorg abortado: Sin ancestro común.")
                return False

            logger.info(f"🔀 Divergencia en bloque #{fork_index}. Iniciando reorg...")

            # 2. Rescate de transacciones de la rama que va a desaparecer
            orphaned_txs = self._collect_orphaned_txs(fork_index)

            # 3. Aplicar la nueva cadena al repositorio
            if not self._blockchain.replace_chain(new_chain_blocks):
                logger.info("Reorg fallido: Error en persistencia.")
                return False

            # 4. Reconstrucción completa del estado (UTXO)
            self._rebuild_utxo_set_from_scratch()

            # 5. Devolver las TXs rescatadas al mempool
            restored_count = self._restore_mempool(orphaned_txs)
            
            logger.info(f"✅ Reorg finalizado. {restored_count} TXs rescatadas.")
            return True

        except Exception:
            logger.exception("Error crítico durante la reorganización")
            return False

    def apply_block_to_state(self, block: Block) -> None:
        
        txs_to_remove: List[Transaction] = []
        for tx in block.transactions:
            if not self._is_coinbase(tx):
                self._utxo_set.remove_inputs(tx.inputs)
            
            tx_id = getattr(tx, 'tx_hash', None)
            if tx_id:
                self._utxo_set.add_outputs(tx_id, tx.outputs)
            txs_to_remove.append(tx)
        
        self._mempool.remove_mined_transactions(txs_to_remove)

    # --- MÉTODOS PRIVADOS ---

    def _find_fork_index_optimized(self, new_chain: List[Block]) -> int:
        last_match_index = -1
        for block in new_chain:
            stored_block = self._blockchain.get_block_by_index(block.index)
            if stored_block is None:
                break
            
            stored_hash = getattr(stored_block, 'block_hash', stored_block.hash)
            new_hash = getattr(block, 'block_hash', block.hash)

            if stored_hash == new_hash:
                last_match_index = block.index
            else:
                break
        return last_match_index

    def _collect_orphaned_txs(self, fork_index: int) -> List[Transaction]:
        orphaned_txs: List[Transaction] = [] 
        try:
            start_orphan = fork_index + 1
            history_iterator = self._blockchain.get_history_iterator(start_index=start_orphan)
            
            for block in history_iterator:
                for tx in block.transactions:
                    if not self._is_coinbase(tx):
                        orphaned_txs.append(tx)
        except Exception:
            logger.warning("No se pudieron recolectar todas las TXs huérfanas.")
            
        return orphaned_txs

    def _restore_mempool(self, txs: List[Transaction]) -> int:
        count = 0
        for tx in txs:
            if self._mempool.add_transaction(tx):
                count += 1
        return count

    def _rebuild_utxo_set_from_scratch(self) -> None:
        try:
            logger.info("♻️  Reconstruyendo estado UTXO...")
            self._utxo_set.clear()
            
            processed_count = 0
            for block in self._blockchain.get_history_iterator():
                self.apply_block_to_state(block)
                processed_count += 1
                
            logger.info(f"Estado sincronizado ({processed_count} bloques).")
        except Exception:
            logger.exception("Fallo técnico reconstruyendo estado")
            raise

    def _is_coinbase(self, tx: Transaction) -> bool:
        if hasattr(tx, 'is_coinbase'):
            return tx.is_coinbase
        return len(tx.inputs) == 1 and tx.inputs[0].previous_tx_hash == "0"*64