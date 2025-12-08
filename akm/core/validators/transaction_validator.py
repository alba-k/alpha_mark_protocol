# akm/core/validators/transaction_validator.py
import logging
from typing import Dict

from akm.core.models.transaction import Transaction
from akm.core.services.transaction_hasher import TransactionHasher
from akm.core.scripting.engine import ScriptEngine

logger = logging.getLogger(__name__)

class TransactionValidator:
    """
    Servicio de validación integral: Estructural, Monetaria y Scripts.
    """

    @staticmethod
    def verify_integrity(transaction: Transaction) -> bool:
        """Verifica que el hash de la transacción sea correcto (PoW/Integridad)."""
        calc_hash = TransactionHasher.calculate(transaction)
        if calc_hash != transaction.tx_hash:
            logger.warning(f"Integridad fallida: Calc {calc_hash} != {transaction.tx_hash}")
            return False
        return True

    @staticmethod
    def validate_monetary_balance(transaction: Transaction, total_input_albas: int) -> bool:
        """Verifica Inputs >= Outputs + Fee (No inflación)."""
        total_output = transaction.total_output_albas
        total_cost = total_output + transaction.fee

        if total_cost <= 0:
            logger.error("Costo total inválido (<= 0).")
            return False

        if total_input_albas < total_cost:
            logger.error(f"Fondos insuficientes: In {total_input_albas} < Cost {total_cost}")
            return False
        return True

    @staticmethod
    def verify_scripts(transaction: Transaction, previous_outputs: Dict[int, bytes]) -> bool:
        """
        Ejecuta la Stack Machine para cada entrada.
        Args:
            previous_outputs: {input_index: script_pubkey_bytes} (El candado del UTXO a gastar)
        """
        engine = ScriptEngine()
        
        for i, inp in enumerate(transaction.inputs):
            # Obtener el 'candado' (ScriptPubKey) del UTXO referenciado
            script_pubkey = previous_outputs.get(i)
            
            if not script_pubkey:
                logger.error(f"Input {i}: No se encontró el UTXO o ScriptPubKey.")
                return False

            # Ejecutar Desbloqueo + Bloqueo
            success = engine.execute(
                script_sig=inp.script_sig,
                script_pubkey=script_pubkey,
                transaction=transaction,
                tx_input_index=i
            )
            
            if not success:
                logger.warning(f"Input {i}: Falló ejecución del Script.")
                return False
                
        return True