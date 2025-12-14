# akm/core/models/tx_output.py

import logging
from typing import Dict, Any, Union

logger = logging.getLogger(__name__)

class TxOutput:

    def __init__(self, value_alba: int, script_pubkey: Union[str, bytes]): 
        try:
            if value_alba < 0:
                raise ValueError("El valor del output no puede ser negativo.")
            if not script_pubkey:
                raise ValueError("Se requiere un script_pubkey (candado) válido.")

            self._value_alba: int = value_alba
            
            if isinstance(script_pubkey, str):
                self._script_pubkey: bytes = script_pubkey.encode('utf-8')
            elif isinstance(script_pubkey, bytes):
                self._script_pubkey: bytes = script_pubkey
            else:
                raise TypeError("script_pubkey debe ser str o bytes")

            # [MEJORA] Usamos debug para no saturar la consola al cargar miles de outputs
            logger.debug(f"Output creado: {value_alba} albas.")

        except Exception:
            logger.exception("Error en creación de TxOutput")

    @property
    def value_alba(self) -> int: return self._value_alba
    @property
    def script_pubkey(self) -> bytes: return self._script_pubkey

    def to_dict(self) -> Dict[str, Any]:
        try:
            script_str = self._script_pubkey.decode('utf-8')
        except UnicodeDecodeError:
            script_str = self._script_pubkey.decode('latin-1')

        return {
            "value_alba": str(self._value_alba), # Guardamos como string por seguridad en JSON
            "script_pubkey": script_str 
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'TxOutput':
        """
        [NUEVO] Método vital para leer desde la Base de Datos.
        """
        return TxOutput(
            # Convertimos de string a int, ya que to_dict lo guardó como string
            value_alba=int(data.get("value_alba", 0)),
            script_pubkey=data.get("script_pubkey", "")
        )
    
    def __str__(self) -> str:
        return f"TxOutput(val={self._value_alba}, script={self._script_pubkey!r})"