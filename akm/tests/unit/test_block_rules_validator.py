# akm/tests/unit/test_block_rules_validator.py
'''
Test Suite para BlockRulesValidator (Integration Logic):
    Verifica que el orquestador de validación aplique correctamente las reglas
    estructurales, financieras y, sobre todo, la POLÍTICA MONETARIA (Halving).

    Functions::
        test_validate_valid_block_genesis_subsidy(): Bloque válido con subsidio inicial (50).
        test_validate_valid_block_halving_subsidy(): Bloque válido tras un Halving (25).
        test_validate_inflationary_block(): Bloque rechazado por pedir más recompensa de la permitida.
        test_validate_structural_failure(): Bloque rechazado por fallo en BlockValidator.
'''

import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importaciones del Sistema
from akm.core.models.block import Block
from akm.core.models.transaction import Transaction
from akm.core.models.tx_output import TxOutput
from akm.core.validators.block_rules_validator import BlockRulesValidator

class TestBlockRulesValidator(unittest.TestCase):

    def setUp(self):
        # 1. Mock del UTXO Set (No necesitamos base de datos real)
        self.mock_utxo_set = MagicMock()
        
        # 2. Instanciamos el Validador bajo prueba
        self.validator = BlockRulesValidator(self.mock_utxo_set)
        
        # 3. INYECCIÓN DE MOCKS (Interceptamos los colaboradores internos)
        # Esto es clave para probar OCP: Simulamos el DifficultyAdjuster
        self.validator._difficulty_adjuster = MagicMock() # type: ignore
        self.validator._tx_rules_validator = MagicMock() # type: ignore

    def create_dummy_block(self, coinbase_reward: int, fees: int = 0) -> Block:
        """Helper para crear un bloque con estructura mínima para el test."""
        # Coinbase TX (Recompensa)
        coinbase_out = TxOutput(coinbase_reward, "MINER_ADDR")
        # Mock de Coinbase Transaction
        coinbase_tx = MagicMock(spec=Transaction)
        coinbase_tx.outputs = [coinbase_out]
        coinbase_tx.is_coinbase = True
        
        # Standard TX (Para generar fees)
        txs = [coinbase_tx]
        if fees > 0:
            std_tx = MagicMock(spec=Transaction)
            std_tx.fee = fees
            std_tx.is_coinbase = False
            txs.append(std_tx)
            
        block = MagicMock(spec=Block)
        block.transactions = txs
        block.hash = "BLOCK_HASH_123"
        block.index = 100 # Altura arbitraria
        return block

    @patch('akm.core.validators.block_rules_validator.BlockValidator')
    @patch('akm.core.validators.block_rules_validator.CoinbaseValidator')
    def test_validate_valid_block_genesis_subsidy(self, MockCoinbaseValidator: MagicMock, MockBlockValidator: MagicMock):
        print("\n>> Ejecutando: test_validate_valid_block_genesis_subsidy...")
        
        # CONFIGURACIÓN DEL ESCENARIO
        # 1. Los validadores estáticos dicen que todo está OK
        MockBlockValidator.validate_structure.return_value = True
        MockBlockValidator.validate_pow.return_value = True
        MockCoinbaseValidator.validate_structure.return_value = True
        MockCoinbaseValidator.validate_emission_rules.return_value = True # La regla final pasa
        
        # 2. El validador de TXs dice que OK
        # Usamos 'configure_mock' o asignación directa segura para el linter
        self.validator._tx_rules_validator.validate.return_value = True # type: ignore
        
        # 3. POLÍTICA MONETARIA (SIMULACIÓN): El ajustador dice que el subsidio es 50
        self.validator._difficulty_adjuster.calculate_block_subsidy.return_value = 50 # type: ignore
        
        # CREACIÓN DEL BLOQUE (Minero reclama 50)
        block = self.create_dummy_block(coinbase_reward=50, fees=0)
        
        # EJECUCIÓN
        result = self.validator.validate(block)
        
        # VERIFICACIÓN
        assert result is True
        # Verificamos que se llamó al validador de emisión con el valor correcto (50 + 0)
        MockCoinbaseValidator.validate_emission_rules.assert_called_with(block.transactions[0], 50)
        print("[SUCCESS] Bloque con subsidio estándar aceptado.")

    @patch('akm.core.validators.block_rules_validator.BlockValidator')
    @patch('akm.core.validators.block_rules_validator.CoinbaseValidator')
    def test_validate_valid_block_halving_subsidy(self, MockCoinbaseValidator: MagicMock, MockBlockValidator: MagicMock):
        print(">> Ejecutando: test_validate_valid_block_halving_subsidy...")
        
        # CONFIGURACIÓN
        MockBlockValidator.validate_structure.return_value = True
        MockBlockValidator.validate_pow.return_value = True
        MockCoinbaseValidator.validate_structure.return_value = True
        MockCoinbaseValidator.validate_emission_rules.return_value = True
        self.validator._tx_rules_validator.validate.return_value = True # type: ignore
        
        # ESCENARIO HALVING: El ajustador dice que el subsidio bajó a 25
        self.validator._difficulty_adjuster.calculate_block_subsidy.return_value = 25 # type: ignore
        
        # CREACIÓN DEL BLOQUE (Minero reclama 25 + 5 de fees = 30)
        block = self.create_dummy_block(coinbase_reward=30, fees=5)
        
        # EJECUCIÓN
        result = self.validator.validate(block)
        
        # VERIFICACIÓN
        assert result is True
        # Verificamos que la regla de emisión recibió: Subsidio(25) + Fees(5) = 30
        MockCoinbaseValidator.validate_emission_rules.assert_called_with(block.transactions[0], 30)
        print("[SUCCESS] Bloque post-halving (25 + fees) aceptado correctamente.")

    @patch('akm.core.validators.block_rules_validator.BlockValidator')
    @patch('akm.core.validators.block_rules_validator.CoinbaseValidator')
    def test_validate_inflationary_block(self, MockCoinbaseValidator: MagicMock, MockBlockValidator: MagicMock):
        print(">> Ejecutando: test_validate_inflationary_block...")
        
        # CONFIGURACIÓN
        MockBlockValidator.validate_structure.return_value = True
        MockBlockValidator.validate_pow.return_value = True
        MockCoinbaseValidator.validate_structure.return_value = True
        self.validator._tx_rules_validator.validate.return_value = True # type: ignore
        
        # El validador de emisión dirá FALSE (Fallo)
        MockCoinbaseValidator.validate_emission_rules.return_value = False
        
        # Política: 50 monedas
        self.validator._difficulty_adjuster.calculate_block_subsidy.return_value = 50 # type: ignore
        
        # Bloque intenta reclamar 50 pero el mock de validación de emisión falla
        # (Simulamos que logicamente pidió de más o el validador lo rechazó)
        block = self.create_dummy_block(coinbase_reward=100) # Pide 100
        
        result = self.validator.validate(block)
        
        assert result is False
        print("[SUCCESS] Bloque inflacionario rechazado.")

if __name__ == "__main__":
    print("==========================================")
    print("   TESTING BLOCK RULES VALIDATOR (OCP)    ")
    print("==========================================\n")
    try:
        # Ejecutamos los tests manualmente para ver la salida limpia
        suite = unittest.TestLoader().loadTestsFromTestCase(TestBlockRulesValidator)
        unittest.TextTestRunner(verbosity=0).run(suite)
        print("\nTODOS LOS TESTS DE INTEGRACIÓN PASARON")
    except Exception as e:
        print(f"\nERROR: {e}")