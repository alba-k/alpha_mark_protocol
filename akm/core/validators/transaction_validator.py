# akm/core/validators/transaction_validator.py
import logging
import binascii
from typing import Dict

# Dependencias Criptográficas
from ecdsa import VerifyingKey, SECP256k1, util, BadSignatureError # type: ignore

# Dependencias del Proyecto
from akm.core.models.transaction import Transaction
from akm.core.services.transaction_hasher import TransactionHasher

# Intentamos importar ScriptEngine, si no existe (aún no creado), fallamos suavemente
try:
    from akm.core.scripting.engine import ScriptEngine
except ImportError:
    ScriptEngine = None # type: ignore

logger = logging.getLogger(__name__)

class TransactionValidator:

    @staticmethod
    def verify_integrity(transaction: Transaction) -> bool:
        """Verifica que el hash (TXID) coincida con el contenido."""
        calculated_hash = TransactionHasher.calculate(transaction)
        if calculated_hash != transaction.tx_hash:
            logger.warning(f"Integridad fallida. Calc: {calculated_hash} != Recibido: {transaction.tx_hash}")
            return False
        return True

    @staticmethod
    def validate_monetary_balance(transaction: Transaction, total_input_albas: int) -> bool:
        """Verifica que Inputs >= Outputs + Fee."""
        total_cost = transaction.total_output_albas + transaction.fee
        
        if total_cost <= 0:
            logger.error("Costo total inválido (cero o negativo).")
            return False
            
        if total_input_albas < total_cost:
            logger.error(f"Fondos insuficientes. In: {total_input_albas} < Out: {total_cost}")
            return False
        return True

    # --------------------------------------------------------------------------
    # MÉTODO CLÁSICO (COMPATIBILIDAD): Verifica una firma ECDSA suelta
    # --------------------------------------------------------------------------
    @staticmethod
    def verify_signature(public_key_hex: str, tx_hash: str, signature_hex: str) -> bool:
        """
        Verifica criptográficamente (ECDSA) que la firma sea válida para ese hash.
        Usado por TransactionRulesValidator en modo Legacy.
        """
        try:
            pub_key_bytes = binascii.unhexlify(public_key_hex)
            signature_bytes = binascii.unhexlify(signature_hex)
            hash_bytes = binascii.unhexlify(tx_hash)

            vk = VerifyingKey.from_string(pub_key_bytes, curve=SECP256k1) # type: ignore

            # sigdecode=util.sigdecode_der es el estándar para Bitcoin/ECDSA
            return vk.verify_digest(signature_bytes, hash_bytes, sigdecode=util.sigdecode_der) # type: ignore

        except (ValueError, BadSignatureError, binascii.Error) as e:
            logger.error(f"Firma inválida o clave malformada: {e}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado en verificación de firma: {e}")
            return False

    # --------------------------------------------------------------------------
    # MÉTODO NUEVO (SCRIPTING): Usa la Stack Machine (Si está disponible)
    # --------------------------------------------------------------------------
    @staticmethod
    def verify_scripts(transaction: Transaction, previous_outputs: Dict[int, bytes]) -> bool:
        if not ScriptEngine:
            logger.warning("Motor de Scripting no disponible. Saltando validación de scripts.")
            return True

        engine = ScriptEngine() # type: ignore
        
        for i, inp in enumerate(transaction.inputs):
            script_pubkey = previous_outputs.get(i)
            
            if not script_pubkey:
                logger.error(f"TX {transaction.tx_hash}: Input {i} referencia UTXO desconocido.")
                return False

            success = engine.execute(
                script_sig=inp.script_sig,
                script_pubkey=script_pubkey,
                transaction=transaction,
                tx_input_index=i
            )
            
            if not success:
                logger.warning(f"TX {transaction.tx_hash}: Falló Script en Input {i}.")
                return False
                
        return True