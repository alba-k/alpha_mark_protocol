# akm/infra/persistence/json/json_repository.py
from typing import Optional, List
from akm.core.interfaces.i_repository import IBlockchainRepository
from akm.core.models.block import Block

class JsonBlockchainRepository(IBlockchainRepository):
    """
    [FUTURO/LEGACY] Implementación basada en archivos de texto.
    Útil para debug visual rápido, pero no para producción.
    """
    def save_block(self, block: Block) -> None:
        raise NotImplementedError("Persistencia JSON desactivada. Use SQLite.")

    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        raise NotImplementedError("Persistencia JSON desactivada. Use SQLite.")

    def get_last_block(self) -> Optional[Block]:
        raise NotImplementedError("Persistencia JSON desactivada. Use SQLite.")

    def get_blocks_range(self, start_index: int, limit: int) -> List[Block]:
        raise NotImplementedError("Persistencia JSON desactivada. Use SQLite.")

    def count(self) -> int:
        raise NotImplementedError("Persistencia JSON desactivada. Use SQLite.")