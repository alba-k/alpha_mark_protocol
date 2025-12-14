# akm/core/services/signature_verifier_service.py

import logging
from typing import Any

# Importamos librería criptográfica (silenciando errores de tipado legacy)
from ecdsa import VerifyingKey, SECP256k1, util, BadSignatureError # type: ignore

# Importamos el modelo para poder llamar a get_hash_for_signature
from akm.core.models.transaction import Transaction

logger = logging.getLogger(__name__)

class SignatureVerifierService:
    """
    Servicio de Dominio encargado de la verificación criptográfica (ECDSA).
    Se inyecta en el ScriptEngine para resolver la operación OP_CHECKSIG.
    """

    @staticmethod
    def verify(signature: bytes, public_key: bytes, transaction: Any, input_index: int) -> bool:
        """
        Verifica si la 'signature' es válida para la 'public_key' dada y la transacción actual.
        """
        try:
            # 1. Validación de Tipo
            if not isinstance(transaction, Transaction):
                logger.error("SignatureVerifier recibió un objeto que no es Transaction.")
                return False
            
            tx: Transaction = transaction

            # 2. Reconstruir el Hash del Mensaje (SIGHASH)
            # Calculamos el hash de la transacción modificada (input actual con script vacío).
            # Nota: Al usar connected_script=b'', estamos validando la firma sobre la estructura
            # de la transacción, excluyendo el script previo.
            message_hash_bytes = tx.get_hash_for_signature(input_index, connected_script=b'')
            
            # 3. Decodificar Clave Pública
            try:
                vk = VerifyingKey.from_string(public_key, curve=SECP256k1) # type: ignore
            except Exception:
                logger.warning(f"Clave pública inválida en input {input_index}.")
                return False

            # 4. Verificar Firma (ECDSA)
            return vk.verify_digest(signature, message_hash_bytes, sigdecode=util.sigdecode_der) # type: ignore

        except BadSignatureError:
            return False # Firma incorrecta
            
        except Exception as e:
            logger.error(f"Error inesperado en verificador de firmas: {e}")
            return False