# akm/core/managers/utxo_set.py
import logging
from typing import Dict, List, Optional, Any

from akm.core.models.tx_output import TxOutput
from akm.core.models.tx_input import TxInput
from akm.core.interfaces.i_utxo_repository import IUTXORepository

logging.basicConfig(level=logging.INFO, format='[UTXOSet] %(message)s')

class UTXOSet:

    def __init__(self, repository: IUTXORepository):
        # Inyección de dependencia: Ya no usamos un dict interno, vamos al disco.
        self._repository = repository

    def add_outputs(self, tx_hash: str, outputs: List[TxOutput]) -> None:
        if not tx_hash:
            raise ValueError("UTXOSet: Se requiere un hash de transacción válido.")

        for index, output in enumerate(outputs):
            self._repository.add_utxo(tx_hash, index, output)
            logging.debug(f"UTXO Guardado: {tx_hash[:8]}:{index} -> {output.value_alba}")

    def remove_inputs(self, inputs: List[TxInput]) -> None:
        for inp in inputs:
            # Validamos si existe antes (opcional, pero recomendado)
            # Para mayor rendimiento, podríamos mandar delete directo.
            self._repository.remove_utxo(inp.previous_tx_hash, inp.output_index)
            logging.debug(f"UTXO Gastado (Removido): {inp.previous_tx_hash[:8]}:{inp.output_index}")

    def get_utxo_by_reference(self, prev_tx_hash: str, output_index: int) -> Optional[TxOutput]:
        return self._repository.get_utxo(prev_tx_hash, output_index)

    def get_balance_for_address(self, address: str) -> int:
        """Suma eficiente usando SQL."""
        utxos = self._repository.get_utxos_by_address(address)
        return sum(u["amount"] for u in utxos)

    def get_utxos_for_address(self, address: str) -> List[Dict[str, Any]]:
        return self._repository.get_utxos_by_address(address)

    def get_total_circulating_supply(self) -> int:
        return self._repository.get_total_supply()

    def clear(self) -> None:
        self._repository.clear()