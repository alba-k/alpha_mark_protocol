# akm/core/services/transaction_hasher.py
'''
class TransactionHasher:
    Servicio de dominio encargado de generar la Identidad Única de una transacción.

    Methods:
        calculate(transaction) -> str:
            Genera el Doble SHA-256 de los componentes inmutables de la transacción.
'''

import json
from typing import Dict, Any

# Dependencias del Dominio
from akm.core.models.transaction import Transaction
from akm.core.utils.crypto_utility import CryptoUtility

class TransactionHasher:

    @staticmethod
    def calculate(transaction: Transaction) -> str:

        payload: Dict[str, Any] = {
            "inputs": [inp.to_dict() for inp in transaction.inputs],
            "outputs": [out.to_dict() for out in transaction.outputs],
            "timestamp": transaction.timestamp,
            "fee": transaction.fee
        }

        serialized_payload = json.dumps(payload, sort_keys=True)
        return CryptoUtility.double_sha256(serialized_payload)