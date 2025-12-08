# akm/core/interfaces/i_chain_manager.py

from abc import ABC, abstractmethod
from akm.core.models.block_header import BlockHeader

class IChainManager(ABC):
    """Interfaz común para cualquier tipo de cadena (Full o Light)."""
    
    @abstractmethod
    def add_header(self, header: BlockHeader) -> bool:
        pass
        
    @property
    @abstractmethod
    def height(self) -> int:
        pass