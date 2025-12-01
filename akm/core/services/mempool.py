# akm/core/services/mempool.py
'''
class Mempool:
    Almacena las transacciones validadas que esperan ser incluidas en un bloque.

    Attributes::
        _pending_txs (Dict[str, Transaction]): Mapa interno de hash -> transacción.
        _config (ConfigManager): Referencia a la configuración del sistema.
        _lock (RLock): Mecanismo de sincronización para thread-safety.

    Methods::
        add_transaction(tx) -> bool:
            Agrega una nueva transacción si hay espacio y no es duplicada.
        get_transactions_for_block(max_count) -> List[Transaction]:
            Selecciona las mejores transacciones (mayor comisión) para armar un bloque.
        remove_mined_transactions(mined_txs) -> None:
            Limpia el mempool eliminando las transacciones que ya fueron confirmadas.
        get_pending_count() -> int:
            Retorna la cantidad actual de transacciones en espera.
'''

import threading
import logging
from typing import Dict, List

# Dependencias
from akm.core.models.transaction import Transaction
from akm.core.config.config_manager import ConfigManager

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='[Mempool] %(message)s')

class Mempool:

    def __init__(self):
        self._pending_txs: Dict[str, Transaction] = {}
        self._config = ConfigManager()
        self._lock = threading.RLock()

    def add_transaction(self, tx: Transaction) -> bool:
        with self._lock:
            if tx.tx_hash in self._pending_txs:
                logging.debug(f"TX rechazada (Duplicada): {tx.tx_hash[:8]}")
                return False

            if len(self._pending_txs) >= self._config.mempool_max_size:
                logging.warning("Mempool lleno. Rechazando transacción entrante.")
                return False

            self._pending_txs[tx.tx_hash] = tx
            logging.info(f"TX Agregada al Mempool: {tx.tx_hash[:8]} (Fee: {tx.fee})")
            return True

    def get_transactions_for_block(self, max_count: int = 2000) -> List[Transaction]:
        with self._lock:
            all_txs = list(self._pending_txs.values())
            all_txs.sort(key=lambda t: t.fee, reverse=True)
            selected_txs = all_txs[:max_count]
            
            return selected_txs

    def remove_mined_transactions(self, mined_txs: List[Transaction]) -> None:
        with self._lock:
            count = 0
            for tx in mined_txs:
                if tx.tx_hash in self._pending_txs:
                    del self._pending_txs[tx.tx_hash]
                    count += 1
            
            if count > 0:
                logging.info(f"Limpieza de Mempool: {count} transacciones confirmadas eliminadas.")

    def get_pending_count(self) -> int:
        with self._lock:
            return len(self._pending_txs)