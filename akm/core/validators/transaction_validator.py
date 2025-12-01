# akm/core/validators/transaction_validator.py
'''
class TransactionValidator:
    Servicio de validación de seguridad.

    Methods::
        verify_integrity(transaction) -> bool:
            Recalcula el hash y confirma que coincide con el ID de la transacción.
        verify_signature(public_key, tx_hash, signature) -> bool:
            Verifica criptográficamente (ECDSA) que la firma sea válida para ese hash.
'''

import logging
import binascii
from ecdsa import VerifyingKey, SECP256k1, util, BadSignatureError # type: ignore

# Dependencias
from akm.core.models.transaction import Transaction
from akm.core.services.transaction_hasher import TransactionHasher

class TransactionValidator:

    @staticmethod
    def verify_integrity(transaction: Transaction) -> bool:

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