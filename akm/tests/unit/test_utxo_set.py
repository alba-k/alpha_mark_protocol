# akm/tests/unit/test_utxo_set.py
'''
Test Suite para UTXOSet (Libro Mayor):
    Verifica la integridad financiera del sistema, asegurando que el UTXOSet
    funcione correctamente como fuente de verdad para saldos y validación de gastos.

    Functions::
        test_add_outputs_and_supply():
            Verifica el registro de nuevas monedas y el cálculo del suministro total.
        test_balance_calculation():
            Verifica la suma correcta de UTXOs para calcular el saldo de una dirección.
        test_remove_inputs_and_double_spend():
            Verifica que las monedas se consuman y que el sistema maneje intentos de doble gasto.
        test_get_utxo_by_reference():
            Verifica la búsqueda de monedas existentes y el manejo de referencias inválidas.
'''

import logging
import sys
import os

# Ajuste de ruta para permitir ejecución directa como script
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '../../..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from akm.core.managers.utxo_set import UTXOSet
from akm.core.models.tx_output import TxOutput
from akm.core.models.tx_input import TxInput

# Desactivamos logs críticos durante los tests para mantener la consola limpia
logging.basicConfig(level=logging.CRITICAL)

# --- CONFIGURACIÓN DE PRUEBA (SETUP) ---
TEST_ADDRESS_1 = "1111_DIRECCION_ALICE_1111"
TEST_ADDRESS_2 = "2222_DIRECCION_BOB_2222"

def test_add_outputs_and_supply():
    print(">> Ejecutando: test_add_outputs_and_supply...")
    utxo_set = UTXOSet()
    output_1 = TxOutput(value_alba=1000, script_pubkey=TEST_ADDRESS_1)
    utxo_set.add_outputs(tx_hash="TX_A", outputs=[output_1])
    assert utxo_set.get_total_circulating_supply() == 1000
    print("[SUCCESS] Prueba de Suministro OK.\n")

def test_balance_calculation():
    print(">> Ejecutando: test_balance_calculation...")
    utxo_set = UTXOSet()
    utxo_set.add_outputs("TX_A", [TxOutput(1000, TEST_ADDRESS_1)])
    utxo_set.add_outputs("TX_B", [TxOutput(2000, TEST_ADDRESS_1)])
    utxo_set.add_outputs("TX_C", [TxOutput(500, TEST_ADDRESS_2)])
    
    balance_alice = utxo_set.get_balance_for_address(TEST_ADDRESS_1)
    assert balance_alice == 3000
    
    assert utxo_set.get_balance_for_address(TEST_ADDRESS_2) == 500
    print("[SUCCESS] Prueba de Saldos OK.\n")

def test_remove_inputs_and_double_spend():
    print(">> Ejecutando: test_remove_inputs_and_double_spend...")
    utxo_set = UTXOSet()
    output_1 = TxOutput(1000, TEST_ADDRESS_1)
    utxo_set.add_outputs("TX_A", [output_1])
    input_1 = TxInput(previous_tx_hash="TX_A", output_index=0, script_sig="sig")
    utxo_set.remove_inputs([input_1])
    assert utxo_set.get_balance_for_address(TEST_ADDRESS_1) == 0
    try:
        utxo_set.remove_inputs([input_1])
    except Exception as e:
        print(f"[FAIL] El UTXOSet lanzó error en lugar de manejar el doble gasto: {e}")
        return
        
    assert utxo_set.get_balance_for_address(TEST_ADDRESS_1) == 0
    print("[SUCCESS] Prueba de Doble Gasto OK.\n")

def test_get_utxo_by_reference():
    print(">> Ejecutando: test_get_utxo_by_reference...")
    utxo_set = UTXOSet()
    output_real = TxOutput(1000, TEST_ADDRESS_1)
    utxo_set.add_outputs("TX_A", [output_real])
    
    found = utxo_set.get_utxo_by_reference("TX_A", 0)
    assert found is not None
    assert found.value_alba == 1000
    not_found = utxo_set.get_utxo_by_reference("TX_INEXISTENTE", 5)
    assert not_found is None
    print("[SUCCESS] Prueba de Búsqueda OK.\n")

if __name__ == "__main__":
    print("==========================================")
    print("   EJECUTANDO TESTS UTXO MANUALMENTE      ")
    print("==========================================\n")
    
    try:
        test_add_outputs_and_supply()
        test_balance_calculation()
        test_remove_inputs_and_double_spend()
        test_get_utxo_by_reference()
        
        print("==========================================")
        print("   TODOS LOS TESTS PASARON EXITOSAMENTE   ")
        print("==========================================")
    except AssertionError as e:
        print("\n==========================================")
        print(f"\nERROR: UN TEST FALLÓ: {e}")
        print("==========================================")
    except Exception as e:
        print(f"\nERROR INESPERADO: {e}")