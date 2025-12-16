# akm/core/validators/block_rules_validator.py
import logging
from typing import Set  # <--- [FIX 1] Importante para el tipado

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
            # 1. Validaciones Estructurales y PoW
            if not BlockValidator.validate_structure(block): 
                return False
            if not BlockValidator.validate_pow(block): 
                return False

            if not block.transactions:
                logger.info(f"Bloque {block.hash[:8]} rechazado: Vacío.")
                return False

            # 2. Inicialización de contadores
            coinbase_tx = block.transactions[0]
            total_fees = 0
            
            # [FIX 2] Conjunto TIPADO para rastrear inputs gastados en ESTE bloque.
            # Esto evita que la TX #2 gaste el mismo UTXO que la TX #1.
            spent_in_this_block: Set[str] = set()

            # 3. Iterar transacciones (saltando la Coinbase)
            for i in range(1, len(block.transactions)):
                tx = block.transactions[i]
                
                # A. Validación Individual (Firmas y UTXO existente en DB)
                if not self._tx_rules_validator.validate(tx):
                    logger.info(f"Bloque {block.hash[:8]} rechazado: TX {tx.tx_hash[:8]} inválida.")
                    return False
                
                # B. Validación de Doble Gasto INTERNO (Critical Security Fix)
                for inp in tx.inputs:
                    # Creamos una clave única para el UTXO: "hash_tx_previa:indice"
                    utxo_key = f"{inp.previous_tx_hash}:{inp.output_index}"
                    
                    if utxo_key in spent_in_this_block:
                        logger.warning(f"⛔ DOBLE GASTO DETECTADO en bloque {block.index}: UTXO {utxo_key} usado dos veces.")
                        return False
                    
                    # [FIX 3] Ahora 'add' sabe que recibe un str gracias al tipado de arriba
                    spent_in_this_block.add(utxo_key)
                
                total_fees += tx.fee

            # 4. Validar Coinbase (Recompensa + Fees)
            block_height = block.index 
            if not self._coinbase_validator.validate_coinbase_transaction(
                tx=coinbase_tx,
                block_height=block_height,
                block_fees=total_fees
            ):
                logger.info(f"Bloque {block.hash[:8]} rechazado: Coinbase inválida.")
                return False

            logger.info(f"✅ Bloque {block.index} ({block.hash[:8]}) verificado exitosamente.")
            return True

        except Exception as e:
            logger.exception(f"🐛 Bug crítico validando Bloque {block.index}: {e}")
            return False