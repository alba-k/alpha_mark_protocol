# akm/core/models/tx_output.py
from typing import Dict, Any, Union

class TxOutput:
    """
    Modelo inmutable que representa una Salida de Transacción (UTXO).
    """

    def __init__(self, value_alba: int, script_pubkey: Union[str, bytes]):
        if value_alba < 0:
            raise ValueError("TxOutput: El valor no puede ser negativo.")
        if not script_pubkey:
            raise ValueError("TxOutput: Se requiere un script_pubkey válido.")

        self._value_alba: int = value_alba
        
        # ⚡ CORRECCIÓN: Normalización a bytes interna
        if isinstance(script_pubkey, str):
            self._script_pubkey: bytes = script_pubkey.encode('utf-8')
        elif isinstance(script_pubkey, bytes):
            self._script_pubkey: bytes = script_pubkey
        else:
            raise TypeError("script_pubkey debe ser str o bytes")

    @property
    def value_alba(self) -> int:
        return self._value_alba

    @property
    def script_pubkey(self) -> bytes:
        return self._script_pubkey

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa el Output.
        Importante: Decodificamos bytes a string para que JSON no se rompa ni guarde "b'...'".
        """
        try:
            # Intentamos UTF-8 (direcciones normales)
            script_str = self._script_pubkey.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback para datos binarios puros (latin-1 preserva bytes 1:1)
            script_str = self._script_pubkey.decode('latin-1')

        return {
            "value_alba": str(self._value_alba),
            "script_pubkey": script_str  # Guardamos string limpio "1A1z..."
        }
    
    def __str__(self) -> str:
        return f"TxOutput(val={self._value_alba}, script={self._script_pubkey!r})"