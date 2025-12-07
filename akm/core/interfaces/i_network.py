# akm/core/interfaces/i_network.py
from abc import ABC, abstractmethod
from typing import Callable, Dict, Any, List, Optional # Importamos Optional y List

class INetworkService(ABC):
    """
    Contrato para el servicio de red P2P.
    Define cómo el nodo interactúa con el mundo exterior.
    """

    @abstractmethod
    def start(self) -> None:
        """Inicia el servidor para escuchar conexiones entrantes."""
        pass

    @abstractmethod
    def connect_to(self, ip: str, port: int) -> bool:
        """Establece una conexión persistente (TCP) con otro nodo."""
        pass

    @abstractmethod
    def broadcast(self, message: Dict[str, Any], exclude_peer: Optional[str] = None) -> None:
        """Envía un mensaje a TODOS los nodos conectados, excepto al indicado."""
        pass

    @abstractmethod
    def register_handler(self, handler: Callable[[Dict[str, Any], str], None]) -> None:
        """
        Registra la función que el Core ejecutará cuando llegue un mensaje.
        El handler recibe (datos, peer_id).
        """
        pass
    
    @abstractmethod
    def get_connected_peers(self) -> List[str]: # Tipado explícito con List[str]
        """Retorna lista de nodos conectados."""
        pass