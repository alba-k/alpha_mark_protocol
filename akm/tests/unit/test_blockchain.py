# akm/tests/unit/test_blockchain.py
'''
Test Suite para Blockchain:
    Verifica la funcionalidad del contenedor Blockchain y el ChainValidator.
    Simula un escenario de "Vida Real": Génesis -> Bloques -> Ataque Hacker.

    Functions::
        crear_bloque_simulado(index, prev_hash, transactions) -> Block:
            Helper para fabricar bloques válidos con Proof-of-Work simulado.
        test_blockchain_integrity_and_tampering():
            Ejecuta el flujo completo de creación, validación y detección de corrupción.
'''

import sys
import os
import time
from typing import List, Optional

# --- AJUSTE DE RUTA PARA EJECUCIÓN DIRECTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '../../..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from akm.core.models.blockchain import Blockchain
from akm.core.models.block import Block
from akm.core.models.transaction import Transaction
from akm.core.validators.chain_validator import ChainValidator
from akm.core.services.block_hasher import BlockHasher
from akm.core.services.merkle_tree_builder import MerkleTreeBuilder

# --- UTILIDAD (HELPER) PARA EL TEST ---
def crear_bloque_simulado(index: int, prev_hash: str, transactions: Optional[List[Transaction]] = None) -> Block:
    if transactions is None:
        transactions = []
        
    timestamp = int(time.time())
    
    tx_hashes = [tx.tx_hash for tx in transactions] if transactions else []
    merkle_root = MerkleTreeBuilder.build(tx_hashes)
    
    block = Block(
        index=index,
        timestamp=timestamp,
        previous_hash=prev_hash,
        bits="1d00ffff", 
        merkle_root=merkle_root,
        nonce=0,         
        block_hash="",   
        transactions=transactions
    )
    
    real_hash = BlockHasher.calculate(block)
    block._hash = real_hash  # type: ignore
    
    return block

def test_blockchain_integrity_and_tampering():
    print("\n==========================================")
    print("   TEST DE INTEGRIDAD BLOCKCHAIN (AKM)    ")
    print("==========================================\n")

    print(">> Iniciando Blockchain...")
    chain = Blockchain()

    print("\n[1] Construyendo cadena válida...")
    
    genesis = crear_bloque_simulado(index=0, prev_hash="0" * 64)
    chain.add_block(genesis)
    
    block_1 = crear_bloque_simulado(index=1, prev_hash=genesis.hash)
    chain.add_block(block_1)
    
    block_2 = crear_bloque_simulado(index=2, prev_hash=block_1.hash)
    chain.add_block(block_2)
    
    print(f"\n+ Altura actual: {len(chain.chain)} bloques.")
    print("\n[2] Verificando integridad inicial...")
    es_valida = ChainValidator.verify_chain_links(chain.chain)
    
    assert es_valida is True
    print("\nESTADO: CADENA VÁLIDA.")

    print("\n[3]\nATENCIÓN: Simulando ataque de hacker...")
    print("    -> Modificando el Hash del Bloque 1 en memoria...")
    
    chain._chain[1]._hash = "HASH_FALSO_INTRODUCIDO_POR_HACKER"  # type: ignore

    print("\n[4] Verificando integridad post-ataque...")
    es_valida_post_ataque = ChainValidator.verify_chain_links(chain.chain)

    assert es_valida_post_ataque is False
    
    print("\nSEGURIDAD EXITOSA: El validador detectó la corrupción.")
    print("\n(El test pasó porque el sistema falló como se esperaba)")
    print("\n==========================================")

if __name__ == "__main__":
    try:
        test_blockchain_integrity_and_tampering()
        print("\nTEST FINALIZADO CON ÉXITO")
    except AssertionError as e:
        print(f"\nEL TEST FALLÓ: {e}")
    except Exception as e:
        print(f"\nERROR INESPERADO: {e}")