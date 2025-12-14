# akm/core/interfaces/i_network.py

from abc import ABC, abstractmethod
from typing import Callable, Dict, Any, List, Optional

class INetworkService(ABC):
    """
    Contrato para el servicio de red P2P.
    Define cómo el nodo interactúa con el mundo exterior de forma desacoplada.
    """

    @abstractmethod
    def start(self) -> None:
        """Inicia el servidor y pone al nodo en modo escucha."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Detiene el servidor y cierra conexiones activas (Graceful Shutdown)."""
        pass

    @abstractmethod
    def connect_to(self, ip: str, port: int) -> bool:
        """Establece una conexión saliente persistente con un par."""
        pass
    
    @abstractmethod
    def broadcast(self, message: Dict[str, Any], exclude_peer: Optional[str] = None) -> None:
        """
        GOSSIP: Propaga un mensaje a TODOS los nodos conectados.
        Ideal para: Difusión de nuevos bloques y transacciones.
        """
        pass

    @abstractmethod
    def send_message(self, peer_id: str, message: Dict[str, Any]) -> bool:
        """
        DIRECTO: Envía un mensaje a un único nodo específico.
        Ideal para: Sincronización (Sync) y petición de bloques faltantes.
        """
        pass

    @abstractmethod
    def register_handler(self, handler: Callable[[Dict[str, Any], str], None]) -> None:
        """Inyecta la lógica del Core (Manejador de Mensajes) en la red."""
        pass
    
    @abstractmethod
    def get_connected_peers(self) -> List[str]: 
        """Retorna la lista de identificadores de los nodos activos."""
        pass