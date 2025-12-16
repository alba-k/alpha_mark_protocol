# akm/core/models/tx_output.py

import logging
from typing import Dict, Any, Union

logger = logging.getLogger(__name__)

class TxOutput:
    """
    Representa una salida de transacción (Un lock/candado con monedas).
    """

    def __init__(self, value_alba: int, script_pubkey: Union[str, bytes]): 
        # Validación defensiva
        if value_alba < 0:
            raise ValueError("El valor del output no puede ser negativo.")
        
        self._value_alba: int = value_alba
        
        # [FIX] Normalización estricta
        if isinstance(script_pubkey, bytes):
            self._script_pubkey: bytes = script_pubkey
        elif isinstance(script_pubkey, str):
            try:
                self._script_pubkey: bytes = bytes.fromhex(script_pubkey)
            except ValueError:
                self._script_pubkey: bytes = script_pubkey.encode('utf-8')
        else:
            raise TypeError(f"script_pubkey debe ser str (hex) o bytes. Recibido: {type(script_pubkey)}")

    @property
    def value_alba(self) -> int: 
        return self._value_alba

    @property
    def script_pubkey(self) -> bytes: 
        return self._script_pubkey

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa usando HEXADECIMAL. 
        """
        return {
            "value_alba": self._value_alba,
            "script_pubkey": self._script_pubkey.hex() # Siempre Hex
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'TxOutput':
        """
        Reconstruye (Soporta Hex String o Bytes directos).
        """
        raw_script = data.get("script_pubkey", "")
        
        # [FIX CRÍTICO]: Si ya viene como bytes (desde DB o interno), lo usamos directo.
        if isinstance(raw_script, bytes):
            script_bytes = raw_script
        else:
            try:
                script_bytes = bytes.fromhex(raw_script)
            except ValueError:
                script_bytes = raw_script.encode('utf-8')

        return TxOutput(
            value_alba=int(data.get("value_alba", 0)),
            script_pubkey=script_bytes
        )
    
    def __repr__(self) -> str:
        return f"<TxOutput val={self._value_alba} script={self._script_pubkey.hex()[:8]}...>"