# akm/core/validators/coinbase_validator.py

import logging

# Dependencias del Proyecto
from akm.core.models.transaction import Transaction
from akm.core.config.consensus_config import ConsensusConfig 
from akm.core.consensus.subsidy_calculator import SubsidyCalculator

logger = logging.getLogger(__name__)

class CoinbaseValidator:

    def __init__(self):
        self._consensus_config = ConsensusConfig()
        self._subsidy_calculator = SubsidyCalculator(self._consensus_config)

    def validate_coinbase_transaction(
        self, 
        tx: Transaction, 
        block_height: int, 
        block_fees: int
    ) -> bool:
        try:
            if not tx.is_coinbase:
                logger.info(f"Rechazo Coinbase: No marcada como coinbase en bloque {block_height}.")
                return False

            if len(tx.outputs) != 1:
                logger.info(f"Rechazo Coinbase: Múltiples salidas detectadas.")
                return False
                
            if tx.fee != 0:
                logger.info(f"Rechazo Coinbase: Campo 'fee' no es cero.")
                return False

            base_subsidy: int = self._subsidy_calculator.get_subsidy(block_height)
            expected_total: int = base_subsidy + block_fees
            actual_total: int = tx.outputs[0].value_alba

            if actual_total > expected_total:
                logger.info(
                    f"Rechazo Coinbase: Recompensa excesiva. "
                    f"Actual: {actual_total} > Máxima: {expected_total}"
                )
                return False
            
            logger.info(f"Coinbase bloque {block_height} verificada.")
            return True

        except Exception:
            logger.exception(f"Bug en validación de Coinbase para bloque {block_height}")
            return False