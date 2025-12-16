# akm/core/managers/consensus_orchestrator.py

import logging
from typing import List, Optional

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
        """
        Intenta añadir un bloque a la cadena. 
        Maneja extensión normal, bloques génesis y bifurcaciones (forks).
        """
        try:
            # 1. Validación de Reglas de Consenso (PoW, Firmas, Estructura)
            if not self._validator.validate(new_block):
                logger.warning(f"⛔ Bloque {new_block.hash[:8]} rechazado: Reglas inválidas.")
                return False

            last_block: Optional[Block] = self._blockchain.last_block
            
            # --- CASO A: Bloque Génesis ---
            if last_block is None:
                if new_block.index == 0:
                    logger.info("🌟 Bloque Génesis aceptado. Cadena iniciada.")
                    self._reorg_manager.apply_block_to_state(new_block)
                    self._blockchain.add_block(new_block)
                    return True
                return False

            # --- CASO B: Extensión Simple (Happy Path) ---
            # El bloque es exactamente el hijo del actual tip.
            if new_block.previous_hash == last_block.hash:
                if new_block.index == last_block.index + 1:
                    self._reorg_manager.apply_block_to_state(new_block)
                    self._blockchain.add_block(new_block)
                    logger.info(f"🔗 Bloque #{new_block.index} ({new_block.hash[:8]}) extendió la cadena.")
                    return True

            # --- CASO C: Bifurcación o Bloque Fuera de Orden ---
            return self._handle_potential_fork(new_block, last_block)

        except Exception as e:
            logger.exception(f"🐛 Bug procesando bloque #{new_block.index}: {e}")
            return False

    def _handle_potential_fork(self, new_block: Block, current_tip: Block) -> bool:
        try:
            # 1. ¿Es un bloque huérfano? (Padre desconocido)
            # Si no tenemos el padre en la DB, no podemos conectarlo ni validarlo.
            if not self._blockchain.get_block_by_hash(new_block.previous_hash):
                # Retornamos False para que el FullNode active el Sync y pida los ancestros.
                logger.debug(f"Bloque #{new_block.index} es huérfano. Requiere Sync.")
                return False

            # 2. Regla de la Cadena Más Larga
            # [FIX LINE 92]: Aseguramos que current_tip sea un objeto Block válido
            if new_block.index <= current_tip.index:
                logger.debug(f"Fork ignorado: Rama no ganadora (Alt: {new_block.index} <= {current_tip.index}).")
                return False

            # 3. ¡REORG DETECTADO! (La nueva rama es más larga)
            logger.info(f"🔀 REORG DETECTADO: Rama nueva (#{new_block.index}) supera a local (#{current_tip.index}).")

            # Intentamos construir la cadena completa desde el nuevo bloque hacia atrás
            # hasta encontrar un ancestro común que ya tengamos.
            
            # [FIX LINE 100]: Tipado explícito para 'new_chain'
            new_chain: List[Block] = self._build_new_chain_segment(new_block)
            
            if not new_chain:
                # Esto pasa si tenemos el padre (paso 1) pero algo falló en la recolección
                logger.warning("Reorg abortado: No se pudo construir el segmento de cadena.")
                return False

            # 4. Ejecutar la reorganización
            # [FIX LINE 106]: Retorno explícito booleano
            success: bool = self._reorg_manager.handle_reorg(new_chain)
            return success

        except Exception:
            logger.exception("Error crítico en lógica de resolución de forks")
            return False

    def _build_new_chain_segment(self, tip_block: Block) -> List[Block]:
        """Recupera los bloques de la rama nueva hacia atrás."""
        # [FIX]: Inicialización tipada de la lista
        segment: List[Block] = [tip_block]
        
        curr_hash = tip_block.previous_hash
        
        # Recuperamos el primer ancestro
        curr: Optional[Block] = self._blockchain.get_block_by_hash(curr_hash)
        
        while curr is not None:
            # Si llegamos a un punto donde la cadena ya es canónica, paramos.
            # (Simplificación: asumimos que reconstruimos hasta encontrar el punto de split)
            segment.append(curr)
            
            # Avanzamos hacia atrás
            if curr.index == 0:
                break
                
            curr = self._blockchain.get_block_by_hash(curr.previous_hash)
            
            # Freno de emergencia para evitar bucles infinitos o memoria excesiva
            if len(segment) > 1000: 
                break 
        
        segment.reverse()
        return segment