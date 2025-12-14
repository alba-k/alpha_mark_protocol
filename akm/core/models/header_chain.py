# akm/core/models/header_chain.py

import logging
from typing import List, Optional, Dict

from akm.core.models.block_header import BlockHeader
from akm.core.utils.difficulty_utils import DifficultyUtils
from akm.core.interfaces.i_chain import IChain

logger = logging.getLogger(__name__)

class HeaderChain(IChain): 
    
    def __init__(self):
        self._headers: List[BlockHeader] = []
        
        self._headers_map: Dict[str, BlockHeader] = {}
        
        logger.info("📱 Cadena SPV (Light Client) iniciada.")

    # --- Propiedades de la Interfaz ---
    @property
    def height(self) -> int:
        return len(self._headers) - 1

    @property
    def tip(self) -> Optional[BlockHeader]:
        return self._headers[-1] if self._headers else None

    # --- Métodos Públicos ---

    def add_header(self, header: BlockHeader) -> bool:
        try:
            # Caso A: Primer bloque (Génesis)
            if not self._headers:
                self._save_header_internal(header)
                logger.info(f"✨ Header Génesis #{header.index} aceptado.")
                return True

            last = self._headers[-1]
            
            # Caso B: Validación de continuidad
            if header.previous_hash != last.hash: 
                logger.warning(f"⛔ Header #{header.index} rechazado: Hash previo no coincide.")
                return False

            # Caso C: Validación PoW
            target = DifficultyUtils.bits_to_target(header.bits)
            hash_int = int(header.hash, 16) # ⚠️ Mantenemos tu atributo '.hash'
            
            if hash_int > target:
                logger.warning(f"🔨 Header #{header.index} rechazado: PoW insuficiente.")
                return False

            # Éxito: Guardamos en ambas estructuras
            self._save_header_internal(header)
            
            # Log reducido para no saturar consola
            if header.index % 100 == 0:
                logger.info(f"Header #{header.index} añadido.")
            
            return True

        except Exception:
            logger.exception(f"Error procesando header #{header.index}")
            return False

    def get_header_by_hash(self, block_hash: str) -> Optional[BlockHeader]:
        
        return self._headers_map.get(block_hash)

    # --- Método Privado de Ayuda ---
    
    def _save_header_internal(self, header: BlockHeader):
        self._headers.append(header)
        self._headers_map[header.hash] = header 