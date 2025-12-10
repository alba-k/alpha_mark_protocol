# akm/core/models/header_chain.py
import logging
from typing import List, Optional

from akm.core.models.block_header import BlockHeader
from akm.core.utils.difficulty_utils import DifficultyUtils
from akm.core.interfaces.i_chain import IChain

class HeaderChain(IChain):
    """
    [Componente Móvil]
    Gestiona la secuencia de encabezados en un Nodo SPV (solo en memoria RAM por ahora).
    """
    def __init__(self):
        self._headers: List[BlockHeader] = []

    # --- Implementación IChain ---

    @property
    def height(self) -> int:
        return len(self._headers)

    @property
    def tip(self) -> Optional[BlockHeader]:
        return self._headers[-1] if self._headers else None

    def add_header(self, header: BlockHeader) -> bool:
        if not self._headers:
            # Aceptamos el primero (Génesis o checkpoint)
            self._headers.append(header)
            return True

        last = self._headers[-1]
        
        # 1. Validación de Enlace (Hash Chain)
        if header.previous_hash != last.hash:
            logging.warning(f"⛔ SPV: Quiebre de cadena. Esperado {last.hash[:8]}, recibido {header.previous_hash[:8]}")
            return False

        # 2. Validación de PoW (Dificultad)
        try:
            target = DifficultyUtils.bits_to_target(header.bits)
            hash_int = int(header.hash, 16)
            
            if hash_int > target:
                logging.warning(f"⛔ SPV: PoW insuficiente en header #{header.index}")
                return False
        except Exception as e:
            logging.error(f"Error validando PoW: {e}")
            return False

        self._headers.append(header)
        logging.info(f"📱 SPV: Header #{header.index} aceptado.")
        return True

    # ⚡ MÉTODO PÚBLICO: Permite buscar headers para validar pagos
    def get_header_by_hash(self, block_hash: str) -> Optional[BlockHeader]:
        """
        Busca un header validado por su hash.
        Necesario para verificar pruebas de Merkle.
        """
        for header in self._headers:
            if header.hash == block_hash:
                return header
        return None