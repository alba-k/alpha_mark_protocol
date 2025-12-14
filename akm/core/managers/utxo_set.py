# akm/core/managers/utxo_set.py

import logging
from typing import Dict, List, Optional, Any, Tuple

# Modelos
from akm.core.models.tx_output import TxOutput
from akm.core.models.tx_input import TxInput
from akm.core.interfaces.i_utxo_repository import IUTXORepository

logger = logging.getLogger(__name__)

class UTXOSet:

    def __init__(self, repository: IUTXORepository) -> None:
        try:
            self._repository = repository
            logger.info("Gestor UTXO (Estado) iniciado.")
        except Exception:
            logger.exception("Error al inicializar UTXOSet")

    def add_outputs(self, tx_hash: str, outputs: List[TxOutput]) -> None:
        try:
            for index, output in enumerate(outputs):
                self._repository.add_utxo(tx_hash, index, output)
        except Exception:
            logger.exception(f"Bug guardando outputs de TX {tx_hash[:8]}")

    def remove_inputs(self, inputs: List[TxInput]) -> None:
        try:
            for inp in inputs:
                self._repository.remove_utxo(inp.previous_tx_hash, inp.output_index)
        except Exception:
            logger.exception("Bug eliminando inputs del estado")

    def apply_batch(self, new_utxos: List[Tuple[str, int, TxOutput]], spent_utxos: List[Tuple[str, int]]) -> None:
        
        try:
            self._repository.update_batch(new_utxos, spent_utxos)
            logger.info(f"Estado actualizado: +{len(new_utxos)} / -{len(spent_utxos)} UTXOs.")
        except Exception:
            logger.exception("Fallo técnico en actualización atómica de saldos")

    # --- Consultas (Silenciosas por rendimiento) ---

    def get_utxo_by_reference(self, prev_tx_hash: str, output_index: int) -> Optional[TxOutput]:
        return self._repository.get_utxo(prev_tx_hash, output_index)

    def get_balance_for_address(self, address: str) -> int:
        try:
            utxos = self._repository.get_utxos_by_address(address)
            return sum(u["amount"] for u in utxos)
        except Exception:
            logger.exception(f"Error consultando balance para: {address}")
            return 0

    def get_utxos_for_address(self, address: str) -> List[Dict[str, Any]]:
        return self._repository.get_utxos_by_address(address)

    def get_total_circulating_supply(self) -> int:
        return self._repository.get_total_supply()

    def clear(self) -> None:
        
        try:
            logger.warning("⚠️  ESTADO FINANCIERO REINICIADO (CLEAR).")
            self._repository.clear()
        except Exception:
            logger.exception("Fallo crítico al intentar limpiar el estado")