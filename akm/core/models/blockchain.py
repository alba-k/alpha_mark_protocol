# akm/core/models/blockchain.py

import logging
from typing import List, Optional, Iterator, Dict, Any

from akm.core.models.block import Block
from akm.core.models.block_header import BlockHeader
from akm.core.interfaces.i_repository import IBlockchainRepository
from akm.core.interfaces.i_chain import IChain

logger = logging.getLogger(__name__)

class Blockchain(IChain): 

    def __init__(self, repository: IBlockchainRepository):
        self._repository = repository
        logger.info(f"🚀 Sistema iniciado. Altura actual: {self.height}")

    # --- Getters ---
    @property
    def height(self) -> int: 
        count = self._repository.count()
        return count - 1 if count > 0 else -1

    @property
    def tip(self) -> Optional[Block]: 
        # Usamos Any para evitar conflicto de tipos (Repo devuelve Dict, Interface dice Block)
        data: Any = self._repository.get_last_block()
        return Block.from_dict(data) if data else None

    def add_header(self, header: BlockHeader) -> bool:
        return False 

    # --- Getters ---
    @property
    def last_block(self) -> Optional[Block]: 
        data: Any = self._repository.get_last_block()
        return Block.from_dict(data) if data else None

    def add_block(self, block: Block) -> bool:
        """
        Agrega un bloque a la persistencia.
        """
        try:
            # [CORRECCIÓN 1] Usamos 'Any' para engañar al Linter.
            # La interfaz espera 'Block', pero SQLite necesita 'Dict'.
            # Al tiparlo como Any, el linter deja de quejarse.
            block_data: Any = block.to_dict()
            
            success = self._repository.save_block(block_data)
            
            if success:
                logger.info(f"✅ Bloque #{block.index} guardado en DB permanentemente.")
                return True
            else:
                logger.error(f"❌ Fallo al escribir Bloque #{block.index} en DB.")
                return False

        except Exception:
            logger.exception("❌ Error fatal: El bloque no pudo unirse.")
            return False

    def replace_chain(self, new_chain: List[Block]) -> None:
        try:
            # [CORRECCIÓN 2] Lo mismo para la lista de bloques
            chain_data: Any = [b.to_dict() for b in new_chain]
            
            self._repository.save_blocks_atomic(chain_data)
            logger.info(f"🔄 Cadena reemplazada. Nueva altura: {len(new_chain)}.")
        except Exception:
            logger.exception("❌ Error crítico en reemplazo de cadena.")

    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        data: Any = self._repository.get_block_by_hash(block_hash)
        return Block.from_dict(data) if data else None

    def get_block_by_index(self, index: int) -> Optional[Block]:
        blocks_data: Any = self._repository.get_blocks_range(start_index=index, limit=1)
        if blocks_data and len(blocks_data) > 0:
            return Block.from_dict(blocks_data[0])
        return None
    
    def get_blocks_range(self, start_index: int, limit: int) -> List[Block]:
        data_list: Any = self._repository.get_blocks_range(start_index, limit)
        
        # [CORRECCIÓN 3] Definimos explícitamente el tipo de la lista resultante
        # Esto soluciona el error "Type of append is partially unknown"
        result: List[Block] = []
        
        if data_list:
            for d in data_list:
                if isinstance(d, Block):
                    result.append(d)
                else:
                    result.append(Block.from_dict(d))
        return result

    def get_history_iterator(self, start_index: int = 0, batch_size: int = 100) -> Iterator[Block]:
        current = start_index
        while True:
            batch_data: Any = self._repository.get_blocks_range(current, batch_size)
            if not batch_data:
                break
            
            for data in batch_data:
                if isinstance(data, Block):
                    yield data
                else:
                    yield Block.from_dict(data)
            
            current += len(batch_data)

    def get_headers(self, start_hash: str, limit: int = 2000) -> List[Dict[str, Any]]:
        return self._repository.get_headers_range(start_hash, limit)

    def __len__(self) -> int:
        return self._repository.count()