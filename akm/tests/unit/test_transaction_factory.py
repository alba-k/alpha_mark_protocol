# akm/tests/unit/test_transaction_factory.py
'''
Test Suite para TransactionFactory y Transaction Model:
    Verifica la correcta fabricación de objetos Transaction y la lógica de Coinbase.

    Functions::
        test_create_coinbase(): Verifica la estructura de la tx de recompensa.
        test_create_signed_standard_tx(): Verifica una tx normal de pago (Fee implícito 0).
        test_create_transaction_with_fee(): (NUEVO) Verifica que el factory asigne correctamente la comisión.
'''

import sys
import os

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '../../..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from akm.core.factories.transaction_factory import TransactionFactory
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput

def test_create_coinbase():
    print(">> Ejecutando: test_create_coinbase...")
    
    miner_address_hash = "MINER_WALLET_ADDRESS_123"
    block_height = 100
    reward = 5000
    
    coinbase_tx = TransactionFactory.create_coinbase(
        miner_pubkey_hash=miner_address_hash,
        block_height=block_height,
        total_reward=reward
    )
    
    assert len(coinbase_tx.inputs) == 0
    assert len(coinbase_tx.outputs) == 1
    assert coinbase_tx.outputs[0].value_alba == reward
    assert coinbase_tx.outputs[0].script_pubkey == miner_address_hash
    assert coinbase_tx.is_coinbase is True
    assert coinbase_tx.fee == 0 # Coinbase no tiene fee
    
    print("[SUCCESS] Coinbase creada correctamente.\n")

def test_create_signed_standard_tx():
    print(">> Ejecutando: test_create_signed_standard_tx...")
    
    # Inputs simulados (ya firmados)
    inp = TxInput(previous_tx_hash="prev_hash_abc", output_index=0, script_sig="sig_123")
    
    # Outputs simulados
    out = TxOutput(value_alba=50, script_pubkey="RECIPIENT_ADDR")
    
    # 1. Crear Transacción Estándar (Sin especificar fee, default 0)
    tx = TransactionFactory.create_signed(inputs=[inp], outputs=[out])
    
    # 2. Verificaciones
    assert tx.tx_hash is not None
    assert len(tx.tx_hash) == 64  # Hex string válido
    assert len(tx.inputs) == 1
    assert tx.is_coinbase is False
    assert tx.fee == 0 # Verificación del default
    
    print("[SUCCESS] Transacción Estándar (Default Fee) creada correctamente.\n")

def test_create_transaction_with_fee():
    print(">> Ejecutando: test_create_transaction_with_fee...")
    
    inp = TxInput(previous_tx_hash="hash_x", output_index=0, script_sig="sig")
    out = TxOutput(value_alba=10, script_pubkey="ADDR")
    
    # 1. Crear con Fee explícito
    expected_fee = 5
    tx = TransactionFactory.create_signed(inputs=[inp], outputs=[out], fee=expected_fee)
    
    # 2. Verificaciones
    assert tx.fee == expected_fee
    assert tx.is_coinbase is False
    
    print(f"[SUCCESS] Transacción con Fee ({expected_fee}) creada correctamente.\n")

if __name__ == "__main__":
    print("==========================================")
    print("   TESTING TRANSACTION FACTORY (MANUAL)   ")
    print("==========================================\n")
    
    try:
        test_create_coinbase()
        test_create_signed_standard_tx()
        test_create_transaction_with_fee()
        print("\nTODOS LOS TESTS PASARON EXITOSAMENTE")
    except AssertionError as e:
        print(f"\nFALLO DE ASERCIÓN: {e}")
    except Exception as e:
        print(f"\nERROR INESPERADO: {e}")