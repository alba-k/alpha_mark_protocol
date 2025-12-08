# akm/core/models/tx_input.py
from typing import Dict, Any

class TxInput:
    """
    Representa una entrada de transacción.
    ScriptSig ahora se almacena como bytes crudos para el motor de scripting.
    """

    def __init__(self, previous_tx_hash: str, output_index: int, script_sig: bytes):
        if not previous_tx_hash or len(previous_tx_hash) == 0:
            raise ValueError("TxInput: Debe referenciar un hash de transacción previo.")
        if output_index < 0:
            raise ValueError("TxInput: El índice del output no puede ser negativo.")
        if not isinstance(script_sig, bytes):
            raise TypeError(f"TxInput: script_sig debe ser bytes, recibido {type(script_sig)}")

        self._previous_tx_hash: str = previous_tx_hash
        self._output_index: int = output_index
        self._script_sig: bytes = script_sig

    @property
    def previous_tx_hash(self) -> str:
        return self._previous_tx_hash

    @property
    def output_index(self) -> int:
        return self._output_index

    @property
    def script_sig(self) -> bytes:
        return self._script_sig

    @script_sig.setter
    def script_sig(self, value: bytes):
        if not isinstance(value, bytes):
            raise TypeError("script_sig debe ser bytes")
        self._script_sig = value

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a JSON (convertimos bytes a HEX)."""
        return {
            "previous_tx_hash": self._previous_tx_hash,
            "output_index": self._output_index,
            # 🔥 CORRECCIÓN: Bytes -> Hex String para transmisión segura
            "script_sig": self._script_sig.hex()
        }

    def __str__(self) -> str:
        return f"TxInput(prev={self._previous_tx_hash[:8]}..., idx={self._output_index})"