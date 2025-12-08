# akm/core/managers/chain_reorg_manager.py
import logging
from typing import List, Iterator

from akm.core.models.block import Block
from akm.core.models.blockchain import Blockchain
from akm.core.models.transaction import Transaction
from akm.core.managers.utxo_set import UTXOSet
from akm.core.services.mempool import Mempool

logging.basicConfig(level=logging.INFO, format='[ReorgManager] %(message)s')

class ChainReorgManager:

    def __init__(self, blockchain: Blockchain, utxo_set: UTXOSet, mempool: Mempool):
        self._blockchain = blockchain
        self._utxo_set = utxo_set
        self._mempool = mempool

    def handle_reorg(self, new_chain_blocks: List[Block]) -> bool:
        """
        Gestiona el cambio de cadena usando estrategia de Rebuild Optimizado.
        """
        if not new_chain_blocks:
            return False

        # 1. Encontrar el punto de divergencia
        fork_index = self._find_fork_index_optimized(new_chain_blocks)
        
        if fork_index == -1:
            logging.error("Reorg fallido: No se encontró ancestro común.")
            return False

        logging.warning(f"\nINICIANDO REORG | Fork Index: {fork_index}")
        logging.info(f"   Nueva rama tiene {len(new_chain_blocks)} bloques.")

        # 2. Identificar TXs Huérfanas
        # CORRECCIÓN: Usamos el iterador público 'get_history_iterator' en lugar de acceder a _repository.
        # Esto nos da los bloques desde el fork hasta el final (tip actual) de forma segura.
        start_orphan = fork_index + 1
        blocks_to_orphan_iterator: Iterator[Block] = self._blockchain.get_history_iterator(start_index=start_orphan)

        orphaned_txs: List[Transaction] = []
        
        # Iteramos el generador directamente (eficiente en memoria)
        for block in blocks_to_orphan_iterator:
            for tx in block.transactions:
                if not tx.is_coinbase:
                    orphaned_txs.append(tx)

        # 3. Actualizar DB Atómicamente
        # 'replace_chain' delega internamente a save_blocks_atomic del repositorio
        self._blockchain.replace_chain(new_chain_blocks)

        # 4. RECONSTRUCCIÓN DEL ESTADO (UTXO SET)
        try:
            self._rebuild_utxo_set_from_scratch(new_chain_blocks)
        except Exception as e:
            logging.critical(f"\nERROR FATAL DURANTE RECONSTRUCCIÓN DE ESTADO: {e}")
            return False

        # 5. Restaurar Mempool
        restored_count = 0
        for tx in orphaned_txs:
            if self._mempool.add_transaction(tx):
                restored_count += 1
        
        logging.info(f"\nReorg completado. {restored_count} TXs restauradas.")
        return True

    def _find_fork_index_optimized(self, new_chain: List[Block]) -> int:
        """
        Compara la nueva cadena contra la DB bloque por bloque para hallar donde divergen.
        """
        last_match_index = -1
        
        for block in new_chain:
            # Usamos el método público get_block_by_index
            stored_block = self._blockchain.get_block_by_index(block.index)
            if stored_block and stored_block.hash == block.hash:
                last_match_index = block.index
            else:
                break
                
        return last_match_index

    def apply_block_to_state(self, block: Block) -> None:
        txs_to_remove: List[Transaction] = []
        for tx in block.transactions:
            if not tx.is_coinbase:
                self._utxo_set.remove_inputs(tx.inputs)
            self._utxo_set.add_outputs(tx.tx_hash, tx.outputs)
            txs_to_remove.append(tx)
        self._mempool.remove_mined_transactions(txs_to_remove)

    def _rebuild_utxo_set_from_scratch(self, chain: List[Block]) -> None:
        """
        Reconstruye UTXOs reiniciando el set y reaplicando la nueva cadena.
        """
        logging.info("Reconstruyendo UTXO Set...")
        if hasattr(self._utxo_set, 'clear'):
            self._utxo_set.clear()
        else:
            # Fallback temporal si UTXOSet no tiene clear público, aunque debería tenerlo
            self._utxo_set._utxos.clear() # type: ignore
        
        for block in chain:
            self.apply_block_to_state(block)