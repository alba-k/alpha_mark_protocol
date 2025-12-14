# akm/core/interfaces/i_chain_manager.py

from abc import ABC, abstractmethod
from akm.core.models.block_header import BlockHeader

class IChainManager(ABC):
    """
    Contrato fundamental para la gestión de la cadena de bloques.
    Define las capacidades mínimas compartidas entre un Full Node y un Cliente SPV.
    """
    
    @abstractmethod
    def add_header(self, header: BlockHeader) -> bool:
        """
        Intenta procesar y añadir un nuevo encabezado a la cadena local.
        
        Args:
            header: El objeto BlockHeader a validar e integrar.
            
        Returns:
            bool: True si el header fue aceptado y enlazado correctamente.
        """
        pass
        
    @property
    @abstractmethod
    def height(self) -> int:
        """
        Retorna la altura actual de la cadena (cantidad de bloques/headers).
        
        Returns:
            int: Índice del último elemento más uno.
        """
        pass