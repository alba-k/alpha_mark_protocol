# akm/core/validators/transaction_validator.py

import logging
import binascii
from typing import Dict, Any

# Dependencias Criptográficas
from ecdsa import VerifyingKey, SECP256k1, util, BadSignatureError # type: ignore

# Dependencias del Proyecto
from akm.core.models.transaction import Transaction
from akm.core.services.transaction_hasher import TransactionHasher
from akm.core.scripting.engine import ScriptEngine

logger = logging.getLogger(__name__)

class TransactionValidator:

    @staticmethod
    def verify_integrity(transaction: Transaction) -> bool:
        try:
            calculated_hash = TransactionHasher.calculate(transaction)
            if calculated_hash != transaction.tx_hash:
                logger.info(f"Integridad TX fallida: ID {transaction.tx_hash[:8]}")
                return False
            return True
        except Exception:
            logger.exception("Bug en cálculo de integridad de transacción")
            return False

    @staticmethod
    def validate_monetary_balance(transaction: Transaction, total_input_albas: int) -> bool:
        try:
            total_cost = transaction.total_output_albas + transaction.fee
            
            if total_cost <= 0:
                logger.info(f"TX {transaction.tx_hash[:8]} rechazada: Costo <= 0.")
                return False
                
            if total_input_albas < total_cost:
                logger.info(f"TX {transaction.tx_hash[:8]} rechazada: Fondos insuficientes.")
                return False
            return True
        except Exception:
            logger.exception("Bug en validación de balance monetario")
            return False

    @staticmethod
    def verify_signature(public_key_hex: str, tx_hash: str, signature_hex: str) -> bool:
        """Verificación técnica de firma ECDSA (estándar SECP256k1)."""
        try:
            pub_key_bytes = binascii.unhexlify(public_key_hex)
            signature_bytes = binascii.unhexlify(signature_hex)
            hash_bytes = binascii.unhexlify(tx_hash)

            vk = VerifyingKey.from_string(pub_key_bytes, curve=SECP256k1) # type: ignore
            return vk.verify_digest(signature_bytes, hash_bytes, sigdecode=util.sigdecode_der) # type: ignore

        except (ValueError, BadSignatureError, binascii.Error):
            logger.info("Firma criptográfica inválida.")
            return False
        except Exception:
            logger.exception("Error técnico en motor ECDSA")
            return False

    @staticmethod
    def _engine_signature_adapter(signature: bytes, pub_key: bytes, tx: Any, input_idx: int) -> bool:
    
        try:
            tx_hash_bytes = tx.get_hash_for_signature(input_idx)
            
            return TransactionValidator.verify_signature(
                public_key_hex=pub_key.hex(),
                tx_hash=tx_hash_bytes.hex() if isinstance(tx_hash_bytes, bytes) else tx_hash_bytes,
                signature_hex=signature.hex()
            )
        except Exception as e:
            logger.error(f"Error en adaptador de firma: {e}")
            return False

    @staticmethod
    def verify_scripts(transaction: Transaction, previous_outputs: Dict[int, bytes]) -> bool:
        try:
            engine = ScriptEngine(signature_verifier=TransactionValidator._engine_signature_adapter)
            
            for i, inp in enumerate(transaction.inputs):
                script_pubkey = previous_outputs.get(i)
                
                if not script_pubkey:
                    logger.info(f"TX {transaction.tx_hash[:8]}: UTXO {i} no encontrado.")
                    return False

                if not engine.execute(
                    script_sig=inp.script_sig,
                    script_pubkey=script_pubkey,
                    transaction=transaction,
                    tx_input_index=i
                ):
                    logger.info(f"TX {transaction.tx_hash[:8]}: Script fallido en input {i}.")
                    return False
                    
            return True
        except Exception:
            logger.exception(f"Bug en ejecución de scripts para TX {transaction.tx_hash[:8]}")
            return False