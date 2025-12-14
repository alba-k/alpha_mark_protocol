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
            
            # Manejo robusto de script_sig
            if isinstance(script_sig, str):
                # Si viene como string (hex o texto), lo convertimos a bytes si es necesario
                # Por ahora asumimos utf-8 para mantener tu lógica
                self._script_sig: bytes = script_sig.encode('utf-8')
            elif isinstance(script_sig, bytes):
                self._script_sig: bytes = script_sig
            else:
                self._script_sig = b""

            # CAMBIO: Usamos debug para no ensuciar el log principal
            logger.debug(f"Input vinculado: {previous_tx_hash[:8]}...[{output_index}]")

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
        if isinstance(value, str):
            self._script_sig = value.encode('utf-8')
        elif isinstance(value, bytes):
            self._script_sig = value

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para guardar en DB."""
        try:
            # Intentamos decodificar a texto legible
            sig_str = self._script_sig.decode('utf-8')
        except UnicodeDecodeError:
            # Si son bytes binarios (firmas reales), usamos latin-1 o hex para no perder datos
            sig_str = self._script_sig.decode('latin-1')

        return {
            "previous_tx_hash": self._previous_tx_hash,
            "output_index": self._output_index,
            "script_sig": sig_str
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'TxInput':
        """
        [NUEVO] Reconstruye el Input desde la DB.
        Esencial para que Transaction.from_dict funcione.
        """
        return TxInput(
            previous_tx_hash=data.get("previous_tx_hash", ""),
            output_index=int(data.get("output_index", -1)),
            script_sig=data.get("script_sig", "")
        )