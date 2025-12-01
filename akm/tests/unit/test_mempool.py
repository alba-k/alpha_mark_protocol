# akm/tests/unit/   
'''
Test Suite para Mempool:
    Verifica la gestión de transacciones pendientes, la priorización por comisión
    y la limpieza post-minado.

    Functions::
        test_add_transaction_success(): Verifica la admisión básica.
        test_reject_duplicates(): Verifica la idempotencia (no duplicados).
        test_priority_by_fee(): Verifica que el minero seleccione las TXs más rentables.
        test_mempool_capacity_limit(): Verifica el rechazo cuando la memoria está llena.
        test_remove_mined_transactions(): Verifica la limpieza del pool tras confirmar un bloque.
'''

import sys
import os
import time

# --- AJUSTE DE RUTA PARA EJECUCIÓN DIRECTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '../../..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from akm.core.services.mempool import Mempool
from akm.core.models.transaction import Transaction

# --- UTILIDAD (HELPER) PARA EL TEST ---
def create_dummy_tx(tx_hash: str, fee: int) -> Transaction:
    """Crea una transacción mínima para pruebas de Mempool."""
    return Transaction(
        tx_hash=tx_hash,
        timestamp= int(time.time()),
        inputs=[],  # No relevante para test de mempool
        outputs=[], # No relevante para test de mempool
        fee=fee
    )

def test_add_transaction_success():
    print(">> Ejecutando: test_add_transaction_success...")
    
    mempool = Mempool()
    tx = create_dummy_tx("tx_001", 10)
    
    # 1. Agregar transacción válida
    accepted = mempool.add_transaction(tx)
    
    # 2. Verificar estado
    assert accepted is True
    assert mempool.get_pending_count() == 1
    print("[SUCCESS] Transacción agregada correctamente.\n")

def test_reject_duplicates():
    print(">> Ejecutando: test_reject_duplicates...")
    
    mempool = Mempool()
    tx = create_dummy_tx("tx_unique", 50)
    
    # 1. Agregar primera vez
    mempool.add_transaction(tx)
    
    # 2. Intentar agregar la misma transacción
    accepted_again = mempool.add_transaction(tx)
    
    # 3. Verificar rechazo
    assert accepted_again is False
    assert mempool.get_pending_count() == 1
    print("[SUCCESS] Duplicado rechazado correctamente.\n")

def test_priority_by_fee():
    print(">> Ejecutando: test_priority_by_fee (Fee Market)...")
    
    mempool = Mempool()
    
    # Escenario: 3 transacciones con diferentes comisiones
    # tx_low: Paga poco (10)
    # tx_high: Paga mucho (100) - Debería ser la primera
    # tx_med: Paga medio (50)
    
    tx_low = create_dummy_tx("tx_low", 10)
    tx_high = create_dummy_tx("tx_high", 100)
    tx_med = create_dummy_tx("tx_mid", 50)
    
    mempool.add_transaction(tx_low)
    mempool.add_transaction(tx_high)
    mempool.add_transaction(tx_med)
    
    # Solicitamos las mejores transacciones para el bloque
    selection = mempool.get_transactions_for_block(max_count=3)
    
    # Verificación de Orden (Debe ser Descendente por Fee)
    assert selection[0].tx_hash == "tx_high"  # 100
    assert selection[1].tx_hash == "tx_mid"   # 50
    assert selection[2].tx_hash == "tx_low"   # 10
    
    print("[SUCCESS] Priorización por mercado (Fees) verificada.\n")

def test_mempool_capacity_limit():
    print(">> Ejecutando: test_mempool_capacity_limit...")
    
    mempool = Mempool()
    
    # Simulamos un límite bajo para la prueba (Hack de caja blanca)
    # Accedemos a la configuración interna solo para este test
    mempool._config._mempool_max_size = 2 # type: ignore
    
    tx1 = create_dummy_tx("tx_1", 10)
    tx2 = create_dummy_tx("tx_2", 10)
    tx3_overflow = create_dummy_tx("tx_overflow", 10)
    
    # Llenamos el pool
    mempool.add_transaction(tx1)
    mempool.add_transaction(tx2)
    
    # Intentamos desbordar
    accepted = mempool.add_transaction(tx3_overflow)
    
    assert accepted is False
    assert mempool.get_pending_count() == 2
    print("[SUCCESS] Protección de capacidad (DDoS) verificada.\n")

def test_remove_mined_transactions():
    print(">> Ejecutando: test_remove_mined_transactions...")
    
    mempool = Mempool()
    
    tx1 = create_dummy_tx("tx_mined_1", 20)
    tx2 = create_dummy_tx("tx_pending", 20)
    
    mempool.add_transaction(tx1)
    mempool.add_transaction(tx2)
    
    # Simulamos que un bloque confirmó tx1
    block_transactions = [tx1]
    
    # Limpieza
    mempool.remove_mined_transactions(block_transactions)
    
    # Verificación: tx1 debe haber desaparecido, tx2 debe seguir ahí
    assert mempool.get_pending_count() == 1
    
    # Verificar que la que queda es tx2
    remaining = mempool.get_transactions_for_block(1)
    assert remaining[0].tx_hash == "tx_pending"
    
    print("[SUCCESS] Limpieza post-minado correcta.\n")

# --- PUNTO DE ENTRADA PARA EJECUCIÓN MANUAL ---
if __name__ == "__main__":
    print("==========================================")
    print("   EJECUTANDO TESTS MEMPOOL (MANUAL)      ")
    print("==========================================\n")

    try:
        test_add_transaction_success()
        test_reject_duplicates()
        test_priority_by_fee()
        test_mempool_capacity_limit()
        test_remove_mined_transactions()

        print("==========================================")
        print("   TODOS LOS TESTS PASARON EXITOSAMENTE   ")
        print("==========================================")
    except AssertionError as e:
        print(f"\nFALLO DE ASERCIÓN: {e}")
    except Exception as e:
        print(f"\nERROR INESPERADO: {e}")