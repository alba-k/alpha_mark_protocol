# akm/core/factories/transaction_factory.py
'''
class TransactionFactory:
    Fábrica encargada de la construcción segura de transacciones.
    Centraliza la lógica de creación, cálculo de hash y firma.

    Methods::
        create_pay_to_public_key_hash(inputs, outputs, timestamp) -> Transaction:
            Crea una transacción estándar de pago (P2PKH).
        create_coinbase(miner_pubkey_hash, block_height, total_reward) -> Transaction:
            Crea la transacción especial de generación de monedas (Coinbase).
'''

import time
from typing import List
from akm.core.models.transaction import Transaction
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput
from akm.core.services.transaction_hasher import TransactionHasher

class TransactionFactory:

    @staticmethod
    def create_pay_to_public_key_hash(
        inputs: List[TxInput],
        outputs: List[TxOutput],
        timestamp: int = 0
    ) -> Transaction:
        """
        Construye una transacción estándar.
        Calcula el hash (TXID) automáticamente basándose en el contenido.
        """
        # Si no se provee tiempo, usamos el actual (UTC Unix Seconds)
        if timestamp == 0:
            timestamp = int(time.time())

        # 1. Crear instancia temporal sin hash (Dummy Hash) para poder serializarla
        temp_tx = Transaction(
            tx_hash="",
            timestamp=timestamp,
            inputs=inputs,
            outputs=outputs,
            fee=0 # El fee se calcula externamente o se deduce implícitamente (Inputs - Outputs)
        )

        # 2. Calcular el Hash Real (TXID) usando el servicio de dominio
        tx_id = TransactionHasher.calculate(temp_tx)

        # 3. Retornar el objeto inmutable definitivo
        return Transaction(
            tx_hash=tx_id,
            timestamp=timestamp,
            inputs=inputs,
            outputs=outputs,
            fee=0
        )

    @staticmethod
    def create_coinbase(
        miner_pubkey_hash: str,
        block_height: int,
        total_reward: int
    ) -> Transaction:
        """
        Crea la transacción Coinbase (Emisión).
        Reglas: Sin inputs reales, paga el subsidio + fees al minero.
        """
        # Coinbase Input: No referencia UTXO previo.
        # En Bitcoin se usa el hash nulo y el índice 0xFFFFFFFF.
        # Aquí usamos convención simplificada: lista vacía de inputs.
        # (Opcional: Podríamos agregar un input con datos arbitrarios 'height' como script_sig para entropía extra)
        coinbase_inputs: List[TxInput] = []

        # Coinbase Output: El pago al minero
        coinbase_outputs = [
            TxOutput(value_alba=total_reward, script_pubkey=miner_pubkey_hash)
        ]

        timestamp = int(time.time())

        # Instancia temporal
        temp_tx = Transaction(
            tx_hash="",
            timestamp=timestamp,
            inputs=coinbase_inputs,
            outputs=coinbase_outputs
        )

        # Hash definitivo
        tx_id = TransactionHasher.calculate(temp_tx)

        return Transaction(
            tx_hash=tx_id,
            timestamp=timestamp,
            inputs=coinbase_inputs,
            outputs=coinbase_outputs
        )