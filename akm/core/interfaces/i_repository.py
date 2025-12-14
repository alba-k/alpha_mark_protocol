from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

# NOTA: Ya no importamos 'Block' aquí para evitar dependencias circulares
# y porque el repositorio ahora trabaja con datos crudos (Diccionarios).

class IBlockchainRepository(ABC):
    """
    Contrato Polimórfico para el almacenamiento de la Blockchain.
    Ahora define operaciones sobre DATOS (Dicts), no sobre Entidades.
    """

    @abstractmethod
    def save_block(self, block_data: Dict[str, Any]) -> bool:
        """
        Guarda un solo bloque persistente.
        Recibe: Diccionario serializado del bloque.
        Retorna: True si se guardó, False si falló.
        """
        pass

    @abstractmethod
    def save_blocks_atomic(self, chain_data: List[Dict[str, Any]]) -> bool:
        """
        Guarda una lista de bloques en una sola transacción.
        Recibe: Lista de Diccionarios.
        """
        pass

    @abstractmethod
    def get_block_by_hash(self, block_hash: str) -> Optional[Dict[str, Any]]:
        """Recupera los datos de un bloque por su hash."""
        pass

    @abstractmethod
    def get_last_block(self) -> Optional[Dict[str, Any]]:
        """Recupera los datos del último bloque (Tip)."""
        pass

    @abstractmethod
    def get_blocks_range(self, start_index: int, limit: int) -> List[Dict[str, Any]]:
        """Recupera una secuencia de datos de bloques."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Retorna la altura total."""
        pass

    @abstractmethod
    def get_headers_range(self, start_hash: str, limit: int = 2000) -> List[Dict[str, Any]]:
        """Recupera solo metadatos."""
        pass