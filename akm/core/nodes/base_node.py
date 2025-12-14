# akm/core/nodes/base_node.py

import logging
from typing import Dict, Any, List

# Interfaces
from akm.core.interfaces.i_network import INetworkService

# Gestores
from akm.core.managers.gossip_manager import GossipManager

logger = logging.getLogger(__name__)

class BaseNode:
    
    def __init__(self, network_service: INetworkService, gossip_manager: GossipManager) -> None:
        try:
            self._network = network_service
            self._gossip = gossip_manager
            
            self._network.register_handler(self._handle_incoming_message)
            logger.info("Servicios de Nodo Base inicializados.")
        except Exception:
            logger.exception("Error al inicializar BaseNode")

    def start(self) -> None:
        try:
            logger.info("🌐 Iniciando servicios de red...")
            self._network.start()
        except Exception:
            logger.exception("Fallo crítico al arrancar la red")

    def stop(self) -> None:
        try:
            logger.info("🛑 Deteniendo servicios de red...")
            self._network.stop()
        except Exception:
            logger.exception("Error durante el apagado del nodo")

    def get_peers(self) -> List[str]:
        return self._network.get_connected_peers()

    def connect_to(self, ip: str, port: int) -> bool:
        try:
            logger.info(f"🔗 Conectando a {ip}:{port}...")
            success = self._network.connect_to(ip, port)
            if not success:
                logger.info(f"Fallo de conexión con {ip}:{port}.")
            return success
        except Exception:
            logger.exception(f"Bug intentando conectar a {ip}:{port}")
            return False

    # --- MÉTODOS PROTEGIDOS (Filtros internos) ---

    def _handle_incoming_message(self, message: Dict[str, Any], peer_id: str) -> None:
        """
        Filtro primario de la capa de red.
        Asegura que el mensaje tenga la estructura mínima antes de procesarlo.
        """
        msg_type = message.get("type")
        payload = message.get("payload")
        
        if not msg_type:
            logger.info(f"Mensaje ignorado de {peer_id[:8]}: Sin tipo definido.")
            return

        self._process_payload(str(msg_type), payload, peer_id)

    def _process_payload(self, msg_type: str, payload: Any, peer_id: str) -> None:
        """
        [HOOK] Método gancho para ser sobreescrito por FullNode, MinerNode, etc.
        """
        pass