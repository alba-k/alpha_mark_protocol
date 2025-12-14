# akm/tests/unit/test_merkle_tree.py
'''
Test Suite para MerkleTreeBuilder:
    Verifica la correcta construcción del Árbol de Merkle y el cálculo de la Raíz.
    
    Functions::
        test_build_empty_list(): Verifica lista vacía.
        test_build_single_transaction(): Verifica raíz directa.
        test_build_even_transactions(): Verifica pares.
        test_build_odd_transactions(): Verifica duplicación impar.
'''

import sys
import os

# Ajuste de ruta para ejecución directa
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '../../..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from akm.core.services.merkle_tree_builder import MerkleTreeBuilder
from akm.core.utils.crypto_utility import CryptoUtility

def test_build_empty_list():
    print(">> Ejecutando: test_build_empty_list...")
    
    root = MerkleTreeBuilder.build([])
    
    # Usamos tu método de test específico
    expected = CryptoUtility.double_sha256("")
    
    assert root == expected
    print("[SUCCESS] Lista vacía manejada correctamente.\n")

def test_build_single_transaction():
    print(">> Ejecutando: test_build_single_transaction...")
    
    tx_hash = "aaaa" * 16 # 64 chars
    
    root = MerkleTreeBuilder.build([tx_hash])
    
    assert root == tx_hash
    print("[SUCCESS] Raíz única verificada.\n")

def test_build_even_transactions():
    print(">> Ejecutando: test_build_even_transactions...")
    
    tx1 = "aaaa" * 16
    tx2 = "bbbb" * 16
    
    root = MerkleTreeBuilder.build([tx1, tx2])
    
    combined = tx1 + tx2
    # Usamos tu método de test
    expected = CryptoUtility.double_sha256(combined)
    
    assert root == expected
    print("[SUCCESS] Árbol par verificado.\n")

def test_build_odd_transactions():
    print(">> Ejecutando: test_build_odd_transactions...")
    
    tx1 = "1111" * 16
    tx2 = "2222" * 16
    tx3 = "3333" * 16
    
    root = MerkleTreeBuilder.build([tx1, tx2, tx3])

    # Verificación usando tus métodos de test para replicar la lógica
    h12 = CryptoUtility.double_sha256(tx1 + tx2)
    h33 = CryptoUtility.double_sha256(tx3 + tx3)
    expected_root = CryptoUtility.double_sha256(h12 + h33)
    
    assert root == expected_root
    print("[SUCCESS] Árbol impar (duplicación) verificado.\n")

if __name__ == "__main__":
    print("==========================================")
    print("   EJECUTANDO TESTS MERKLE TREE (MANUAL)  ")
    print("==========================================\n")

    try:
        test_build_empty_list()
        test_build_single_transaction()
        test_build_even_transactions()
        test_build_odd_transactions()

        print("==========================================")
        print("   TODOS LOS TESTS PASARON EXITOSAMENTE   ")
        print("==========================================")
    except AssertionError as e:
        print(f"\nNFALLO DE ASERCIÓN: {e}")
    except Exception as e:
        print(f"\nERROR INESPERADO: {e}")