# akm/core/models/tx_input.py

import logging
from typing import Dict, Any, Union

logger = logging.getLogger(__name__)

class TxInput:

    def __init__(self, previous_tx_hash: str, output_index: int, script_sig: Union[str, bytes]) -> None:
        try:
            if not previous_tx_hash:
                raise ValueError("Referencia a hash previo vacía.")
            if output_index < 0:
                raise ValueError("Índice de output negativo.")

            self._previous_tx_hash: str = previous_tx_hash
            self._output_index: int = output_index
            
            # [FIX] Normalización estricta para Firmas
            if isinstance(script_sig, bytes):
                self._script_sig: bytes = script_sig
            elif isinstance(script_sig, str):
                try:
                    self._script_sig: bytes = bytes.fromhex(script_sig)
                except ValueError:
                    self._script_sig: bytes = script_sig.encode('utf-8')
            else:
                self._script_sig = b""

        except Exception:
            logger.exception("Error en validación de TxInput")
    
    # --- Getters ---
    @property
    def previous_tx_hash(self) -> str: return self._previous_tx_hash
    @property
    def output_index(self) -> int: return self._output_index
    @property
    def script_sig(self) -> bytes: return self._script_sig

    @script_sig.setter
    def script_sig(self, value: Union[str, bytes]):
        if isinstance(value, bytes):
            self._script_sig = value
        elif isinstance(value, str):
             try:
                self._script_sig = bytes.fromhex(value)
             except ValueError:
                self._script_sig = value.encode('utf-8')

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la firma como HEX string."""
        return {
            "previous_tx_hash": self._previous_tx_hash,
            "output_index": self._output_index,
            "script_sig": self._script_sig.hex() # Siempre Hex
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'TxInput':
        """Reconstruye el Input (Soporta Hex String o Bytes directos)."""
        raw_sig = data.get("script_sig", "")
        
        # [FIX CRÍTICO]: Si ya viene como bytes (desde DB o interno), lo usamos directo.
        if isinstance(raw_sig, bytes):
            sig_bytes = raw_sig
        else:
            # Si es string, intentamos convertir de hex
            try:
                sig_bytes = bytes.fromhex(raw_sig)
            except ValueError:
                sig_bytes = raw_sig.encode('utf-8')

        return TxInput(
            previous_tx_hash=data.get("previous_tx_hash", ""),
            output_index=int(data.get("output_index", -1)),
            script_sig=sig_bytes
        )