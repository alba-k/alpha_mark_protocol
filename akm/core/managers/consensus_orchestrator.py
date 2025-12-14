# akm/core/managers/consensus_orchestrator.py

import logging
from typing import List

# Modelos
from akm.core.models.block import Block
from akm.core.models.blockchain import Blockchain
from akm.core.managers.utxo_set import UTXOSet
from akm.core.services.mempool import Mempool
from akm.core.validators.block_rules_validator import BlockRulesValidator
from akm.core.managers.chain_reorg_manager import ChainReorgManager

logger = logging.getLogger(__name__)

class ConsensusOrchestrator:
    def __init__(
        self,
        blockchain: Blockchain,
        utxo_set: UTXOSet,
        mempool: Mempool,
        chain_reorg_manager: ChainReorgManager,
        block_rules_validator: BlockRulesValidator
    ) -> None:
        try:
            self._blockchain = blockchain
            self._utxo_set = utxo_set
            self._mempool = mempool
            self._reorg_manager = chain_reorg_manager
            self._validator = block_rules_validator
            logger.info("Cerebro de consenso iniciado.")
        except Exception:
            logger.exception("Error al inicializar ConsensusOrchestrator")

    def add_block(self, new_block: Block) -> bool:
        
        try:
            # 1. Validación de Reglas de Consenso
            if not self._validator.validate(new_block):
                logger.info(f"Bloque {new_block.hash[:8]} rechazado: Fallo de reglas.")
                return False

            last_block = self._blockchain.last_block
            
            # --- CASO A: Bloque Génesis ---
            if not last_block:
                if new_block.index == 0:
                    logger.info("🌟 Bloque Génesis aceptado. Cadena iniciada.")
                    self._reorg_manager.apply_block_to_state(new_block)
                    self._blockchain.add_block(new_block)
                    return True
                return False

            # --- CASO B: Extensión Simple (Happy Path) ---
            if new_block.previous_hash == last_block.hash:
                if new_block.index == last_block.index + 1:
                    # Actualización de estado y persistencia
                    self._reorg_manager.apply_block_to_state(new_block)
                    self._blockchain.add_block(new_block)
                    logger.info(f"🔗 Bloque #{new_block.index} unido a la cadena.")
                    return True

            # --- CASO C: Bifurcación (Fork) ---
            return self._handle_potential_fork(new_block, last_block)

        except Exception:
            logger.exception(f"Bug procesando bloque #{new_block.index}")
            return False

    def _handle_potential_fork(self, new_block: Block, current_tip: Block) -> bool:
        try:
            # 1. ¿Es un bloque huérfano?
            if not self._blockchain.get_block_by_hash(new_block.previous_hash):
                logger.info(f"Bloque #{new_block.index} huérfano. Ignorado.")
                return False

            # 2. Regla de la cadena más larga (Longest Chain Rule)
            if new_block.index <= current_tip.index:
                logger.info(f"Fork ignorado: Rama débil (Alt: {new_block.index}).")
                return False

            logger.info(f"🔀 Conflicto detectado: Rama nueva (#{new_block.index}) es más larga.")

            # 3. Reconstrucción de la nueva rama
            new_chain = self._build_new_chain_segment(new_block)
            if not new_chain:
                logger.info("Reorg abortado: Cadena incompleta.")
                return False

            # 4. Delegar la cirugía al ReorgManager
            return self._reorg_manager.handle_reorg(new_chain)

        except Exception:
            logger.exception("Error en lógica de resolución de forks")
            return False

    def _build_new_chain_segment(self, tip_block: Block) -> List[Block]:
        segment = [tip_block]
        curr = self._blockchain.get_block_by_hash(tip_block.previous_hash)
        
        while curr:
            segment.append(curr)
            if curr.index == 0: break
            curr = self._blockchain.get_block_by_hash(curr.previous_hash)
        
        segment.reverse()
        return segment if segment and segment[0].index == 0 else []