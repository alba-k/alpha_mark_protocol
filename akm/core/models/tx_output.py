# akm/core/models/tx_output.py
from typing import Dict, Any

class TxOutput:
    """
    Salida de transacción (UTXO). 
    ScriptPubKey almacena el 'candado' criptográfico en bytes.
    """

    def __init__(self, value_alba: int, script_pubkey: bytes):
        if value_alba < 0:
            raise ValueError("TxOutput: El valor no puede ser negativo.")
        if not script_pubkey or not isinstance(script_pubkey, bytes):
            raise ValueError("TxOutput: script_pubkey debe ser bytes válidos.")

        self._value_alba: int = value_alba
        self._script_pubkey: bytes = script_pubkey

    @property
    def value_alba(self) -> int:
        return self._value_alba

    @property
    def script_pubkey(self) -> bytes:
        return self._script_pubkey

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa el Output. 
        - value_alba -> String (para precisión en JSON)
        - script_pubkey -> Hex String
        """
        return {
            "value_alba": str(self._value_alba),
            # 🔥 CORRECCIÓN: Bytes -> Hex String
            "script_pubkey": self._script_pubkey.hex()
        }
    
    def __str__(self) -> str:
        # Mostramos solo el inicio del script en hex para debug
        script_hex = self._script_pubkey.hex()
        preview = script_hex[:16] + "..." if len(script_hex) > 16 else script_hex
        return f"TxOutput(val={self._value_alba}, script={preview})"