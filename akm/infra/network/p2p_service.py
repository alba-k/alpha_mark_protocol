# akm/infra/network/p2p_service.py
import json
import logging
import time
from typing import Dict, Any, Callable, Optional, List

# Interfaces y Configuración
from akm.core.interfaces.i_network import INetworkService
from akm.core.config.config_manager import ConfigManager
from akm.core.config.protocol_constants import ProtocolConstants
from akm.infra.network.connection_manager import ConnectionManager

logging.basicConfig(level=logging.INFO, format='[P2P] %(message)s')

class P2PService(INetworkService):
    """
    Servicio de Red P2P.
    Orquesta la comunicación de alto nivel (JSON, Handshake) usando el ConnectionManager.
    """
    
    def __init__(self, config_manager: ConfigManager):
        # 1. Configuración Inyectada
        self.config = config_manager.network
        self.message_handler: Optional[Callable[[Dict[str, Any], str], None]] = None
        
        # 2. Inicializamos ConnectionManager con los límites de seguridad
        self.connection = ConnectionManager(
            host=self.config.host,
            port=self.config.port,
            max_connections=self.config.max_connections, # Inyección
            max_buffer_size=self.config.max_buffer_size, # Inyección
            on_message_received=self._on_bytes_received
        )

    def start(self) -> None:
        """Arranca el servidor y conecta a los nodos semilla."""
        self.connection.start_server()
        
        # Bootstrap: Conectar a seeds
        if self.config.seeds:
            for seed in self.config.seeds:
                if seed:
                    try:
                        ip, port_str = seed.split(":")
                        self.connect_to(ip, int(port_str))
                    except ValueError:
                        logging.error(f"[P2P] Seed inválido: {seed}")

    def connect_to(self, ip: str, port: int) -> bool:
        """Conecta y envía Handshake."""
        if self.connection.connect_outbound(ip, port):
            peer_id = f"{ip}:{port}"
            # 🔥 Iniciar protocolo inmediatamente
            self._send_handshake(peer_id)
            return True
        return False

    def broadcast(self, message: Dict[str, Any], exclude_peer: Optional[str] = None) -> None:
        """Serializa y envía mensaje a todos."""
        try:
            # Añadir timestamp de red para métricas/debug
            message["_net_t"] = int(time.time())
            
            # Serialización segura
            json_bytes = json.dumps(message).encode('utf-8')
            
            self.connection.broadcast(json_bytes, exclude_peer)
            logging.debug(f"📣 Broadcast: {message.get('type')}")
            
        except Exception as e:
            logging.error(f"[P2P] Error broadcast: {e}")

    def register_handler(self, handler: Callable[[Dict[str, Any], str], None]) -> None:
        self.message_handler = handler

    def get_connected_peers(self) -> List[str]:
        return self.connection.get_active_peers()

    def stop(self) -> None:
        self.connection.stop()

    # --- PROTOCOLO INTERNO (Privado) ---

    def _send_handshake(self, peer_id: str):
        """Envía el saludo inicial con versión."""
        handshake_msg: dict[str, Any] = {
            "type": ProtocolConstants.MSG_HANDSHAKE,
            "payload": {
                "version": ProtocolConstants.PROTOCOL_VERSION,
                "agent": ProtocolConstants.USER_AGENT,
                "node_id": f"{self.config.host}:{self.config.port}",
                "timestamp": int(time.time())
            }
        }
        try:
            json_bytes = json.dumps(handshake_msg).encode('utf-8')
            # En esta implementación básica usamos broadcast. 
            # El ConnectionManager se encarga de enviarlo.
            self.connection.broadcast(json_bytes) 
            logging.info(f"🤝 [P2P] Handshake enviado a {peer_id}")
        except Exception as e:
            logging.error(f"[P2P] Error Handshake: {e}")

    def _on_bytes_received(self, peer_id: str, message_str: str):
        """Procesa bytes, deserializa JSON y enruta."""
        try:
            if not message_str.strip(): return

            data = json.loads(message_str)
            
            if "type" not in data:
                logging.warning(f"[P2P] Mensaje sin 'type' de {peer_id}")
                return

            msg_type = data["type"]

            # 1. Intercepción de Protocolo (Handshake)
            if msg_type == ProtocolConstants.MSG_HANDSHAKE:
                logging.info(f"🤝 [P2P] Handshake recibido de {peer_id}: {data.get('payload')}")
                return 

            # 2. Enrutamiento al Negocio (GossipManager)
            if self.message_handler:
                self.message_handler(data, peer_id)
            else:
                logging.debug(f"[P2P] Mensaje {msg_type} recibido sin handler.")
                
        except json.JSONDecodeError:
            logging.warning(f"[P2P] ⚠️ JSON inválido de {peer_id}")
        except Exception as e:
            logging.error(f"[P2P] Error procesando mensaje: {e}")