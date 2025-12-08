# akm/core/models/transaction.py
from typing import List, Dict, Any, Optional
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput

# Importación diferida para evitar ciclos
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

class Transaction:
    """
    Representa una transacción. Soporta Scripting y SIGHASH.
    """

    def __init__(
        self,
        tx_hash: str, 
        timestamp: int,
        inputs: Optional[List[TxInput]] = None,
        outputs: Optional[List[TxOutput]] = None,
        fee: int = 0 
    ):
        # ... (Tus validaciones de tipos existentes se mantienen igual) ...
        if not isinstance(fee, int): raise TypeError(f"Fee debe ser int. Recibido: {type(fee)}") # pyright: ignore[reportUnnecessaryIsInstance]
        if fee < 0: raise ValueError("Fee negativo.")

        self._inputs: List[TxInput] = inputs if inputs is not None else []
        self._outputs: List[TxOutput] = outputs if outputs is not None else []
        self._tx_hash: str = tx_hash
        self._timestamp: int = timestamp
        self._fee: int = fee

    # --- Properties (Iguales que antes) ---
    @property
    def tx_hash(self) -> str: return self._tx_hash
    @property
    def inputs(self) -> List[TxInput]: return self._inputs[:]
    @property
    def outputs(self) -> List[TxOutput]: return self._outputs[:]
    @property
    def timestamp(self) -> int: return self._timestamp
    @property
    def fee(self) -> int: return self._fee
    
    @property
    def total_output_albas(self) -> int:
        return sum(out.value_alba for out in self._outputs)

    @property
    def is_coinbase(self) -> bool:
        if len(self._inputs) != 1: return False
        inp = self._inputs[0]
        return inp.previous_tx_hash == "0" * 64 and inp.output_index == 0xFFFFFFFF

    def set_final_hash(self, new_hash: str) -> None:
        self._tx_hash = new_hash

    # 🔥 NUEVO MÉTODO CRÍTICO PARA EL SCRIPT ENGINE 🔥
    def get_hash_for_signature(self, input_index: int, connected_script: Optional[bytes] = None) -> bytes:
        """
        Calcula el hash de la transacción "modificada" para ser firmada (SIGHASH_ALL).
        Lógica:
        1. Copia la TX.
        2. Vacía los scripts de todos los inputs.
        3. Pone el 'connected_script' (PubKey del Output previo) en el input actual.
        4. Calcula el hash binario.
        """
        from akm.core.services.transaction_hasher import TransactionHasher

        # Preparar inputs limpios
        temp_inputs: List[TxInput] = []
        for i, inp in enumerate(self._inputs):
            script_to_use: bytes = b''
            
            # Si estamos en el input que se firma, inyectamos el script del candado
            if i == input_index and connected_script:
                script_to_use = connected_script
            
            temp_inputs.append(TxInput(
                previous_tx_hash=inp.previous_tx_hash,
                output_index=inp.output_index,
                script_sig=script_to_use 
            ))

        # Crear TX temporal
        temp_tx = Transaction(
            tx_hash="", 
            timestamp=self._timestamp,
            inputs=temp_inputs,
            outputs=self._outputs, 
            fee=self._fee
        )

        # Calcular hash binario
        tx_hash_hex = TransactionHasher.calculate(temp_tx)
        return bytes.fromhex(tx_hash_hex)

    def to_dict(self) -> Dict[str, Any]:
        """Serialización para API/Red (Hexadecimal)."""
        return {
            "tx_hash": self._tx_hash,
            "inputs": [inp.to_dict() for inp in self._inputs],
            "outputs": [out.to_dict() for out in self._outputs],
            "timestamp": self._timestamp,
            "fee": str(self._fee)
        }