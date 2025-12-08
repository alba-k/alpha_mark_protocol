# akm/core/models/tx_input.py
from typing import Dict, Any, Union

class TxInput:
    """
    Modelo inmutable que representa una Entrada de Transacción.
    """

    def __init__(self, previous_tx_hash: str, output_index: int, script_sig: Union[str, bytes]):
        
        if not previous_tx_hash:
            raise ValueError("TxInput: Debe referenciar un hash de transacción previo.")
        if output_index < 0:
            raise ValueError("TxInput: El índice del output no puede ser negativo.")

        self._previous_tx_hash: str = previous_tx_hash
        self._output_index: int = output_index
        
        # ⚡ CORRECCIÓN BLINDADA: Aceptamos ambos y normalizamos a bytes internamente
        if isinstance(script_sig, str):
            self._script_sig: bytes = script_sig.encode('utf-8')
        elif isinstance(script_sig, bytes):
            self._script_sig: bytes = script_sig
        else:
            # Fallback seguro para evitar crashes
            self._script_sig = b""

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
    def script_sig(self, value: Union[str, bytes]):
        if isinstance(value, str):
            self._script_sig = value.encode('utf-8')
        elif isinstance(value, bytes):
            self._script_sig = value

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para la red/DB (JSON requiere string)."""
        try:
            sig_str = self._script_sig.decode('utf-8')
        except UnicodeDecodeError:
            sig_str = self._script_sig.decode('latin-1')

        return {
            "previous_tx_hash": self._previous_tx_hash,
            "output_index": self._output_index,
            "script_sig": sig_str
        }