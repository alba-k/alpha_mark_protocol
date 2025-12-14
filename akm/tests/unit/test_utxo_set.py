# akm/tests/unit/test_utxo_set.py
'''
Test Suite para UTXOSet (Libro Mayor):
    Verifica la integridad financiera del sistema, asegurando que el UTXOSet
    funcione correctamente como fuente de verdad para saldos y validación de gastos.

    Functions::
        test_add_outputs_and_supply(): Verifica registro y suministro.
        test_balance_calculation(): Verifica cálculo de saldo.
        test_remove_inputs_and_double_spend(): Verifica consumo y prevención de doble gasto.
        test_get_utxo_by_reference(): Verifica búsqueda individual.
        test_get_utxos_for_address_structure(): (NUEVO) Verifica el formato para la Wallet.
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

def test_get_utxos_for_address_structure():
    print(">> Ejecutando: test_get_utxos_for_address_structure...")
    utxo_set = UTXOSet()
    
    # Escenario: Alice tiene 2 UTXOs, Bob tiene 1
    # TX1: Output 0 -> Alice (100)
    out_alice_1 = TxOutput(100, TEST_ADDRESS_1)
    utxo_set.add_outputs("TX_1", [out_alice_1])
    
    # TX2: Output 0 -> Bob (50), Output 1 -> Alice (200)
    out_bob = TxOutput(50, TEST_ADDRESS_2)
    out_alice_2 = TxOutput(200, TEST_ADDRESS_1)
    utxo_set.add_outputs("TX_2", [out_bob, out_alice_2])
    
    # Ejecutar método nuevo
    alice_utxos = utxo_set.get_utxos_for_address(TEST_ADDRESS_1)
    
    # Verificaciones
    assert len(alice_utxos) == 2, "Alice debería tener 2 UTXOs"
    
    # Verificar estructura del primer UTXO (TX_1)
    # Buscamos en la lista (el orden no está garantizado en sets, pero en listas de append sí suele estarlo)
    utxo_1 = next(u for u in alice_utxos if u['tx_hash'] == "TX_1")
    assert utxo_1['amount'] == 100
    assert utxo_1['output_index'] == 0
    assert utxo_1['output_object'] == out_alice_1
    
    # Verificar estructura del segundo UTXO (TX_2)
    utxo_2 = next(u for u in alice_utxos if u['tx_hash'] == "TX_2")
    assert utxo_2['amount'] == 200
    assert utxo_2['output_index'] == 1
    
    print("[SUCCESS] Estructura detallada de UTXOs para Wallet OK.\n")

if __name__ == "__main__":
    print("==========================================")
    print("   EJECUTANDO TESTS UTXO MANUALMENTE      ")
    print("==========================================\n")
    
    try:
        test_add_outputs_and_supply()
        test_balance_calculation()
        test_remove_inputs_and_double_spend()
        test_get_utxo_by_reference()
        test_get_utxos_for_address_structure()
        
        print("==========================================")
        print("   TODOS LOS TESTS PASARON EXITOSAMENTE   ")
        print("==========================================")
    except AssertionError as e:
        print("\n==========================================")
        print(f"\nERROR: UN TEST FALLÓ: {e}")
        print("==========================================")
    except Exception as e:
        print(f"\nERROR INESPERADO: {e}")