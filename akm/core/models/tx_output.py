# akm/core/models/tx_output.py
'''
class TxOutput:
    Modelo inmutable que representa una Salida de Transacción no gastada (UTXO).

    Methods::
        to_dict() -> Dict[str, Any]: Serialización.
'''

from typing import Dict, Any

class TxOutput:

    def __init__(self, value_alba: int, script_pubkey: str):
        if value_alba < 0:
            raise ValueError("TxOutput: El valor no puede ser negativo.")
        if not script_pubkey:
            raise ValueError("TxOutput: Se requiere un script_pubkey (dirección) válido.")

        self._value_alba: int = value_alba
        self._script_pubkey: str = script_pubkey

    @property
    def value_alba(self) -> int:
        return self._value_alba

    @property
    def script_pubkey(self) -> str:
        return self._script_pubkey

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value_alba": self._value_alba,
            "script_pubkey": self._script_pubkey
        }
    
    def __str__(self) -> str:
        return f"TxOutput(val={self._value_alba}, script={self._script_pubkey[:8]}...)"