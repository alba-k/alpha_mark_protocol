# akm/core/managers/consensus_orchestrator.py
'''
class ConsensusOrchestrator:
    El Cerebro del sistema (Controlador de Flujo).
    Coordina la validación, aceptación y reorganización de bloques siguiendo SOLID/SRP.

    Methods::
        add_block(new_block) -> bool:
            Punto de entrada principal. Evalúa y decide si un bloque se añade a la cadena.
'''

import logging

from akm.core.models.block import Block
from akm.core.models.blockchain import Blockchain
from akm.core.managers.utxo_set import UTXOSet
from akm.core.services.mempool import Mempool
from akm.core.validators.block_rules_validator import BlockRulesValidator
from akm.core.managers.chain_reorg_manager import ChainReorgManager

logging.basicConfig(level=logging.INFO, format='[Consensus] %(message)s')

class ConsensusOrchestrator:

    def __init__(
        self,
        blockchain: Blockchain,
        utxo_set: UTXOSet,
        mempool: Mempool,
        chain_reorg_manager: ChainReorgManager,
        block_rules_validator: BlockRulesValidator
    ):
        self._blockchain = blockchain
        self._utxo_set = utxo_set
        self._mempool = mempool
        self._reorg_manager = chain_reorg_manager
        self._validator = block_rules_validator

    def add_block(self, new_block: Block) -> bool:
        """
        Flujo Principal de Consenso:
        1. Validar Reglas Integrales.
        2. Decidir: ¿Extensión simple o Fork?
        """
        
        # 1. Validación Integral
        if not self._validator.validate(new_block):
            logging.error(f"Bloque {new_block.hash[:8]} rechazado por el Validador de Reglas.")
            return False

        last_block = self._blockchain.last_block
        
        # CASO A: Génesis (Primer bloque de la historia)
        if not last_block:
            if new_block.index != 0:
                logging.error("Rechazado: Se esperaba bloque Génesis (Index 0).")
                return False
            
            logging.info("🌟 Bloque Génesis aceptado. Iniciando cadena.")
            self._reorg_manager.apply_block_to_state(new_block)
            self._blockchain.add_block(new_block)
            return True

        # CASO B: Extensión Simple (Happy Path)
        if new_block.previous_hash == last_block.hash:
            if new_block.index != last_block.index + 1:
                logging.error(f"Rechazado: Índice discontinuo. Esperado {last_block.index + 1}, recibido {new_block.index}.")
                return False
            
            logging.info(f"🔗 Extendiendo cadena con Bloque #{new_block.index} ({new_block.hash[:8]})")
            self._reorg_manager.apply_block_to_state(new_block)
            self._blockchain.add_block(new_block)
            return True

        # CASO C: Bifurcación (Fork) - LÓGICA CORREGIDA Y ACTIVADA
        parent_block = self._blockchain.get_block_by_hash(new_block.previous_hash)

        if parent_block:
            # Conocemos al padre, es un fork válido.
            # Regla de la Cadena Más Larga:
            if new_block.index > last_block.index:
                logging.warning(f"🔀 REORG DETECTADO: Nueva rama (Alt: {new_block.index}) supera actual ({last_block.index})")
                
                # --- INICIO CORRECCIÓN: Sincronización Local ---
                # Reconstruimos la cadena alternativa completa retrocediendo punteros en la DB
                # Esto actúa como un "SyncManager" local usando los bloques que ya hemos descargado/recibido.
                potential_new_chain = [new_block]
                curr = parent_block
                
                # Retroceder hasta encontrar el Génesis (index 0)
                while curr:
                    potential_new_chain.append(curr)
                    if curr.index == 0:
                        break
                    # Buscamos al padre del actual
                    curr = self._blockchain.get_block_by_hash(curr.previous_hash)
                
                # Invertimos la lista para tener [Génesis -> ... -> NuevoBloque]
                potential_new_chain.reverse()
                
                # Verificar integridad: ¿Llegamos al origen?
                if not potential_new_chain or potential_new_chain[0].index != 0:
                    logging.error("❌ Reorg fallido: No se pudo reconstruir la cadena completa (faltan ancestros).")
                    return False

                logging.info(f"🔄 Ejecutando Reorg de {len(potential_new_chain)} bloques...")
                
                # Delegamos al ChainReorgManager la tarea pesada (Reemplazo + Reconstrucción UTXO)
                if self._reorg_manager.handle_reorg(potential_new_chain):
                    logging.info(f"✅ Reorganización exitosa. Nuevo Tip: {new_block.hash[:8]}")
                    return True
                else:
                    logging.error("❌ Falló la ejecución del Reorg en el Manager.")
                    return False
                # --- FIN CORRECCIÓN ---

            else:
                logging.info(f"Fork ignorado: Rama alterna (Alt: {new_block.index}) es más corta o igual.")
                return False

        # CASO D: Huérfano
        logging.warning(f"⚠️ Bloque Huérfano: Padre {new_block.previous_hash[:8]} desconocido.")
        return False