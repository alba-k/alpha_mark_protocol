# akm/tests/unit/test_transaction_hashing.py
'''
Test Suite para Hashing y Validación de Transacciones:
    Verifica que la "Máquina Bruta" (CryptoUtility) funcione correctamente,
    que el Hasher sea determinista y que el Validador detecte manipulaciones.

    Functions::
        test_crypto_utility_double_sha256_is_correct():
            Verifica la corrección matemática del Doble SHA-256.
        test_transaction_hasher_is_deterministic():
            Verifica que el hasher produzca siempre el mismo ID para los mismos datos.
        test_transaction_validator_verify_integrity_passes():
            Verifica que una transacción válida pase la prueba de integridad.
        test_transaction_validator_verify_integrity_fails_if_data_altered():
            Verifica que cualquier cambio en los datos invalide el hash.
'''

import json
import hashlib
import sys
import os
from typing import Dict, Any

# --- AJUSTE DE RUTA PARA EJECUCIÓN DIRECTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '../../..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Importaion de arquitectura
from akm.core.models.transaction import Transaction 
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput

# Servicios de Hashing
from akm.core.utils.crypto_utility import CryptoUtility
from akm.core.services.transaction_hasher import TransactionHasher
from akm.core.validators.transaction_validator import TransactionValidator

# --- CONFIGURACIÓN DE DATOS DETERMINISTAS (SETUP) ---
TEST_OUTPUT = TxOutput(value_alba=1500, script_pubkey="1A_TEST_RECEPTOR_PUBLIC_KEY")
TEST_INPUT = TxInput(previous_tx_hash="00000000000000000000000000000000",
                     output_index=0,
                     script_sig="TEST_SIGNATURE_FOR_SPEND")

CANONICAL_PAYLOAD_DICT: Dict[str, Any] = {
    "inputs": [TEST_INPUT.to_dict()],
    "outputs": [TEST_OUTPUT.to_dict()],
    "timestamp": 1678886400.0, # Timestamp fijo para determinismo
    "fee": 10
}

def test_crypto_utility_double_sha256_is_correct():
    """
    Verifica que la función central de Doble SHA-256 (que evita la duplicación de código)
    produzca el resultado correcto para una entrada de prueba conocida.
    """
    test_data = "alpha_mark_protocol_test"
    
    first_hash_bytes = hashlib.sha256(test_data.encode('utf-8')).digest()
    expected_hash = hashlib.sha256(first_hash_bytes).hexdigest()

    calculated_hash = CryptoUtility.double_sha256(test_data)
    
    assert calculated_hash == expected_hash

def test_transaction_hasher_is_deterministic():

    serialized_payload = json.dumps(CANONICAL_PAYLOAD_DICT, sort_keys=True)
    expected_tx_hash = CryptoUtility.double_sha256(serialized_payload)
    
    tx_to_hash = Transaction(tx_hash="DUMMY_ID",
                             timestamp=1678886400,
                             inputs=[TEST_INPUT],
                             outputs=[TEST_OUTPUT],
                             fee=10)
    
    calculated_hash = TransactionHasher.calculate(tx_to_hash)
    
    assert calculated_hash == expected_tx_hash
    assert len(calculated_hash) == 64 

def test_transaction_validator_verify_integrity_passes():

    serialized_payload = json.dumps(CANONICAL_PAYLOAD_DICT, sort_keys=True)
    correct_hash = CryptoUtility.double_sha256(serialized_payload)
    
    tx_valid = Transaction(tx_hash=correct_hash,
                           timestamp=1678886400,
                           inputs=[TEST_INPUT],
                           outputs=[TEST_OUTPUT],
                           fee=10)
    
    assert TransactionValidator.verify_integrity(tx_valid) is True

def test_transaction_validator_verify_integrity_fails_if_data_altered():
    serialized_payload = json.dumps(CANONICAL_PAYLOAD_DICT, sort_keys=True)
    correct_hash = CryptoUtility.double_sha256(serialized_payload)
    
    tx_altered = Transaction(tx_hash=correct_hash,
                             timestamp=1678886400,
                             inputs=[TEST_INPUT],
                             outputs=[TEST_OUTPUT],
                             fee=9999)
    
    assert TransactionValidator.verify_integrity(tx_altered) is False

if __name__ == "__main__":
    print("==========================================")
    print("   EJECUTANDO TESTS DE HASHING (MANUAL)   ")
    print("==========================================\n")

    try:
        print(">> test_crypto_utility_double_sha256_is_correct...")
        test_crypto_utility_double_sha256_is_correct()
        print("[SUCCESS]\n")

        print(">> test_transaction_hasher_is_deterministic...")
        test_transaction_hasher_is_deterministic()
        print("[SUCCESS]\n")

        print(">> test_transaction_validator_verify_integrity_passes...")
        test_transaction_validator_verify_integrity_passes()
        print("[SUCCESS]\n")

        print(">> test_transaction_validator_verify_integrity_fails_if_data_altered...")
        test_transaction_validator_verify_integrity_fails_if_data_altered()
        print("[SUCCESS]\n")

        print("==========================================")
        print("   TODOS LOS TESTS PASARON EXITOSAMENTE   ")
        print("==========================================")

    except AssertionError as e:
        print(f"\nFALLO DE ASERCIÓN: El test no cumplió la condición esperada.\n{e}")
    except Exception as e:
        print(f"\nERROR INESPERADO: {e}")