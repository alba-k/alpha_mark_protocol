# akm/core/interfaces/i_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from akm.core.models.block import Block

class IBlockchainRepository(ABC):
    """
    Contrato Polimórfico para el almacenamiento de la Blockchain.
    """

    @abstractmethod
    def save_block(self, block: Block) -> None:
        """Guarda un bloque de forma persistente."""
        pass

    @abstractmethod
    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        """Recupera un bloque por su hash único."""
        pass

    @abstractmethod
    def get_last_block(self) -> Optional[Block]:
        """Recupera el último bloque (Tip) de la cadena."""
        pass

    @abstractmethod
    def get_blocks_range(self, start_index: int, limit: int) -> List[Block]:
        """Recupera una secuencia de bloques (paginación)."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Retorna la altura total/cantidad de bloques."""
        pass