# akm/core/nodes/base_node.py
import logging
from typing import Dict, Any
from akm.infra.network.p2p_service import P2PService
from akm.core.managers.gossip_manager import GossipManager

logging.basicConfig(level=logging.INFO, format='[BaseNode] %(message)s')

class BaseNode:
    """
    [OCP] Nodo de Enrutamiento (Routing Node).
    """
    
    def __init__(self, p2p_service: P2PService, gossip_manager: GossipManager):
        self.p2p = p2p_service
        self.gossip = gossip_manager
        self.p2p.register_handler(self._handle_incoming_message)
        
    def start(self):
        logging.info("🌐 Iniciando Nodo Base (Capa de Red)...")
        self.p2p.start()

    # ⚡ MÉTODO NUEVO REQUERIDO POR EL TEST
    def stop(self):
        logging.info("🛑 Deteniendo servicios de red del nodo...")
        if self.p2p:
            self.p2p.stop()

    def get_peers(self):
        return self.p2p.get_connected_peers()

    def connect_to(self, ip: str, port: int):
        self.p2p.connect_to(ip, port)

    def _handle_incoming_message(self, message: Dict[str, Any], peer_id: str):
        msg_type = message.get("type")
        payload = message.get("payload")
        if not msg_type or not payload: return
        self._process_payload(str(msg_type), payload, peer_id)

    def _process_payload(self, msg_type: str, payload: Dict[str, Any], peer_id: str):
        pass