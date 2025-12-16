# akm/core/managers/utxo_set.py

import logging
import threading
from typing import Dict, List, Optional, Any

# Modelos
from akm.core.models.tx_output import TxOutput
from akm.core.models.tx_input import TxInput
from akm.core.interfaces.i_utxo_repository import IUTXORepository

logger = logging.getLogger(__name__)

class UTXOSet:
    """
    Gestor de Estado Financiero (Unspent Transaction Outputs).
    Actúa como intermediario entre la lógica de negocio y el almacenamiento.
    
    [THREAD-SAFE]: Protegido contra condiciones de carrera entre Minero y Red.
    """

    def __init__(self, repository: IUTXORepository) -> None:
        self._repository = repository
        # RLock permite que el mismo hilo adquiera el candado varias veces
        # (necesario porque get_balance llama a get_utxos_for_address)
        self._lock = threading.RLock()
        logger.info("Gestor UTXO (State Manager) iniciado correctamente.")

    def add_outputs(self, tx_hash: str, outputs: List[TxOutput]) -> None:
        """Registra nuevos outputs generados por una transacción."""
        with self._lock:
            try:
                for index, output in enumerate(outputs):
                    self._repository.add_utxo(tx_hash, index, output)
            except Exception:
                logger.exception(f"Error crítico guardando outputs de TX {tx_hash}")
                raise

    def remove_inputs(self, inputs: List[TxInput]) -> None:
        """Elimina outputs gastados (los marca como consumidos)."""
        with self._lock:
            try:
                for inp in inputs:
                    self._repository.remove_utxo(inp.previous_tx_hash, inp.output_index)
            except Exception:
                logger.exception("Error crítico eliminando inputs del estado")
                raise

    # --- Consultas Seguras (API Safe) ---

    def get_utxo_by_reference(self, prev_tx_hash: str, output_index: int) -> Optional[TxOutput]:
        with self._lock:
            return self._repository.get_utxo(prev_tx_hash, output_index)

    def get_balance_for_address(self, address: str) -> int:
        """Calcula el saldo total sumando los UTXOs."""
        with self._lock:
            try:
                utxos = self.get_utxos_for_address(address)
                # Nota: get_utxos_for_address garantiza devolver diccionarios con "value_alba"
                return sum(int(u.get("value_alba", 0)) for u in utxos)
            except Exception:
                logger.exception(f"Error calculando balance para: {address}")
                return 0

    def get_utxos_for_address(self, address: str) -> List[Dict[str, Any]]:
        """
        Recupera los UTXOs y garantiza que se retornen como DICCIONARIOS SERIALIZABLES.
        CORRIGE: TypeError: Object of type TxOutput is not JSON serializable.
        """
        with self._lock:
            raw_data = self._repository.get_utxos_by_address(address)
            serialized_data: List[Dict[str, Any]] = []

            for item in raw_data:
                # Si el repositorio devuelve objetos TxOutput, los convertimos
                if isinstance(item, TxOutput):
                    serialized_data.append(item.to_dict())
                # Si el repositorio devuelve tuplas/dict que contienen el objeto
                elif isinstance(item, dict) and "output" in item and isinstance(item["output"], TxOutput): # pyright: ignore[reportUnnecessaryIsInstance]
                    data = item["output"].to_dict()
                    # Fusionamos con otros datos del dict (tx_hash, index, etc)
                    data.update({k:v for k,v in item.items() if k != "output"})
                    serialized_data.append(data)
                # Si ya es diccionario puro, lo pasamos
                elif isinstance(item, dict): # pyright: ignore[reportUnnecessaryIsInstance]
                    serialized_data.append(item)
                else:
                    logger.warning(f"Tipo de dato inesperado en UTXO set: {type(item)}")

            return serialized_data

    def get_total_circulating_supply(self) -> int:
        with self._lock:
            return self._repository.get_total_supply()

    def clear(self) -> None:
        """Reinicia el estado financiero completo (Usado en resync/genesis)."""
        with self._lock:
            try:
                logger.warning("⚠️  ESTADO FINANCIERO REINICIADO (CLEAR).")
                self._repository.clear()
            except Exception:
                logger.exception("Fallo crítico al intentar limpiar el estado")