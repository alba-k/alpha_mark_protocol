# akm/infra/persistence/leveldb/leveldb_repository.py
from typing import Optional, List
from akm.core.interfaces.i_repository import IBlockchainRepository
from akm.core.models.block import Block

class LevelDBBlockchainRepository(IBlockchainRepository):
    """
    [FUTURO] Implementación de alto rendimiento usando LevelDB (Key-Value).
    Reservado para cuando el sistema requiera escala masiva.
    """
    def __init__(self):
        # TODO: Inicializar conexión Plyvel aquí
        pass

    def save_block(self, block: Block) -> None:
        raise NotImplementedError("LevelDB aún no está implementado.")

    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        raise NotImplementedError("LevelDB aún no está implementado.")

    def get_last_block(self) -> Optional[Block]:
        raise NotImplementedError("LevelDB aún no está implementado.")

    def get_blocks_range(self, start_index: int, limit: int) -> List[Block]:
        raise NotImplementedError("LevelDB aún no está implementado.")

    def count(self) -> int:
        raise NotImplementedError("LevelDB aún no está implementado.")