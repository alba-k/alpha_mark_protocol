# alpha_mark_protocol/akm/core/factories/transaction_factory.py
import time
from typing import List
from akm.core.models.transaction import Transaction
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput
from akm.core.services.transaction_hasher import TransactionHasher
# ⚡ IMPORTACIÓN REQUERIDA: Traemos la utilidad monetaria
from akm.core.utils.monetary import Monetary, MonetaryInput 

class TransactionFactory:

    # -----------------------------------------------------------------------
    # ⚡ NUEVO MÉTODO: Crea un Output seguro a partir de un monto AKM
    # -----------------------------------------------------------------------
    @staticmethod
    def create_output_from_akm(
        amount_akm: MonetaryInput, 
        script_pubkey: str
    ) -> TxOutput:
        """
        Convierte un monto de entrada del usuario (AKM, float/str) a Albas (int) 
        y crea un TxOutput seguro.
        """
        # 1. Conversión CRÍTICA: Aquí es donde usamos el conversor seguro
        value_alba = Monetary.to_albas(amount_akm)
        
        # ⚡ CORRECCIÓN DE TIPADO: String -> Bytes para Address
        script_bytes = script_pubkey.encode('utf-8') if isinstance(script_pubkey, str) else script_pubkey # pyright: ignore[reportUnnecessaryIsInstance]

        # 2. Creamos el modelo usando el entero limpio y bytes
        return TxOutput(value_alba=value_alba, script_pubkey=script_bytes)

    # -----------------------------------------------------------------------
    # MÉTODOS EXISTENTES
    # -----------------------------------------------------------------------
    @staticmethod
    def create_signed(
        inputs: List[TxInput],
        outputs: List[TxOutput],
        fee: int = 0
    ) -> Transaction:
        # Nota: Aquí asumimos que 'outputs' y 'fee' ya vienen en ALBAS limpios.
        timestamp = int(time.time())
        temp_tx = Transaction("", timestamp, inputs, outputs, fee)
        tx_id = TransactionHasher.calculate(temp_tx)
        return Transaction(tx_id, timestamp, inputs, outputs, fee)

    @staticmethod
    def create_coinbase(
        miner_pubkey_hash: str,
        block_height: int,
        total_reward: int
    ) -> Transaction:
        # total_reward ya es un entero (Alba) suministrado por el consenso, es seguro.
        coinbase_msg_str = f"Mined at height {block_height}"
        # ⚡ CORRECCIÓN: String -> Bytes para script_sig
        coinbase_msg_bytes = coinbase_msg_str.encode('utf-8')
        
        coinbase_input = TxInput(
            previous_tx_hash="0" * 64,  # Hash Nulo (String está bien aquí si el modelo lo permite, usualmente hashes son hex strings)
            output_index=0xFFFFFFFF,    # Índice Máximo
            script_sig=coinbase_msg_bytes
        )

        # ⚡ CORRECCIÓN: String -> Bytes para Address
        miner_addr_bytes = miner_pubkey_hash.encode('utf-8') if isinstance(miner_pubkey_hash, str) else miner_pubkey_hash # pyright: ignore[reportUnnecessaryIsInstance]

        coinbase_outputs = [
            TxOutput(value_alba=total_reward, script_pubkey=miner_addr_bytes)
        ]

        timestamp = int(time.time())

        temp_tx = Transaction(
            tx_hash="",
            timestamp=timestamp,
            inputs=[coinbase_input], 
            outputs=coinbase_outputs,
            fee=0
        )

        tx_id = TransactionHasher.calculate(temp_tx)

        return Transaction(
            tx_hash=tx_id,
            timestamp=timestamp,
            inputs=[coinbase_input],
            outputs=coinbase_outputs,
            fee=0
        )