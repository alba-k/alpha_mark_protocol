# akm/tests/unit/test_block_validator.py
'''
Test Suite para BlockValidator:
    Verifica que el especialista estructural detecte bloques corruptos o mal formados.

    Functions::
        test_validate_valid_block(): Un bloque perfecto debe pasar.
        test_validate_bad_hash_integrity(): Si el hash no coincide con el contenido, debe fallar.
        test_validate_bad_merkle_root(): Si la raíz Merkle es falsa, debe fallar.
        test_validate_bad_pow(): Si el hash es mayor que el target, debe fallar.
'''

import sys
import os
import time

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from akm.core.models.block import Block
from akm.core.services.block_hasher import BlockHasher
from akm.core.services.merkle_tree_builder import MerkleTreeBuilder
from akm.core.factories.transaction_factory import TransactionFactory
from akm.core.validators.block_validator import BlockValidator
from akm.core.utils.difficulty_utils import DifficultyUtils

def create_valid_block(bits: str ="207fffff") -> Block:
    """
    Helper para crear un bloque válido rápidamente.
    Usamos '207fffff' (Regtest) por defecto para minería instantánea.
    """
    
    # IMPORTANTE: Hackeamos temporalmente el MAX_TARGET para permitir dificultad trivial
    original_max = DifficultyUtils.MAX_TARGET
    DifficultyUtils.MAX_TARGET = 2**256 - 1
    
    try:
        coinbase = TransactionFactory.create_coinbase("MINER_ADDR", 1, 50)
        txs = [coinbase]
        merkle_root = MerkleTreeBuilder.build([tx.tx_hash for tx in txs])
        
        # Creamos bloque candidato
        block = Block(
            index=1,
            timestamp=int(time.time()),
            previous_hash="0000000000000000000000000000000000000000000000000000000000000000",
            bits=bits,
            merkle_root=merkle_root,
            nonce=0,
            block_hash="",
            transactions=txs
        )
        
        target = DifficultyUtils.bits_to_target(bits)
        
        # Minamos (debería ser casi instantáneo con 207fffff)
        for nonce in range(1000000):
            block._nonce = nonce # type: ignore
            h = BlockHasher.calculate(block)
            if int(h, 16) <= target:
                block._hash = h # type: ignore
                return block
                
        raise TimeoutError("No se pudo minar bloque válido en el helper de test.")
        
    finally:
        # Restauramos siempre el valor original
        DifficultyUtils.MAX_TARGET = original_max

def test_validate_valid_block():
    print(">> Ejecutando: test_validate_valid_block...")
    
    # Al no pasar argumentos, usa la dificultad trivial (207fffff)
    block = create_valid_block()
    
    # Hackeamos MAX_TARGET también aquí para que la validación acepte el bloque fácil
    original_max = DifficultyUtils.MAX_TARGET
    DifficultyUtils.MAX_TARGET = 2**256 - 1
    
    try:
        # 1. Estructura
        assert BlockValidator.validate_structure(block) is True
        # 2. PoW
        assert BlockValidator.validate_pow(block) is True
        print("[SUCCESS] Bloque válido aceptado.\n")
    finally:
        DifficultyUtils.MAX_TARGET = original_max

def test_validate_bad_hash_integrity():
    print(">> Ejecutando: test_validate_bad_hash_integrity...")
    
    block = create_valid_block()
    
    # SABOTAJE: Cambiamos el nonce pero no actualizamos el hash
    block._nonce += 1  # type: ignore
    
    # Hackeamos MAX_TARGET para que la validación de PoW no falle antes de tiempo (aunque aquí probamos estructura)
    original_max = DifficultyUtils.MAX_TARGET
    DifficultyUtils.MAX_TARGET = 2**256 - 1
    
    try:
        assert BlockValidator.validate_structure(block) is False
        print("[SUCCESS] Integridad de hash fallida detectada.\n")
    finally:
        DifficultyUtils.MAX_TARGET = original_max

def test_validate_bad_merkle_root():
    print(">> Ejecutando: test_validate_bad_merkle_root...")
    
    block = create_valid_block()
    
    # SABOTAJE: Cambiamos una transacción sin actualizar la Raíz Merkle
    fake_tx = TransactionFactory.create_coinbase("HACKER", 1, 1000)
    block._transactions[0] = fake_tx # type: ignore 
    
    original_max = DifficultyUtils.MAX_TARGET
    DifficultyUtils.MAX_TARGET = 2**256 - 1
    
    try:
        assert BlockValidator.validate_structure(block) is False
        print("[SUCCESS] Merkle Root inconsistente detectada.\n")
    finally:
        DifficultyUtils.MAX_TARGET = original_max

def test_validate_bad_pow():
    print(">> Ejecutando: test_validate_bad_pow...")
    
    # Creamos un bloque válido con dificultad fácil
    block = create_valid_block()
    
    # SABOTAJE: Aumentamos la dificultad drásticamente en el header
    # Le decimos que el target es muy difícil ("1d00ffff"), pero el hash que tiene
    # solo cumple con la dificultad fácil.
    block._bits = "1d00ffff" # type: ignore
    
    # Recalculamos el hash para que pase la validación de integridad (estructura)
    block._hash = BlockHasher.calculate(block) # type: ignore
    
    # No necesitamos hackear MAX_TARGET aquí porque '1d00ffff' es estándar
    
    # Estructura OK (Hash coincide con contenido)
    assert BlockValidator.validate_structure(block) is True
    
    # PoW FAIL (El hash no es lo suficientemente pequeño para 1d00ffff)
    assert BlockValidator.validate_pow(block) is False
    print("[SUCCESS] PoW insuficiente detectado.\n")

if __name__ == "__main__":
    print("==========================================")
    print("   TESTING BLOCK VALIDATOR (SRP)          ")
    print("==========================================\n")
    try:
        test_validate_valid_block()
        test_validate_bad_hash_integrity()
        test_validate_bad_merkle_root()
        test_validate_bad_pow()
        print("\nTODOS LOS TESTS PASARON EXITOSAMENTE")
    except Exception as e:
        print(f"\nERROR: {e}")