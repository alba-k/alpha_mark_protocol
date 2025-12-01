# akm/core/models/tx_input.py
'''
class TxInput:
    Modelo inmutable que representa una Entrada de Transacción.

    Methods::
        to_dict() -> Dict[str, Any]: Serialización estándar.
'''

from typing import Dict, Any

class TxInput:

    def __init__(self, previous_tx_hash: str, output_index: int, script_sig: str):
        
        if not previous_tx_hash or len(previous_tx_hash) == 0:
            raise ValueError("TxInput: Debe referenciar un hash de transacción previo.")
        if output_index < 0:
            raise ValueError("TxInput: El índice del output no puede ser negativo.")

        
        self._previous_tx_hash: str = previous_tx_hash
        self._output_index: int = output_index
        self._script_sig: str = script_sig

    
    @property
    def previous_tx_hash(self) -> str:
        return self._previous_tx_hash

    @property
    def output_index(self) -> int:
        return self._output_index

    @property
    def script_sig(self) -> str:
        return self._script_sig

    def to_dict(self) -> Dict[str, Any]:
        return {
            "previous_tx_hash": self._previous_tx_hash,
            "output_index": self._output_index,
            "script_sig": self._script_sig
        }

    def __str__(self) -> str:
        return f"TxInput(prev={self._previous_tx_hash[:8]}..., idx={self._output_index})"