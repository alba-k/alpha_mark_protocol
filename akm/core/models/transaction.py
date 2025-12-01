# akm/core/models/transaction.py
'''
class Transaction:
    Entidad central del modelo UTXO. Representa una transferencia de valor atómica.
    Una transacción consume Inputs (monedas viejas) y crea Outputs (monedas nuevas).

    Attributes::
        tx_hash (str): Identificador único calculado (Double SHA-256).
        inputs (List[TxInput]): Lista de fondos a gastar (referencias a UTXOs).
        outputs (List[TxOutput]): Lista de nuevos fondos creados (nuevos UTXOs).
        timestamp (float): Momento exacto de creación.
        fee (int): Comisión pagada a la red (Inputs - Outputs).

    Methods::
        to_dict() -> Dict[str, Any]:
            Serializa la transacción completa accediendo a los datos privados internos.
'''

from typing import List, Dict, Any, Optional
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput

class Transaction:

    def __init__(
        self,
        tx_hash: str,
        timestamp: int,
        inputs: Optional[List[TxInput]] = None,
        outputs: Optional[List[TxOutput]] = None,
        fee: int = 0
    ):
        
        inputs_saneados = inputs if inputs is not None else []
        outputs_saneados = outputs if outputs is not None else []


        self._tx_hash: str = tx_hash
        self._inputs: List[TxInput] = inputs_saneados
        self._outputs: List[TxOutput] = outputs_saneados
        self._timestamp: int = timestamp
        self._fee: int = fee

    

    @property
    def tx_hash(self) -> str:
        return self._tx_hash

    @property
    def inputs(self) -> List[TxInput]:
        # Retornamos una copia superficial para proteger la lista interna
        return self._inputs[:]

    @property
    def outputs(self) -> List[TxOutput]:
        # Retornamos una copia superficial
        return self._outputs[:]

    @property
    def timestamp(self) -> int:
        return self._timestamp

    @property
    def fee(self) -> int:
        return self._fee

    

    def to_dict(self) -> Dict[str, Any]:
        
        return {
            "tx_hash": self._tx_hash,
            "inputs": [inp.to_dict() for inp in self._inputs],
            "outputs": [out.to_dict() for out in self._outputs],
            "timestamp": self._timestamp,
            "fee": self._fee
        }

    def __str__(self) -> str:
        return (
            f"Transaction(hash={self._tx_hash[:8]}..., "
            f"in={len(self._inputs)}, out={len(self._outputs)}, "
            f"fee={self._fee})"
        )