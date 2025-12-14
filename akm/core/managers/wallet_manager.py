# akm/core/managers/wallet_manager.py

import logging
import time
from typing import List
from decimal import Decimal

# Interfaces y Modelos
from akm.core.interfaces.i_signer import ISigner
from akm.core.managers.utxo_set import UTXOSet
from akm.core.models.transaction import Transaction
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput

# Servicios
from akm.core.services.transaction_hasher import TransactionHasher
from akm.infra.identity.address_factory import AddressFactory

# Utilidades
from akm.core.utils.monetary import Monetary 

logger = logging.getLogger(__name__)

class WalletManager:

    def __init__(self, signer: ISigner):
        self._signer: ISigner = signer
        logger.info("WalletManager activo.")

    def sign_transaction_hash(self, tx_hash: str) -> str:
        try:
            if not tx_hash:
                raise ValueError("Hash de transacción vacío.")
            return self._signer.sign(tx_hash)
        except Exception:
            logger.exception("Error al generar firma digital")
            raise

    def get_public_key(self) -> str:
        return self._signer.get_public_key()
        
    def get_display_balance(self, utxo_set: UTXOSet) -> Decimal:
        try:
            public_key = self.get_public_key()
            my_address = AddressFactory.create_from_public_key(public_key)
            balance_albas = utxo_set.get_balance_for_address(my_address)
            return Monetary.to_akm(balance_albas)
        except Exception:
            logger.exception("Error consultando saldo")
            return Decimal(0)

    def create_transaction(
        self, 
        recipient_address: str, 
        amount_alba: int, 
        fee: int,         
        utxo_set: UTXOSet
    ) -> Transaction:
    
        try:
            # 1. Identificación
            public_key = self.get_public_key()
            my_address = AddressFactory.create_from_public_key(public_key)
            
            logger.info(f"Wallet: Buscando fondos para {my_address[:8]}...")
            
            # 2. Coin Selection (UTXOs)
            available_utxos = utxo_set.get_utxos_for_address(my_address)
            inputs: List[TxInput] = []
            accumulated_value = 0
            required_total = amount_alba + fee

            for utxo_data in available_utxos:
                inputs.append(TxInput(
                    previous_tx_hash=utxo_data["tx_hash"],
                    output_index=utxo_data["output_index"],
                    script_sig=b"" # Vacío para el pre-image
                ))
                accumulated_value += utxo_data["amount"]
                if accumulated_value >= required_total:
                    break
            
            if accumulated_value < required_total:
                raise ValueError(f"Fondos insuficientes (Tienes {accumulated_value} albas).")

            # 3. Construcción de Outputs
            outputs: List[TxOutput] = [TxOutput(amount_alba, recipient_address.encode('utf-8'))]
            
            change = accumulated_value - required_total
            if change > 0:
                outputs.append(TxOutput(change, my_address.encode('utf-8')))
            
            # 4. Instanciación Base
            tx = Transaction(
                tx_hash="", 
                timestamp=int(time.time()),
                inputs=inputs,
                outputs=outputs,
                fee=fee
            )
            
            # 5. Proceso de Firma
            logger.info("Wallet: Firmando inputs...")
            unsigned_hash = TransactionHasher.calculate(tx)
            
            for inp in tx.inputs:
                signature = self.sign_transaction_hash(unsigned_hash)
                # Formato estándar: [Firma PK]
                inp.script_sig = f"{signature} {public_key}".encode('utf-8')
                
            # 6. Sellado Final (TxID)
            tx.tx_hash = TransactionHasher.calculate(tx)
            
            logger.info(f"Wallet: TX {tx.tx_hash[:8]} lista para envío.")
            return tx

        except Exception:
            logger.exception("Fallo en la creación de transacción")
            raise