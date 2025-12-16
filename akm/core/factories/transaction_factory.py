# akm/core/factories/transaction_factory.py

import time
import struct
import logging
from typing import List

# Fuente de verdad global
from akm.core.config.protocol_constants import ProtocolConstants

# Modelos
from akm.core.models.transaction import Transaction
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput

# Servicios
from akm.core.services.transaction_hasher import TransactionHasher

logger = logging.getLogger(__name__)

class TransactionFactory:

    @staticmethod
    def _build_p2pkh_script(address: str) -> bytes:
        """
        [FIX] Genera un script P2PKH estándar para que WalletManager reconozca los fondos.
        Formato: OP_DUP OP_HASH160 <len> <address> OP_EQUALVERIFY OP_CHECKSIG
        """
        OP_DUP = b'\x76'
        OP_HASH160 = b'\xa9'
        OP_EQUALVERIFY = b'\x88'
        OP_CHECKSIG = b'\xac'
        
        addr_bytes = address.encode('utf-8')
        push_op = bytes([len(addr_bytes)])
        
        return (
            OP_DUP + 
            OP_HASH160 + 
            push_op + addr_bytes + 
            OP_EQUALVERIFY + 
            OP_CHECKSIG
        )

    @staticmethod
    def create_coinbase(miner_address: str, block_height: int, total_reward: int, extra_nonce: str = "") -> Transaction:
        try:
            # 1. Input: Altura + ExtraNonce (BIP34 para unicidad del Hash)
            # Empaquetamos la altura en binario (Little Endian)
            height_bytes = struct.pack("<I", block_height) 
            msg_bytes = extra_nonce.encode('utf-8')
            script_sig = height_bytes + msg_bytes
            
            tx_input = TxInput(
                previous_tx_hash=ProtocolConstants.COINBASE_PREV_HASH,
                output_index=ProtocolConstants.COINBASE_INDEX,
                script_sig=script_sig
            )

            # 2. Output: Pago al minero
            # [FIX CRÍTICO]: Usamos el script P2PKH en lugar de la dirección cruda
            script_pubkey = TransactionFactory._build_p2pkh_script(miner_address)
            
            tx_output = TxOutput(
                value_alba=total_reward,
                script_pubkey=script_pubkey
            )

            # 3. Ensamblaje temporal
            tx = Transaction(
                tx_hash="", 
                timestamp=int(time.time()),
                inputs=[tx_input],
                outputs=[tx_output],
                fee=0 
            )

            # 4. Sellado (Calculo del TXID)
            tx.tx_hash = TransactionHasher.calculate(tx)

            logger.info(f"Coinbase preparada: #{block_height} | ID: {tx.tx_hash[:8]}...")
            
            return tx

        except Exception:
            logger.exception(f"Error fatal creando Coinbase para bloque #{block_height}")
            raise

    @staticmethod
    def create_transfer(
        inputs: List[TxInput], 
        recipient_address: str, 
        amount: int, 
        change_address: str = "", 
        change_amount: int = 0,
        fee: int = 0
    ) -> Transaction:
        try:
            outputs: List[TxOutput] = [] 

            # A. Output Principal (Pago)
            # [FIX]: Aplicamos script P2PKH también aquí
            payment_script = TransactionFactory._build_p2pkh_script(recipient_address)
            payment_output = TxOutput(
                value_alba=amount,
                script_pubkey=payment_script
            )
            outputs.append(payment_output)

            # B. Output de Cambio (Si aplica)
            if change_address and change_amount > 0:
                # [FIX]: Aplicamos script P2PKH al cambio
                change_script = TransactionFactory._build_p2pkh_script(change_address)
                change_output = TxOutput(
                    value_alba=change_amount,
                    script_pubkey=change_script
                )
                outputs.append(change_output)

            # C. Ensamblaje
            tx = Transaction(
                tx_hash="",
                timestamp=int(time.time()),
                inputs=inputs,
                outputs=outputs,
                fee=fee
            )

            # D. Sellado
            tx.tx_hash = TransactionHasher.calculate(tx)
            
            logger.info(f"Transferencia preparada: {amount} albas | ID: {tx.tx_hash[:]}...")
            
            return tx

        except Exception:
            logger.exception("Error fatal creando transacción de transferencia")
            raise