# akm/core/validators/transaction_validator.py
'''
class TransactionValidator:
    Servicio de validación de seguridad (criptográfica) y económica (monetaria).

    Methods::
        verify_integrity(transaction) -> bool:
            Recalcula el hash y confirma que coincide con el ID de la transacción.
        verify_signature(public_key, tx_hash, signature) -> bool:
            Verifica criptográficamente (ECDSA) que la firma sea válida para ese hash.
        validate_monetary_balance(transaction, total_input_albas) -> bool:
            Verifica que el balance Inputs >= Outputs + Fee, usando solo enteros.
'''

import logging
import binascii
# Importaciones criptográficas (Se asume que son correctas)
from ecdsa import VerifyingKey, SECP256k1, util, BadSignatureError # type: ignore

# Dependencias
from akm.core.models.transaction import Transaction
from akm.core.services.transaction_hasher import TransactionHasher

class TransactionValidator:

    @staticmethod
    def verify_integrity(transaction: Transaction) -> bool:
        # Lógica existente para la validación de Hash
        calculated_hash = TransactionHasher.calculate(transaction)
        
        if calculated_hash != transaction.tx_hash:
            logging.warning(
               f'''
                TransactionValidator: Fallo de integridad. 
                Calculado: {calculated_hash}, Recibido: {transaction.tx_hash}
                '''
            )
            return False
            
        return True

    @staticmethod
    def verify_signature(public_key_hex: str, tx_hash: str, signature_hex: str) -> bool:
        # Lógica existente para la validación de Firma
        try:
            pub_key_bytes = binascii.unhexlify(public_key_hex)
            signature_bytes = binascii.unhexlify(signature_hex)
            hash_bytes = binascii.unhexlify(tx_hash)

            vk = VerifyingKey.from_string(pub_key_bytes, curve=SECP256k1) # type: ignore

            return vk.verify_digest(signature_bytes, hash_bytes, sigdecode=util.sigdecode_der) # type: ignore

        except (ValueError, BadSignatureError) as e:
            logging.error(f"TransactionValidator: Firma inválida o clave malformada. {e}")
            return False
        except Exception as e:
            logging.error(f"TransactionValidator: Error inesperado en verificación. {e}")
            return False

    # --------------------------------------------------------------------------
    # ⚡ NUEVO MÉTODO: VALIDACIÓN MONETARIA
    # --------------------------------------------------------------------------
    @staticmethod
    def validate_monetary_balance(transaction: Transaction, total_input_albas: int) -> bool:
        """
        Verifica que el valor de las entradas sea suficiente para cubrir 
        la suma de las salidas y la comisión. Todo en ALBAS (Enteros).
        
        Args:
            transaction: La transacción a validar.
            total_input_albas: El valor total (en Albas) de todas las entradas (UTXOs) gastadas.
        """
        
        # 1. Calcular el Costo Total (Outputs + Fee)
        # Los getters tx.total_output_albas y tx.fee ya devuelven enteros (Albas)
        total_cost_albas = transaction.total_output_albas + transaction.fee
        
        # 2. Validación de Cero (Regla de Saneamiento)
        if total_cost_albas <= 0:
            logging.error("TransactionValidator: Costo total inválido (cero o negativo).")
            return False
            
        # 3. Validación de Balance (Inputs >= Cost)
        if total_input_albas < total_cost_albas:
            logging.error(
                f"TransactionValidator: Fondos insuficientes. "
                f"Input total: {total_input_albas} Albas. "
                f"Costo total (Outputs + Fee): {total_cost_albas} Albas."
            )
            return False
            
        return True