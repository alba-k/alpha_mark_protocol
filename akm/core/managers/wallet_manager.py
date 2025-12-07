# akm/core/managers/wallet_manager.py
import logging
from typing import List
from decimal import Decimal # Necesario para el tipo de retorno en get_display_balance

from akm.core.interfaces.i_signer import ISigner
from akm.core.managers.utxo_set import UTXOSet
from akm.core.models.transaction import Transaction
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput
from akm.core.factories.transaction_factory import TransactionFactory
from akm.core.services.transaction_hasher import TransactionHasher
from akm.infra.identity.address_factory import AddressFactory
# ⚡ IMPORTACIÓN REQUERIDA: Usamos el conversor monetario seguro
from akm.core.utils.monetary import Monetary 

logging.basicConfig(level=logging.INFO, format='[Wallet] %(message)s')

class WalletManager:

    def __init__(self, signer: ISigner):
        self._signer: ISigner = signer

    def sign_transaction_hash(self, tx_hash: str) -> str:
        if not tx_hash:
            logging.error('WalletManager: Se intentó firmar un hash vacío.')
            raise ValueError('El hash de la transacción es inválido o vacío.')

        signature: str = self._signer.sign(tx_hash)
        logging.info(f'WalletManager: Hash {tx_hash[:8]}... firmado exitosamente.')
        return signature

    def get_public_key(self) -> str:
        return self._signer.get_public_key()
        
    # --------------------------------------------------------------------------
    # ⚡ NUEVO MÉTODO: Reporte de saldo seguro (Core -> Usuario)
    # --------------------------------------------------------------------------
    def get_display_balance(self, utxo_set: UTXOSet) -> Decimal:
        """
        Consulta el saldo interno (Albas) y lo convierte a AKM (Decimal) 
        para una visualización segura y precisa.
        """
        public_key = self.get_public_key()
        my_address = AddressFactory.create_from_public_key(public_key)
        
        # 1. Obtener el saldo interno (siempre es un INT de Albas)
        balance_albas = utxo_set.get_balance_for_address(my_address)
        
        # 2. Convertir a formato legible (Decimal AKM)
        return Monetary.to_akm(balance_albas)

    # --------------------------------------------------------------------------
    # MODIFICACIÓN AL create_transaction (sin cambio de lógica, solo una mejora de log)
    # --------------------------------------------------------------------------
    def create_transaction(
        self, 
        recipient_address: str, 
        amount_alba: int, # Ya es un INT (Albas)
        fee: int,         # Ya es un INT (Albas)
        utxo_set: UTXOSet
    ) -> Transaction:
        # 1. Obtener mi identidad real
        public_key = self.get_public_key()
        my_address = AddressFactory.create_from_public_key(public_key)
        
        logging.info(f"🔍 Buscando fondos para la dirección: {my_address}")
        
        # 2. Buscar fondos
        available_utxos = utxo_set.get_utxos_for_address(my_address)
        
        inputs: List[TxInput] = []
        accumulated_value = 0
        required_total = amount_alba + fee

        for utxo_data in available_utxos:
            inputs.append(TxInput(
                previous_tx_hash=utxo_data["tx_hash"],
                output_index=utxo_data["output_index"],
                script_sig="" 
            ))
            # 'utxo_data["amount"]' ya es un entero (Albas), lo cual es seguro.
            accumulated_value += utxo_data["amount"]
            
            if accumulated_value >= required_total:
                break
        
        # Validación de balance (todo en enteros Albas)
        if accumulated_value < required_total:
            # Usamos Monetary.to_akm() solo para el mensaje de error legible
            balance_akm = Monetary.to_akm(accumulated_value)
            required_akm = Monetary.to_akm(required_total)
            raise ValueError(
                f"Fondos insuficientes. Tienes {balance_akm:.8f} AKM, requieres {required_akm:.8f} AKM."
            )

        # 3. Outputs
        outputs: List[TxOutput] = []
        outputs.append(TxOutput(amount_alba, recipient_address))
        
        change = accumulated_value - required_total
        if change > 0:
            outputs.append(TxOutput(change, my_address))
            
        tx = TransactionFactory.create_signed(inputs, outputs, fee=fee)
        
        # 4. Firmar Inputs
        for inp in tx.inputs:
            signature = self.sign_transaction_hash(tx.tx_hash)
            inp.script_sig = f"{signature} {public_key}" 
            
        # 5. Hash final
        final_hash = TransactionHasher.calculate(tx)
        tx.set_final_hash(final_hash)
        
        # Usamos Monetary.to_akm() para el log (sin tocar el valor interno)
        amount_akm_display = Monetary.to_akm(amount_alba)
        logging.info(f"✅ Transacción creada: {tx.tx_hash[:8]} | Envía {amount_akm_display:.8f} AKM a {recipient_address[:8]}...")
        return tx