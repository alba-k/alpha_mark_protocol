# akm/core/interfaces/i_chain.py
from abc import ABC, abstractmethod
from typing import Optional
from akm.core.models.block_header import BlockHeader

class IChain(ABC):
    """
    [Interface Segregation]
    Contrato común para cualquier estructura de cadena (Full o Light).
    Permite polimorfismo: El resto del sistema no necesita saber si es DB o RAM.
    """

    @property
    @abstractmethod
    def height(self) -> int:
        """Altura actual de la cadena."""
        pass

    @property
    @abstractmethod
    def tip(self) -> Optional[BlockHeader]:
        """Último encabezado conocido (Tip)."""
        pass

    @abstractmethod
    def add_header(self, header: BlockHeader) -> bool:
        """Intenta agregar un nuevo encabezado a la cadena."""
        pass