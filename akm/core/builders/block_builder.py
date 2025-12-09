# akm/core/builders/block_builder.py
'''
class BlockBuilder:
    Construye un bloque válido encontrando un nonce que satisfaga la dificultad.

    Methods::
        build(...) -> Optional[Block]:
            Ejecuta la minería (búsqueda de hash) y retorna el bloque sellado.
            Retorna None si se recibe señal de interrupción.
'''

import time
import logging
import threading  # <--- NECESARIO para Event
from typing import List, Optional  # <--- NECESARIO para el retorno Optional

# Modelos y Configuración
from akm.core.models.block import Block
from akm.core.models.transaction import Transaction
from akm.core.config.config_manager import ConfigManager

# Servicios de Dominio
from akm.core.services.merkle_tree_builder import MerkleTreeBuilder
from akm.core.services.block_hasher import BlockHasher
from akm.core.utils.difficulty_utils import DifficultyUtils

# Configuración de log
logging.basicConfig(level=logging.INFO, format='[BlockBuilder] %(message)s')

class BlockBuilder:

    @staticmethod
    def build(
        transactions: List[Transaction],
        previous_hash: str,
        bits: str,
        index: int,
        interrupt_event: Optional[threading.Event] = None  # <--- NUEVO PARÁMETRO
    ) -> Optional[Block]:  # <--- NUEVO TIPO DE RETORNO (Block | None)
        
        config = ConfigManager()
        max_nonce_limit = config.max_nonce

        logging.info(f"Iniciando minería de Bloque #{index} con {len(transactions)} transacciones...")
        logging.info(f"Dificultad objetivo (Bits): {bits}")

        timestamp = int(time.time())
        tx_hashes = [tx.tx_hash for tx in transactions]
        merkle_root = MerkleTreeBuilder.build(tx_hashes)
        target = DifficultyUtils.bits_to_target(bits)
        nonce = 0
        start_time = time.time()

        while nonce <= max_nonce_limit:
            # 1. VERIFICACIÓN DE INTERRUPCIÓN
            # Si el nodo recibe un bloque externo, interrupt_event se activa (set)
            if interrupt_event and interrupt_event.is_set():
                logging.warning(f"⚠️ Minería interrumpida en nonce {nonce}. (Nuevo bloque detectado en la red)")
                return None  # Retornamos None para indicar cancelación

            # 2. Construcción del Candidato
            candidate_block = Block(
                index=index,
                timestamp=timestamp,
                previous_hash=previous_hash,
                bits=bits,
                merkle_root=merkle_root,
                nonce=nonce,
                block_hash="", # Hash temporal vacío para el cálculo
                transactions=transactions
            )
            
            # 3. Cálculo de Hash
            block_hash = BlockHasher.calculate(candidate_block)
            hash_int = int(block_hash, 16)

            # 4. Verificación de Dificultad (PoW)
            if hash_int <= target:
                elapsed = time.time() - start_time
                logging.info(f"\t¡BLOQUE MINADO! Nonce: {nonce} | Hash: {block_hash[:16]}... ({elapsed:.2f}s)")
                
                # Retornamos el bloque completo con el hash válido
                return Block(
                    index=index,
                    timestamp=timestamp,
                    previous_hash=previous_hash,
                    bits=bits,
                    merkle_root=merkle_root,
                    nonce=nonce,
                    block_hash=block_hash,
                    transactions=transactions
                )

            nonce += 1
            
            # Opcional: Actualizar timestamp cada X nonces para evitar desfase si la minería es lenta
            # if nonce % 100000 == 0: timestamp = int(time.time())

        # Si agotamos los nonces sin éxito ni interrupción
        raise TimeoutError("BlockBuilder: No se encontró solución dentro del rango de Nonce (Mining Failed).")