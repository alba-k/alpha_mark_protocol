# akm/core/validators/block_rules_validator.py
import logging

# Dependencias de Estado y Modelos
from akm.core.models.block import Block
from akm.core.managers.utxo_set import UTXOSet

# Especialistas
from akm.core.validators.block_validator import BlockValidator
from akm.core.validators.coinbase_validator import CoinbaseValidator
from akm.core.validators.transaction_rules_validator import TransactionRulesValidator
from akm.core.consensus.difficulty_adjuster import DifficultyAdjuster

logger = logging.getLogger(__name__)

class BlockRulesValidator:

    def __init__(self, utxo_set: UTXOSet):
        self._utxo_set = utxo_set
        self._tx_rules_validator = TransactionRulesValidator(utxo_set)
        self._coinbase_validator = CoinbaseValidator() 
        self._difficulty_adjuster = DifficultyAdjuster()

    def validate(self, block: Block) -> bool:
            try:
                if not BlockValidator.validate_structure(block): 
                    return False
                if not BlockValidator.validate_pow(block): 
                    return False

                if not block.transactions:
                    logger.info(f"Bloque {block.hash[:]} rechazado: Vacío.")
                    return False

                coinbase_tx = block.transactions[0]
                total_fees = 0
                
                for i in range(1, len(block.transactions)):
                    tx = block.transactions[i]
                    
                    if not self._tx_rules_validator.validate(tx):
                        logger.info(f"Bloque {block.hash[:]} rechazado: TX {tx.tx_hash[:]} inválida.")
                        return False
                    
                    total_fees += tx.fee

                block_height = block.index 
                if not self._coinbase_validator.validate_coinbase_transaction(
                    tx=coinbase_tx,
                    block_height=block_height,
                    block_fees=total_fees
                ):
                    logger.info(f"Bloque {block.hash[:]} rechazado: Coinbase inválida.")
                    return False

                logger.info(f"Bloque {block.hash[:]} verificado.")
                return True

            except Exception:
                logger.exception(f"Bug detectado durante validación de Bloque {block.index}")
                return False