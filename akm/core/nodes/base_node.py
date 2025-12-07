# akm/core/nodes/base_node.py
import logging
from typing import Dict, Any

# Infraestructura
from akm.infra.network.p2p_service import P2PService
from akm.core.managers.gossip_manager import GossipManager

logging.basicConfig(level=logging.INFO, format='[BaseNode] %(message)s')

class BaseNode:
    """
    [OCP] Nodo de Enrutamiento (Routing Node).
    Base para cualquier tipo de nodo en la red. Maneja solo transporte.
    """
    
    def __init__(self, p2p_service: P2PService, gossip_manager: GossipManager):
        # Composición: Inyectamos la capacidad de red
        self.p2p = p2p_service
        self.gossip = gossip_manager
        
        # Conectamos el listener
        self.p2p.register_handler(self._handle_incoming_message)
        
    def start(self):
        """Inicia el servicio P2P."""
        logging.info("🌐 Iniciando Nodo Base (Capa de Red)...")
        self.p2p.start()
        
    def get_peers(self):
        return self.p2p.get_connected_peers()

    def connect_to(self, ip: str, port: int):
        self.p2p.connect_to(ip, port)

    def _handle_incoming_message(self, message: Dict[str, Any], peer_id: str):
        """
        Callback de bajo nivel. Valida formato y delega.
        """
        msg_type = message.get("type")
        payload = message.get("payload")
        
        if not msg_type or not payload:
            logging.warning(f"Mensaje malformado de {peer_id}")
            return

        # Delegación (Template Method)
        self._process_payload(str(msg_type), payload, peer_id)

    def _process_payload(self, msg_type: str, payload: Dict[str, Any], peer_id: str):
        """
        Método gancho (Hook) para ser sobreescrito por los hijos (FullNode).
        El nodo base ignora el contenido.
        """
        pass