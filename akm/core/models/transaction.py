# akm/core/models/transaction.py

import logging
from typing import List, Dict, Any, Optional

from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput
from akm.core.services.transaction_hasher import TransactionHasher

logger = logging.getLogger(__name__)

class Transaction:

    def __init__(
        self,
        tx_hash: str, 
        timestamp: int,
        inputs: Optional[List[TxInput]] = None,
        outputs: Optional[List[TxOutput]] = None,
        fee: int = 0 
    ) -> None:
        try:
            # [CORRECCIÓN] Eliminada la verificación isinstance(fee, int) 
            # para evitar la advertencia "Unnecessary isinstance call".
            # Confiamos en el type hinting y en el casting de from_dict.
            if fee < 0: 
                raise ValueError("Fee negativo.")

            self._inputs: List[TxInput] = inputs if inputs is not None else []
            self._outputs: List[TxOutput] = outputs if outputs is not None else []
            self._tx_hash: str = tx_hash
            self._timestamp: int = timestamp
            self._fee: int = fee

            if self._tx_hash:
                # Log en debug para no saturar consola
                logger.debug(f"TX {self._tx_hash[:8]}... instanciada.")

        except Exception:
            logger.exception("Error al inicializar Transaction")

    # --- Getters ---
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
        # Input nulo estándar: hash ceros y índice máximo
        return inp.previous_tx_hash == "0" * 64 and inp.output_index == 0xFFFFFFFF
    
    @tx_hash.setter
    def tx_hash(self, value: str):
        self._tx_hash = value

    def set_final_hash(self, new_hash: str) -> None:
        self._tx_hash = new_hash

    def get_hash_for_signature(self, input_index: int, connected_script: Optional[bytes] = None) -> bytes:
        """
        Calcula el hash de la transacción para ser firmado (SIGHASH_ALL).
        """
        # [CORRECCIÓN] Tipado explícito para evitar 'partially unknown'
        temp_inputs: List[TxInput] = []
        
        for i, inp in enumerate(self._inputs):
            script_to_use: bytes = b''
            
            # Solo copiamos el script si es el input que estamos firmando actualmente
            if i == input_index and connected_script:
                script_to_use = connected_script
            
            temp_inputs.append(TxInput(
                previous_tx_hash=inp.previous_tx_hash,
                output_index=inp.output_index,
                script_sig=script_to_use 
            ))

        temp_tx = Transaction(
            tx_hash="",
            timestamp=self._timestamp,
            inputs=temp_inputs,
            outputs=self._outputs, 
            fee=self._fee
        )

        tx_hash_hex = TransactionHasher.calculate(temp_tx)
        return bytes.fromhex(tx_hash_hex)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la transacción para DB/Red."""
        return {
            "tx_hash": self._tx_hash,
            "inputs": [inp.to_dict() for inp in self._inputs],
            "outputs": [out.to_dict() for out in self._outputs],
            "timestamp": self._timestamp,
            "fee": self._fee 
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Transaction':
        """
        Reconstruye la Transacción desde la DB.
        """
        # [CORRECCIÓN] Definimos el tipo explícito de la lista vacía
        # Esto elimina el error 'Type of append is partially unknown'
        inputs_list: List[TxInput] = []
        if 'inputs' in data:
            for inp_data in data['inputs']:
                inputs_list.append(TxInput.from_dict(inp_data))

        # [CORRECCIÓN] Lo mismo para outputs
        outputs_list: List[TxOutput] = []
        if 'outputs' in data:
            for out_data in data['outputs']:
                outputs_list.append(TxOutput.from_dict(out_data))

        return Transaction(
            tx_hash=data.get('tx_hash', ''),
            timestamp=int(data.get('timestamp', 0)),
            inputs=inputs_list,
            outputs=outputs_list,
            fee=int(data.get('fee', 0))
        )