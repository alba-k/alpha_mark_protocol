# akm/core/models/transaction.py
from typing import List, Dict, Any, Optional
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput
from akm.core.utils.monetary import Monetary 

class Transaction:
    """
    Representa una transacción en la red Alpha Mark.
    Todos los valores monetarios (value, fee) se almacenan como enteros (Albas).
    """

    def __init__(
        self,
        tx_hash: str, 
        timestamp: int,
        inputs: Optional[List[TxInput]] = None,
        outputs: Optional[List[TxOutput]] = None,
        fee: int = 0 
    ):
        # --- VALIDACIONES DE SEGURIDAD ---
        if not isinstance(fee, int): # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"CRÍTICO: El 'fee' debe ser un entero (Albas). Recibido: {type(fee).__name__}")
        
        if fee < 0:
            raise ValueError("CRÍTICO: El fee de transacción no puede ser negativo.")

        self._inputs: List[TxInput] = inputs if inputs is not None else []
        self._outputs: List[TxOutput] = outputs if outputs is not None else []
        
        self._tx_hash: str = tx_hash
        self._timestamp: int = timestamp
        self._fee: int = fee

    @property
    def tx_hash(self) -> str: return self._tx_hash
    @property
    def inputs(self) -> List[TxInput]: return self._inputs[:]
    @property
    def outputs(self) -> List[TxOutput]: return self._outputs[:]
    @property
    def timestamp(self) -> int: return self._timestamp

    @property
    def fee(self) -> int: 
        """Retorna la comisión de la transacción en Albas (Entero)."""
        return self._fee
        
    @property
    def fee_akm_display(self) -> str:
        """Helper para visualización: Retorna el fee formateado como string AKM."""
        val = Monetary.to_akm(self._fee)
        return f"{val:.8f}"

    @property
    def total_output_albas(self) -> int:
        """Calcula la suma total enviada a los destinatarios (sin contar el fee)."""
        return sum(out.value_alba for out in self._outputs)

    @property
    def is_coinbase(self) -> bool:
        """Retorna True si es una Coinbase Real (Transacción de recompensa minera)."""
        if len(self._inputs) != 1:
            return False
        
        inp = self._inputs[0]
        return inp.previous_tx_hash == "0" * 64 and inp.output_index == 0xFFFFFFFF

    def set_final_hash(self, new_hash: str) -> None:
        """Permite actualizar el hash una vez calculado."""
        self._tx_hash = new_hash

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa la transacción para la red P2P. Todos los valores monetarios 
        (fee y output values) se convierten a STR para evitar la pérdida de precisión por float.
        """
        return {
            "tx_hash": self._tx_hash,
            "inputs": [inp.to_dict() for inp in self._inputs],
            "outputs": [out.to_dict() for out in self._outputs],
            "timestamp": self._timestamp,
            "fee": str(self._fee) # ⚡ CORRECCIÓN CLAVE: Convertir INT a STR para la red
        }