# akm/core/validators/transaction_rules_validator.py

import logging
from typing import Dict

# Dependencias del Proyecto
from akm.core.models.transaction import Transaction
from akm.core.managers.utxo_set import UTXOSet
from akm.core.validators.transaction_validator import TransactionValidator


logger = logging.getLogger(__name__)

class TransactionRulesValidator:

    def __init__(self, utxo_set: UTXOSet):
        self._utxo_set = utxo_set

    def validate(self, tx: Transaction) -> bool:
        if tx.is_coinbase: 
            return True

        try:
            if not TransactionValidator.verify_integrity(tx):
                logger.info(f"Rechazo TX {tx.tx_hash[:]}: Integridad fallida.")
                return False

            try:
                total_input_value, previous_scripts = self._fetch_utxo_context(tx)
            except ValueError as e:
                logger.info(f"Rechazo TX {tx.tx_hash[:]}: {e}")
                return False
            
            if not TransactionValidator.verify_scripts(tx, previous_scripts):
                logger.info(f"Rechazo TX {tx.tx_hash[:]}: Firma/Script inválido.")
                return False

            if not TransactionValidator.validate_monetary_balance(tx, total_input_value):
                return False

            logger.info(f"TX {tx.tx_hash[:]} validada.")
            return True

        except Exception:
            logger.exception(f"Bug detectado validando TX {tx.tx_hash[:8]}")
            return False

    def _fetch_utxo_context(self, tx: Transaction) -> tuple[int, Dict[int, bytes]]:
        
        total_value = 0
        previous_scripts: Dict[int, bytes] = {}

        for i, inp in enumerate(tx.inputs):
            utxo = self._utxo_set.get_utxo_by_reference(inp.previous_tx_hash, inp.output_index)
            
            if not utxo:
                raise ValueError(f"Input {i}: UTXO no encontrado o doble gasto.")

            total_value += utxo.value_alba

          
            script_data = utxo.script_pubkey
            if isinstance(script_data, str):
                script_data = script_data.encode('utf-8') # O la codificación que uses
            
            previous_scripts[i] = script_data

        return total_value, previous_scripts