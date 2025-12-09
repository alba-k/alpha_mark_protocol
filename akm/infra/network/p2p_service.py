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
    Servicio de Red P2P. Orquesta la comunicación de alto nivel.
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager.network
        self.message_handler: Optional[Callable[[Dict[str, Any], str], None]] = None
        
        # 🔥 NUEVO: Callback para obtener la altura de la cadena
        self._height_provider: Optional[Callable[[], int]] = None
        
        self.connection = ConnectionManager(
            host=self.config.host,
            port=self.config.port,
            max_connections=self.config.max_connections, 
            max_buffer_size=self.config.max_buffer_size, 
            on_message_received=self._on_bytes_received
        )

    def set_height_provider(self, provider: Callable[[], int]):
        """Permite al nodo inyectar una función que devuelve la altura actual."""
        self._height_provider = provider

    def start(self) -> None:
        self.connection.start_server()
        
        # Bootstrap: Conectar a seeds
        if self.config.seeds:
            for seed in self.config.seeds:
                if seed:
                    try:
                        ip, port_str = seed.split(":")
                        if int(port_str) != self.config.port:
                            self.connect_to(ip, int(port_str))
                    except ValueError:
                        logging.error(f"[P2P] Seed inválido: {seed}")

    def connect_to(self, ip: str, port: int) -> bool:
        if self.connection.connect_outbound(ip, port):
            peer_id = f"{ip}:{port}"
            self._send_handshake(peer_id)
            return True
        return False

    def broadcast(self, message: Dict[str, Any], exclude_peer: Optional[str] = None) -> None:
        try:
            message["_net_t"] = int(time.time())
            json_bytes = json.dumps(message).encode('utf-8')
            self.connection.broadcast(json_bytes, exclude_peer)
            logging.debug(f"📣 Broadcast: {message.get('type')}")
        except Exception as e:
            logging.error(f"[P2P] Error broadcast: {e}")

    # 🔥 NUEVO: Método para enviar mensajes directos (Unicast)
    def send_message(self, peer_id: str, message: Dict[str, Any]) -> bool:
        """
        [VERIFICADO] Envía un mensaje directo a un peer específico.
        Necesario para SYNC_REQUEST y SYNC_BATCH.
        """
        try:
            json_bytes = json.dumps(message).encode('utf-8')
            return self.connection.send_direct(peer_id, json_bytes)
        except Exception as e:
            logging.error(f"[P2P] Error enviando mensaje directo a {peer_id}: {e}")
            return False

    def register_handler(self, handler: Callable[[Dict[str, Any], str], None]) -> None:
        self.message_handler = handler

    def get_connected_peers(self) -> List[str]:
        return self.connection.get_active_peers()

    def stop(self) -> None:
        self.connection.stop()

    # --- PROTOCOLO INTERNO (Privado) ---

    def _send_handshake(self, peer_id: str):
        """Envía el saludo inicial con versión y altura de bloque."""
        
        # Obtener altura dinámica si está disponible
        current_height = 0
        if self._height_provider:
            current_height = self._height_provider()

        handshake_msg: dict[str, Any] = {
            "type": ProtocolConstants.MSG_HANDSHAKE,
            "payload": {
                "version": ProtocolConstants.PROTOCOL_VERSION,
                "agent": ProtocolConstants.USER_AGENT,
                "height": current_height,  # <--- INFORMACIÓN VITAL PARA SYNC
                "node_id": f"{self.config.host}:{self.config.port}",
                "timestamp": int(time.time())
            }
        }
        try:
            json_bytes = json.dumps(handshake_msg).encode('utf-8')
            
            if not self.connection.send_direct(peer_id, json_bytes):
                logging.error(f"❌ [P2P] Fallo al enviar Handshake a {peer_id}")
            else:
                logging.info(f"🤝 [P2P] Handshake enviado a {peer_id} (Altura: {current_height})")
                
        except Exception as e:
            logging.error(f"[P2P] Error Handshake: {e}")

    def _on_bytes_received(self, peer_id: str, message_str: str):
        """Procesa bytes, deserializa JSON y enruta."""
        try:
            if not message_str.strip(): return

            data = json.loads(message_str)
            
            if "type" not in data: return

            msg_type = data["type"]

            # Interceptamos el Handshake y lo dejamos fluir al FullNode
            if msg_type == ProtocolConstants.MSG_HANDSHAKE:
                logging.info(f"🤝 [P2P] Handshake recibido de {peer_id}: {data.get('payload')}")

            # Enrutamiento al Negocio (FullNode)
            if self.message_handler:
                self.message_handler(data, peer_id)
                
        except json.JSONDecodeError:
            logging.warning(f"[P2P] ⚠️ JSON inválido de {peer_id}")
        except Exception as e:
            logging.error(f"[P2P] Error procesando mensaje: {e}")