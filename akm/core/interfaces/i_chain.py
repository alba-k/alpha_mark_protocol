# akm/core/interfaces/i_chain.py

from abc import ABC, abstractmethod
from typing import Optional
from akm.core.models.block_header import BlockHeader

class IChain(ABC):
    """
    Contrato base para cualquier estructura de cadena (Full o Light).
    
    Aplica el principio de Segregación de Interfaces: permite que los componentes
    de red (como el GossipManager) trabajen con la cadena sin importar si
    los datos están en una base de datos o en memoria volátil.
    """

    @property
    @abstractmethod
    def height(self) -> int:
        """
        Retorna la altura actual (cantidad de elementos).
        Utilizado para comparar qué cadena es más larga en resolución de conflictos.
        """
        pass

    @property
    @abstractmethod
    def tip(self) -> Optional[BlockHeader]:
        """
        Retorna el último encabezado (bloque) de la cadena.
        Representa el estado actual de la punta de la cadena.
        """
        pass

    @abstractmethod
    def add_header(self, header: BlockHeader) -> bool:
        """
        Intenta validar y enlazar un nuevo encabezado.
        
        Args:
            header: El BlockHeader recibido.
            
        Returns:
            bool: True si el enlace es válido y se agregó a la cadena.
        """
        pass