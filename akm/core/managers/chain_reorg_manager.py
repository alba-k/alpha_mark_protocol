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

        # 2. Identificar TXs Huérfanas para rescatarlas
        # Recuperamos los bloques de la cadena vieja que van a ser descartados
        start_orphan = fork_index + 1
        blocks_to_orphan_iterator: Iterator[Block] = self._blockchain.get_history_iterator(start_index=start_orphan)

        orphaned_txs: List[Transaction] = []
        
        for block in blocks_to_orphan_iterator:
            for tx in block.transactions:
                # No rescatamos transacciones Coinbase (ya no son válidas en la nueva rama)
                if not tx.is_coinbase:
                    orphaned_txs.append(tx)

        # 3. Actualizar DB Atómicamente
        # Esto sobrescribe los bloques viejos con los nuevos en la persistencia (SQLite/LevelDB)
        self._blockchain.replace_chain(new_chain_blocks)

        # 4. RECONSTRUCCIÓN DEL ESTADO (UTXO SET)
        # CRÍTICO: Debe reconstruirse TODA la historia, no solo la nueva rama.
        try:
            self._rebuild_utxo_set_from_scratch()
        except Exception as e:
            logging.critical(f"\nERROR FATAL DURANTE RECONSTRUCCIÓN DE ESTADO: {e}")
            return False

        # 5. Restaurar Mempool
        # Reinyectamos las TXs de la rama vieja al Mempool por si aún son válidas en la nueva
        restored_count = 0
        for tx in orphaned_txs:
            if self._mempool.add_transaction(tx):
                restored_count += 1
        
        logging.info(f"\nReorg completado. {restored_count} TXs restauradas al Mempool.")
        return True

    def _find_fork_index_optimized(self, new_chain: List[Block]) -> int:
        """
        Compara la nueva cadena contra la DB bloque por bloque para hallar donde divergen.
        """
        last_match_index = -1
        
        for block in new_chain:
            stored_block = self._blockchain.get_block_by_index(block.index)
            # Mientras los hashes coincidan, seguimos en la historia común
            if stored_block and stored_block.hash == block.hash:
                last_match_index = block.index
            else:
                # En cuanto difieren, ese es el punto de fork (last_match es el último ancestro común)
                break
                
        return last_match_index

    def apply_block_to_state(self, block: Block) -> None:
        """Aplica un bloque al conjunto UTXO y limpia el Mempool."""
        txs_to_remove: List[Transaction] = []
        for tx in block.transactions:
            if not tx.is_coinbase:
                self._utxo_set.remove_inputs(tx.inputs)
            self._utxo_set.add_outputs(tx.tx_hash, tx.outputs)
            txs_to_remove.append(tx)
        self._mempool.remove_mined_transactions(txs_to_remove)

    def _rebuild_utxo_set_from_scratch(self) -> None:
        """
        Reconstruye UTXOs reiniciando el set y reaplicando TODA la cadena desde Génesis.
        """
        logging.info("♻️  Reconstruyendo UTXO Set completo desde GÉNESIS...")
        
        # 1. Limpiar estado actual (Reset total)
        if hasattr(self._utxo_set, 'clear'):
            self._utxo_set.clear()
        else:
            self._utxo_set._utxos.clear() # type: ignore
        
        # 2. Reaplicar TODA la historia
        # Usamos el iterador de la blockchain que ya tiene la cadena canónica actualizada (gracias al paso 3)
        # Esto asegura que recuperamos el estado correcto desde el bloque 0 hasta el nuevo Tip.
        processed_count = 0
        for block in self._blockchain.get_history_iterator():
            self.apply_block_to_state(block)
            processed_count += 1
            
        logging.info(f"✅ Estado reconstruido exitosamente ({processed_count} bloques procesados).")