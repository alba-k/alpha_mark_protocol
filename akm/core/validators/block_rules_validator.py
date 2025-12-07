# akm/core/validators/block_rules_validator.py
'''
class BlockRulesValidator:
    Especialista Integral que orquesta todas las validaciones de un bloque.
    Actúa como fachada única para el ConsensusManager, integrando reglas
    estructurales, de consenso (PoW) y financieras (UTXO).

    Methods::
        validate(block) -> bool:
            Ejecuta la secuencia completa de validación. Retorna True si el bloque es válido.
'''

import logging

# Dependencias de Estado y Modelos
from akm.core.models.block import Block
from akm.core.managers.utxo_set import UTXOSet

# Especialistas Específicos
from akm.core.validators.block_validator import BlockValidator
from akm.core.validators.coinbase_validator import CoinbaseValidator
from akm.core.validators.transaction_rules_validator import TransactionRulesValidator

# IMPORTANTE: Importamos el ajustador para consultar la política monetaria (Halving)
from akm.core.consensus.difficulty_adjuster import DifficultyAdjuster
# ⚡ Nota: Ya no necesitamos difficulty_adjuster para el subsidio, usaremos CoinbaseValidator instanciado.

logging.basicConfig(level=logging.INFO, format='[BlockRules] %(message)s')

class BlockRulesValidator:

    def __init__(self, utxo_set: UTXOSet):
        # Inyectamos el UTXO Set para validar reglas financieras (doble gasto)
        self._utxo_set = utxo_set
        
        # Instanciamos los colaboradores
        self._tx_rules_validator = TransactionRulesValidator(utxo_set)
        
        # ⚡ CORRECCIÓN: Instanciamos el validador de Coinbase
        self._coinbase_validator = CoinbaseValidator() 
        
        # Instanciamos DifficultyAdjuster para calcular subsidios dinámicos (OCP Compliance)
        self._difficulty_adjuster = DifficultyAdjuster()

    def validate(self, block: Block) -> bool:
        
        # 1. Validación Estructural y Proof-of-Work
        if not BlockValidator.validate_structure(block):
            return False

        if not BlockValidator.validate_pow(block):
            return False

        # 2. Validación de Contenido Base
        if not block.transactions:
            logging.error(f"Bloque {block.hash[:8]} RECHAZADO: Lista de transacciones vacía.")
            return False

        # 3. Validación de Transacciones Estándar y Cálculo de Comisiones (Fees)
        coinbase_tx = block.transactions[0]
        total_fees = 0
        
        for i in range(1, len(block.transactions)):
            tx = block.transactions[i]
            
            if not self._tx_rules_validator.validate(tx):
                logging.error(f"Bloque {block.hash[:8]} RECHAZADO: Transacción inválida detectada ({tx.tx_hash[:8]}).")
                return False
            
            # ⚡ El fee es un entero (Albas)
            total_fees += tx.fee

        # 4. Validación COMPLETA de Coinbase (Estructura y Emisión)
        # La altura del bloque es el índice (index)
        block_height = block.index 
        
        # ⚡ CORRECCIÓN CRÍTICA: Reemplazamos las dos llamadas obsoletas por una sola
        if not self._coinbase_validator.validate_coinbase_transaction(
            tx=coinbase_tx,
            block_height=block_height,
            block_fees=total_fees # Total de comisiones acumuladas (Albas)
        ):
            logging.error(f"Bloque {block.hash[:8]} RECHAZADO: Error en la transacción Coinbase (Emisión o Estructura).")
            return False

        # 5. Validación final de la Merkle Root y otros (Si aplican)
        # (Se asume que estas validaciones están en BlockValidator o se omiten por brevedad)

        # ¡Bloque válido!
        logging.info(f"Bloque {block.hash[:8]} ACEPTADO.")
        return True