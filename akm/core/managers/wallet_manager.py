# akm/core/managers/wallet_manager.py

import logging
import time
from typing import List

# Interfaces y Modelos
from akm.core.interfaces.i_signer import ISigner
from akm.core.managers.utxo_set import UTXOSet
from akm.core.models.transaction import Transaction
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput

# Servicios
from akm.core.services.transaction_hasher import TransactionHasher
from akm.infra.identity.address_factory import AddressFactory


logger = logging.getLogger(__name__)

class ScriptBuilder:
    OP_DUP = b'\x76'
    OP_HASH160 = b'\xa9'
    OP_EQUALVERIFY = b'\x88'
    OP_CHECKSIG = b'\xac'
    
    @staticmethod
    def build_p2pkh_lock(address_str: str) -> bytes:
        addr_bytes = address_str.encode('utf-8')
        push_op = bytes([len(addr_bytes)])
        return (ScriptBuilder.OP_DUP + ScriptBuilder.OP_HASH160 + push_op + addr_bytes + ScriptBuilder.OP_EQUALVERIFY + ScriptBuilder.OP_CHECKSIG)

    @staticmethod
    def build_p2pkh_unlock(signature: str, public_key: str) -> bytes:
        sig_bytes = signature.encode('utf-8')
        pub_bytes = public_key.encode('utf-8')
        push_sig = bytes([len(sig_bytes)])
        push_pub = bytes([len(pub_bytes)])
        return push_sig + sig_bytes + push_pub + pub_bytes

class WalletManager:

    def __init__(self, signer: ISigner):
        self._signer: ISigner = signer

    def sign_transaction_hash(self, tx_hash: str) -> str:
        try:
            if not tx_hash: raise ValueError("Hash de transacción vacío.")
            return self._signer.sign(tx_hash)
        except Exception:
            logger.exception("Error al generar firma digital")
            raise

    def get_public_key(self) -> str:
        return self._signer.get_public_key()
        
    def create_transaction(self, recipient_address: str, amount_alba: int, fee: int, utxo_set: UTXOSet) -> Transaction:
        try:
            public_key = self.get_public_key()
            my_address = AddressFactory.create_from_public_key(public_key)
            
            logger.info(f"Wallet: Buscando fondos para {my_address[:8]}...")
            
            available_utxos = utxo_set.get_utxos_for_address(my_address)
            inputs: List[TxInput] = []
            accumulated_value = 0
            required_total = amount_alba + fee

            for utxo_data in available_utxos:
                inputs.append(TxInput(
                    previous_tx_hash=utxo_data["tx_hash"],
                    output_index=utxo_data.get("output_index", utxo_data.get("index", 0)),
                    script_sig=b""
                ))
                val = utxo_data.get("amount") or utxo_data.get("value_alba") or 0
                accumulated_value += int(val)
                if accumulated_value >= required_total: break
            
            if accumulated_value < required_total:
                raise ValueError(f"Fondos insuficientes (Tienes {accumulated_value}, necesitas {required_total}).")

            outputs: List[TxOutput] = []
            script_pubkey_recipient = ScriptBuilder.build_p2pkh_lock(recipient_address)
            outputs.append(TxOutput(amount_alba, script_pubkey_recipient))
            
            change = accumulated_value - required_total
            if change > 0:
                script_pubkey_change = ScriptBuilder.build_p2pkh_lock(my_address)
                outputs.append(TxOutput(change, script_pubkey_change))
            
            tx = Transaction(tx_hash="", timestamp=int(time.time()), inputs=inputs, outputs=outputs, fee=fee)
            
            logger.info("Wallet: Firmando inputs...")
            unsigned_hash = TransactionHasher.calculate(tx)
            
            for inp in tx.inputs:
                signature = self.sign_transaction_hash(unsigned_hash)
                inp.script_sig = ScriptBuilder.build_p2pkh_unlock(signature, public_key)
            
            tx.tx_hash = TransactionHasher.calculate(tx)
            logger.info(f"Wallet: TX {tx.tx_hash[:8]} construida y firmada.")
            return tx

        except Exception:
            logger.exception("Fallo en la creación de transacción")
            raise