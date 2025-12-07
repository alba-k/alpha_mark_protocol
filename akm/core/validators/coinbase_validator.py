# akm/core/validators/coinbase_validator.py
'''
class CoinbaseValidator:
    Especialista en la validación de la transacción especial (Coinbase)
    que paga la recompensa al minero.
'''
import logging
from akm.core.models.transaction import Transaction
from akm.core.config.consensus_config import ConsensusConfig 
# ⚡ Importamos el nuevo calculador
from akm.core.consensus.subsidy_calculator import SubsidyCalculator 

class CoinbaseValidator:

    def __init__(self):
        self.consensus_config = ConsensusConfig()
        # ⚡ Inicializamos el calculador
        self.subsidy_calculator = SubsidyCalculator(self.consensus_config)

    def validate_coinbase_transaction(
        self, 
        tx: Transaction, 
        block_height: int, 
        block_fees: int
    ) -> bool:
        """
        Valida que la transacción Coinbase sea bien formada y tenga la recompensa correcta.
        
        Args:
            tx: La transacción Coinbase.
            block_height: La altura del bloque donde se incluye la TX.
            block_fees: La suma total de comisiones (fees) de todas las TX del bloque (en Albas).
            
        Returns:
            bool: True si es válida, False en caso contrario.
        """
        
        # 1. Validación Estructural básica (Sin cambios)
        if not tx.is_coinbase:
            logging.error("CoinbaseValidator: La transacción no está marcada como Coinbase.")
            return False

        if len(tx.outputs) != 1:
            logging.error("CoinbaseValidator: Coinbase debe tener exactamente una salida (Output).")
            return False
            
        if tx.fee != 0:
            logging.error("CoinbaseValidator: El campo 'fee' de Coinbase debe ser cero.")
            return False

        # 2. Obtener la Recompensa Esperada (en ALBAS)
        # ⚡ Usamos el SubsidyCalculator para obtener el subsidio base (entero)
        base_subsidy_albas: int = self.subsidy_calculator.get_subsidy(block_height)
        
        # Recompensa TOTAL: Subsidio base + Comisiones acumuladas. (Ambos son enteros ALBAS)
        expected_reward_albas: int = base_subsidy_albas + block_fees
        
        # 3. Obtener la Recompensa Real (en ALBAS)
        actual_reward_albas: int = tx.outputs[0].value_alba

        # 4. Validación Monetaria (¡Solo enteros!)
        if actual_reward_albas > expected_reward_albas:
            logging.error(
                f"CoinbaseValidator: Recompensa excesiva. Actual: {actual_reward_albas} Albas. "
                f"Esperada: {expected_reward_albas} Albas."
            )
            return False

        # El protocolo Alpha Mark exige que el minero no tome más que la recompensa total.
        # Si actual_reward_albas es menor, se considera una donación implícita.
        
        logging.info(f"CoinbaseValidator: Transacción Coinbase para bloque {block_height} es válida.")
        return True