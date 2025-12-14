# akm/infra/network/p2p_service.py

import json
import logging
import time
from typing import Dict, Any, Callable, Optional, List

# Interfaces
from akm.core.interfaces.i_network import INetworkService

# Configuración y Constantes
from akm.core.config.protocol_constants import ProtocolConstants
from akm.core.config.network_config import NetworkConfig 
from akm.infra.network.connection_manager import ConnectionManager

# Configurar logger local
logger = logging.getLogger(__name__)

class P2PService(INetworkService):
    """
    Implementación concreta del servicio de red P2P.
    Maneja el descubrimiento de pares, handshake y transmisión de mensajes.
    """

    def __init__(self, config: NetworkConfig) -> None:
        try:
            self.config = config
            self.message_handler: Optional[Callable[[Dict[str, Any], str], None]] = None
            self._height_provider: Optional[Callable[[], int]] = None
            
            # Inicialización del transporte de bajo nivel (Sockets/TCP)
            self.connection = ConnectionManager(
                host=self.config.host,
                port=self.config.port,
                max_connections=self.config.max_connections, 
                max_buffer_size=self.config.max_buffer_size, 
                on_message_received=self._on_bytes_received 
            )
            logger.info(f"✅ Servicio P2P inicializado en {self.config.host}:{self.config.port}")
        except Exception as e:
            logger.exception(f"❌ Error crítico al inicializar P2PService: {e}")
            raise e

    def set_height_provider(self, provider: Callable[[], int]) -> None:
        """Define la función callback para obtener la altura actual de la cadena."""
        self._height_provider = provider

    def start(self) -> None:
        """Inicia el servidor y conecta a los seeds."""
        try:
            self.connection.start_server()
            
            if self.config.seeds:
                logger.info(f"🌍 P2P: Iniciando descubrimiento con {len(self.config.seeds)} seeds.")
                for seed in self.config.seeds:
                    try:
                        # Formato esperado "IP:PORT"
                        parts = seed.split(":")
                        if len(parts) == 2:
                            ip, port_str = parts
                            # Evitar auto-conexión
                            if int(port_str) != self.config.port:
                                self.connect_to(ip, int(port_str))
                    except ValueError:
                        logger.warning(f"⚠️ Seed con formato inválido ignorado: {seed}")
        except Exception:
            logger.exception("Error durante el arranque del servicio P2P")

    def connect_to(self, ip: str, port: int) -> bool:
        """Intenta establecer una conexión saliente."""
        try:
            if self.connection.connect_outbound(ip, port):
                peer_id = f"{ip}:{port}"
                # Iniciar protocolo de Handshake inmediatamente después de conectar
                self._send_handshake(peer_id)
                return True
            return False
        except Exception as e:
            logger.error(f"Error al conectar con {ip}:{port} -> {e}")
            return False

    def broadcast(self, message: Dict[str, Any], exclude_peer: Optional[str] = None) -> None:
        """Envía un mensaje a todos los pares conectados, excepto al excluido."""
        try:
            # Añadir timestamp de red para depuración/métricas
            if "_net_t" not in message:
                message["_net_t"] = int(time.time())
            
            json_bytes = json.dumps(message).encode('utf-8')
            self.connection.broadcast(json_bytes, exclude_peer)
        except Exception:
            logger.exception("Fallo técnico en broadcast P2P")

    def send_message(self, peer_id: str, message: Dict[str, Any]) -> bool:
        """Envía un mensaje directo a un par específico."""
        try:
            json_bytes = json.dumps(message).encode('utf-8')
            return self.connection.send_direct(peer_id, json_bytes)
        except Exception:
            logger.exception(f"Error serializando mensaje para {peer_id}")
            return False

    def register_handler(self, handler: Callable[[Dict[str, Any], str], None]) -> None:
        """Registra el callback principal para procesar mensajes entrantes."""
        self.message_handler = handler

    def get_connected_peers(self) -> List[str]:
        return self.connection.get_active_peers()

    def stop(self) -> None:
        try:
            self.connection.stop()
            logger.info("🛑 P2P: Servicio detenido.")
        except Exception:
            logger.exception("Error al detener P2PService")

    # --- PROTOCOLO DE RED (Privado) ---

    def _send_handshake(self, peer_id: str) -> None:
        """Envía el mensaje inicial de versión/handshake."""
        try:
            height = self._height_provider() if self._height_provider else 0
            msg: Dict[str, Any] = {
                "type": ProtocolConstants.MSG_HANDSHAKE,
                "payload": {
                    "version": ProtocolConstants.PROTOCOL_VERSION,
                    "height": height,
                    "node_id": f"{self.config.host}:{self.config.port}",
                    "timestamp": int(time.time())
                }
            }
            # Usar send_direct internamente evita recursión innecesaria
            json_bytes = json.dumps(msg).encode('utf-8')
            if self.connection.send_direct(peer_id, json_bytes):
                logger.debug(f"🤝 Handshake enviado a {peer_id}.")
        except Exception:
            logger.exception(f"Fallo enviando Handshake a {peer_id}")

    def _on_bytes_received(self, peer_id: str, message_str: str) -> None:
        """Callback invocado por ConnectionManager cuando llegan bytes."""
        try:
            if not message_str or not message_str.strip():
                return
            
            data = json.loads(message_str)
            msg_type = data.get("type")
            
            if not msg_type:
                return

            # Manejo interno del Handshake (logging)
            if msg_type == ProtocolConstants.MSG_HANDSHAKE:
                p = data.get('payload', {})
                logger.info(f"🤝 Handshake recibido de {peer_id} | Altura: {p.get('height')} | Ver: {p.get('version')}")
                # Nota: Aquí se podría añadir lógica para rechazar versiones incompatibles

            # Delegar al manejador superior (GossipManager/SyncManager/Node)
            if self.message_handler:
                self.message_handler(data, peer_id)
                
        except json.JSONDecodeError:
            logger.warning(f"🗑️ P2P: JSON inválido recibido de {peer_id}.")
        except Exception:
            logger.exception(f"🔥 Error procesando mensaje de {peer_id}")

    