# akm/tests/unit/test_validators_specialists.py
'''
Test Suite para Validadores Especializados:
    Verifica CoinbaseValidator y TransactionRulesValidator.
'''

import sys
import os
from unittest.mock import patch # Herramienta vital para simular validaciones externas

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput
from akm.core.managers.utxo_set import UTXOSet
from akm.core.factories.transaction_factory import TransactionFactory

# Validadores
from akm.core.validators.coinbase_validator import CoinbaseValidator
from akm.core.validators.transaction_rules_validator import TransactionRulesValidator

# Mocks
from akm.tests.mocks.mock_signer import MockSigner

def test_coinbase_validator_rules():
    print(">> Ejecutando: test_coinbase_validator_rules...")
    
    # 1. Caso Feliz
    tx_ok = TransactionFactory.create_coinbase("MINER_1", 100, 50)
    assert CoinbaseValidator.validate_structure(tx_ok) is True
    assert CoinbaseValidator.validate_emission_rules(tx_ok, expected_reward=50) is True
    
    # 2. Caso Inflación (Miner intenta pagarse más)
    tx_greedy = TransactionFactory.create_coinbase("MINER_1", 100, 1000000)
    assert CoinbaseValidator.validate_emission_rules(tx_greedy, expected_reward=50) is False
    
    print("[SUCCESS] Reglas de Coinbase verificadas.\n")

def test_transaction_rules_double_spend_and_balance():
    print(">> Ejecutando: test_transaction_rules_double_spend_and_balance...")
    
    # SETUP: Crear un UTXO Set con fondos iniciales
    utxo_set = UTXOSet()
    
    # Alice tiene 100 monedas en el sistema (UTXO simulado)
    # Nota: Usamos un hash falso para el prev_hash, debe ser hex válido para evitar errores de unhexlify si se usara
    # pero aquí usaremos el patch, así que strings simples están bien.
    tx_prev_hash = "cafebabe" * 8 
    utxo_alice = TxOutput(value_alba=100, script_pubkey=MockSigner.MOCK_PUBLIC_KEY)
    utxo_set.add_outputs(tx_prev_hash, [utxo_alice])
    
    validator = TransactionRulesValidator(utxo_set)
    
    # Construcción de Transacciones
    inp = TxInput(tx_prev_hash, 0, MockSigner.MOCK_SIGNATURE)
    out1 = TxOutput(40, "BOB_ADDR")
    out2 = TxOutput(60, MockSigner.MOCK_PUBLIC_KEY) # Cambio
    
    tx_valid = TransactionFactory.create_signed([inp], [out1, out2])
    
    # Alice intenta gastar 200 teniendo solo 100
    out_huge = TxOutput(200, "BOB_ADDR")
    tx_invalid_balance = TransactionFactory.create_signed([inp], [out_huge])

    # --- SIMULACIÓN (MOCK) ---
    # Interceptamos la llamada a 'verify_signature' dentro de 'TransactionRulesValidator'.
    # Le decimos: "No ejecutes la criptografía real (que fallaría con datos falsos), simplemente retorna True".
    with patch('akm.core.validators.transaction_validator.TransactionValidator.verify_signature', return_value=True):
        
        # --- ESCENARIO 1: Gasto Válido ---
        is_valid = validator.validate(tx_valid)
        assert is_valid is True
        print("   -> Gasto válido aprobado.")

        # --- ESCENARIO 2: Gasto Excesivo (Crear dinero) ---
        is_valid_balance = validator.validate(tx_invalid_balance)
        assert is_valid_balance is False
        print("   -> Gasto excesivo rechazado.")

        # --- ESCENARIO 3: Doble Gasto (UTXO inexistente) ---
        # Simulamos que el UTXO ya fue borrado (gastado)
        utxo_set.remove_inputs([inp]) 
        
        is_double_spend = validator.validate(tx_valid)
        assert is_double_spend is False
        print("   -> Doble gasto (UTXO no encontrado) rechazado.")
    
    print("[SUCCESS] Reglas Financieras verificadas.\n")

if __name__ == "__main__":
    print("==========================================")
    print("   TESTING VALIDATORS SPECIALISTS         ")
    print("==========================================\n")
    try:
        test_coinbase_validator_rules()
        test_transaction_rules_double_spend_and_balance()
        print("\nTODOS LOS TESTS PASARON EXITOSAMENTE")
    except Exception as e:
        print(f"\nERROR: {e}")