# akm/core/services/mempool.py

import threading
import logging
from typing import Dict, List

# Dependencias
from akm.core.models.transaction import Transaction
from akm.core.config.consensus_config import ConsensusConfig

logger = logging.getLogger(__name__)

class Mempool:

    def __init__(self):
        self._pending_txs: Dict[str, Transaction] = {}
        self._config = ConsensusConfig()
        self._lock = threading.RLock()

    def add_transaction(self, tx: Transaction) -> bool:
        with self._lock:
            try:
                if tx.tx_hash in self._pending_txs:
                    return False

                if len(self._pending_txs) >= self._config.mempool_max_size:
                    logger.info("Mempool llena. TX rechazada.")
                    return False

                self._pending_txs[tx.tx_hash] = tx
                
                logger.info(f"TX {tx.tx_hash[:]}... en espera.")
                return True

            except Exception:
                logger.exception("Bug al procesar entrada en Mempool")
                return False

    def get_transactions_for_block(self, max_count: int = 2000) -> List[Transaction]:
        with self._lock:
            try:
                all_txs = list(self._pending_txs.values())
                all_txs.sort(key=lambda t: t.fee, reverse=True)
                return all_txs[:max_count]
            except Exception:
                logger.exception("Error al recuperar transacciones para el bloque")
                return []

    def remove_mined_transactions(self, mined_txs: List[Transaction]) -> None:
        with self._lock:
            try:
                count = 0
                for tx in mined_txs:
                    if tx.tx_hash in self._pending_txs:
                        del self._pending_txs[tx.tx_hash]
                        count += 1
                
                if count > 0:
                    logger.info(f"Mempool: -{count} TXs confirmadas.")
            except Exception:
                logger.exception("Bug durante la limpieza de Mempool")

    def get_pending_count(self) -> int:
        with self._lock:
            return len(self._pending_txs)