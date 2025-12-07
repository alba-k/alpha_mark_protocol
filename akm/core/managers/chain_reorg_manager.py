# akm/core/managers/chain_reorg_manager.py
'''
class ChainReorgManager:
    Especialista en la manipulación de estado durante bifurcaciones (Forks).
    Implementa la Estrategia de Reconstrucción (State Rebuild) para máxima integridad y rendimiento.

    Methods::
        handle_reorg(new_chain) -> bool:
            Orquesta el cambio de cadena mediante reconstrucción total del UTXO Set.
        apply_block_to_state(block):
            Aplica los cambios de un bloque (consume inputs, crea outputs).
        rollback_block_from_state(block):
            Retrocede cambios (necesario para rollback manual o tests, aunque handle_reorg usa rebuild).
'''

import logging
from typing import List, Optional

from akm.core.models.block import Block
from akm.core.models.blockchain import Blockchain
from akm.core.models.transaction import Transaction
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput
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
        Gestiona el cambio de cadena.
        OPTIMIZACIÓN: En lugar de hacer rollback (undo) lento, reinicia el estado y
        reaplica la nueva cadena ganadora completa (Rebuild Strategy).
        """
        # 1. Validación básica de continuidad
        if not new_chain_blocks:
            return False

        # 2. Identificar Transacciones Huérfanas (Para no perderlas)
        current_chain = self._blockchain.chain
        fork_index = self._find_fork_point(current_chain, new_chain_blocks)
        
        if fork_index == -1:
            logging.error("Reorg fallido: Cadenas incompatibles (Génesis diferente).")
            return False

        logging.warning(f"\nINICIANDO REORG (REBUILD STRATEGY) | Fork Index: {fork_index}")
        logging.info(f"   Altura actual: {len(current_chain)} -> Nueva altura: {len(new_chain_blocks)}")

        # Recolectamos TXs de los bloques que vamos a abandonar para devolverlas al mempool
        orphaned_blocks = current_chain[fork_index + 1:]
        orphaned_txs: List[Transaction] = []
        for block in orphaned_blocks:
            for tx in block.transactions:
                if not tx.is_coinbase: # Las coinbase huérfanas se pierden
                    orphaned_txs.append(tx)

        # 3. Actualizar la Cadena Principal (Blockchain Pointer)
        self._blockchain.replace_chain(new_chain_blocks)

        # 4. RECONSTRUCCIÓN DEL ESTADO (UTXO SET)
        try:
            self._rebuild_utxo_set_from_scratch(new_chain_blocks)
        except Exception as e:
            logging.critical(f"\nERROR FATAL DURANTE RECONSTRUCCIÓN DE ESTADO: {e}")
            return False

        # 5. Restaurar Mempool (Devolver TXs huérfanas a la cola)
        restored_count = 0
        for tx in orphaned_txs:
            if self._mempool.add_transaction(tx):
                restored_count += 1
        
        logging.info(f"\nReorg completado. Estado reconstruido. {restored_count} TXs restauradas al Mempool.")
        return True

    def apply_block_to_state(self, block: Block) -> None:
        """
        Avanza el estado aplicando un bloque.
        Consume inputs, crea outputs y limpia el Mempool.
        """
        txs_to_remove_from_mempool: List[Transaction] = []
        
        for tx in block.transactions:
            # 1. Consumir Inputs (Gastar)
            if not tx.is_coinbase:
                self._utxo_set.remove_inputs(tx.inputs)
            
            # 2. Registrar Outputs (Crear)
            self._utxo_set.add_outputs(tx.tx_hash, tx.outputs)
            
            txs_to_remove_from_mempool.append(tx)

        # 3. Limpiar Mempool
        self._mempool.remove_mined_transactions(txs_to_remove_from_mempool)

    def rollback_block_from_state(self, block: Block) -> None:
        """
        Retrocede el estado (Undo).
        Nota: handle_reorg prefiere la reconstrucción, pero este método es útil para tests o rollbacks puntuales.
        """
        for tx in block.transactions:
            # 1. Borrar outputs creados
            dummy_inputs_to_remove = [TxInput(tx.tx_hash, i, "") for i in range(len(tx.outputs))]
            self._utxo_set.remove_inputs(dummy_inputs_to_remove)

            # 2. Restaurar inputs gastados
            if not tx.is_coinbase:
                for inp in tx.inputs:
                    original_out = self._find_referenced_output(inp.previous_tx_hash, inp.output_index)
                    if original_out:
                        self._utxo_set.add_outputs(inp.previous_tx_hash, [original_out])
                    else:
                        raise ValueError(f"Imposible restaurar UTXO {inp.previous_tx_hash[:8]}: Data no encontrada.")

            # 3. Devolver TX al Mempool
            if not tx.is_coinbase:
                self._mempool.add_transaction(tx)

    def _rebuild_utxo_set_from_scratch(self, chain: List[Block]) -> None:
        """Reinicia el UTXO Set a cero y reaplica toda la historia."""
        logging.info("\nLimpiando UTXO Set y reconstruyendo desde Génesis...")
        
        # Usamos el método público clear() que debes añadir a UTXOSet
        if hasattr(self._utxo_set, 'clear'):
            self._utxo_set.clear()
        else:
            # Fallback si no has actualizado UTXOSet aún, accediendo al protegido (temporal)
            self._utxo_set._utxos.clear() # type: ignore
        
        for block in chain:
            self.apply_block_to_state(block)
            
        logging.info(f"   Estado reconstruido exitosamente ({len(chain)} bloques procesados).")

    def _find_fork_point(self, current_chain: List[Block], new_chain: List[Block]) -> int:
        """Encuentra el índice del último bloque idéntico en ambas cadenas."""
        min_len = min(len(current_chain), len(new_chain))
        for i in range(min_len):
            if current_chain[i].hash != new_chain[i].hash:
                return i - 1
        return min_len - 1

    def _find_referenced_output(self, tx_hash: str, output_index: int) -> Optional[TxOutput]:
        """Busca una transacción histórica para recuperar un Output gastado."""
        for block in reversed(self._blockchain.chain):
            for tx in block.transactions:
                if tx.tx_hash == tx_hash:
                    if output_index < len(tx.outputs):
                        return tx.outputs[output_index]
        return None