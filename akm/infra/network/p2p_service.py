# akm/infra/network/p2p_service.py

import json
import logging
import time
import socket
from typing import Dict, Any, Callable, Optional, List, cast, Set

# Interfaces
from akm.core.interfaces.i_network import INetworkService

# Configuración y Constantes
from akm.core.config.protocol_constants import ProtocolConstants
from akm.core.config.network_config import NetworkConfig 
from akm.infra.network.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

class NetworkEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if hasattr(o, 'to_dict'):
            return o.to_dict()
        if isinstance(o, bytes):
            return o.hex()
        if isinstance(o, set):
            return list(cast(Set[Any], o))
        return super().default(o)

class P2PService(INetworkService):
    
    def __init__(self, config: NetworkConfig, agent_name: str = "AlphaMark/Unknown:0.0.1") -> None:
        try:
            self._config = config
            self._agent_name = agent_name
            self._message_handler: Optional[Callable[[Dict[str, Any], str], None]] = None
            self._height_provider: Optional[Callable[[], int]] = None
            
            self._connection = ConnectionManager(
                host=self._config.host,
                port=self._config.port,
                max_connections=self._config.max_connections, 
                max_buffer_size=self._config.max_buffer_size, 
                on_message_received=self._on_message_received 
            )
            
            self._advertised_host = self._resolve_advertised_host()
            
            logger.info(f"✅ P2PService listo. ID: {self._advertised_host}:{self._config.port} | Agente: {self._agent_name}")
            
        except Exception as e:
            logger.critical(f"❌ Error fatal iniciando P2PService: {e}")
            raise

    # ---------------------------------------------------------
    # 👇 SOLUCIÓN: Agrega esta propiedad para exponer _config
    # ---------------------------------------------------------
    @property
    def config(self) -> NetworkConfig:
        return self._config
    # ---------------------------------------------------------

    def set_height_provider(self, provider: Callable[[], int]) -> None:
        self._height_provider = provider

    def register_handler(self, handler: Callable[[Dict[str, Any], str], None]) -> None:
        self._message_handler = handler

    def start(self) -> None:
        try:
            self._connection.start_server()
            if self._config.seeds:
                logger.info(f"🌍 Iniciando descubrimiento de red ({len(self._config.seeds)} seeds config).")
                self._connect_to_seeds()
        except Exception:
            logger.exception("Error arrancando servicio P2P")

    def stop(self) -> None:
        self._connection.stop()
        logger.info("🛑 P2PService detenido.")

    def connect_to(self, ip: str, port: int) -> bool:
        try:
            if ip in ["127.0.0.1", "localhost", "0.0.0.0"] and port == self._config.port:
                return False

            if self._connection.connect_outbound(ip, port):
                peer_id = f"{ip}:{port}"
                self._send_handshake(peer_id)
                return True
            return False
        except Exception as e:
            logger.warning(f"Fallo conectando a {ip}:{port} - {e}")
            return False

    def broadcast(self, message: Dict[str, Any], exclude_peer: Optional[str] = None) -> None:
        try:
            if "_net_t" not in message:
                message["_net_t"] = int(time.time())
            payload_bytes = self._serialize(message)
            self._connection.broadcast(payload_bytes, exclude_peer)
        except Exception:
            logger.error("Error en broadcast P2P", exc_info=True)

    def send_message(self, peer_id: str, message: Dict[str, Any]) -> bool:
        try:
            payload_bytes = self._serialize(message)
            return self._connection.send_direct(peer_id, payload_bytes)
        except Exception:
            logger.error(f"Error enviando mensaje directo a {peer_id}", exc_info=True)
            return False

    def get_connected_peers(self) -> List[str]:
        return self._connection.get_active_peers()

    def _connect_to_seeds(self):
        for seed in self._config.seeds:
            try:
                if ":" not in seed: continue
                ip, port_str = seed.split(":")
                port = int(port_str)
                if port != self._config.port:
                    self.connect_to(ip, port)
            except ValueError:
                pass

    def _send_handshake(self, peer_id: str) -> None:
        """Protocolo: HANDSHAKE con IDENTIDAD INYECTADA."""
        try:
            current_height = self._height_provider() if self._height_provider else 0
            
            msg: Dict[str, Any] = {
                "type": ProtocolConstants.MSG_HANDSHAKE,
                "payload": {
                    "version": ProtocolConstants.PROTOCOL_VERSION,
                    "height": current_height,
                    "node_id": f"{self._advertised_host}:{self._config.port}",
                    "agent": self._agent_name, 
                    "timestamp": int(time.time())
                }
            }
            
            payload_bytes = self._serialize(msg)
            if self._connection.send_direct(peer_id, payload_bytes):
                logger.debug(f"🤝 Handshake enviado a {peer_id} (Soy: {self._agent_name})")
                
        except Exception:
            logger.error(f"Fallo crítico enviando Handshake a {peer_id}")

    def _on_message_received(self, peer_id: str, message_str: str) -> None:
        try:
            if not message_str: return
            data = json.loads(message_str)
            msg_type = data.get("type")
            if not msg_type: return

            if msg_type == ProtocolConstants.MSG_HANDSHAKE:
                self._handle_handshake_log(data, peer_id)

            if self._message_handler:
                self._message_handler(data, peer_id)
                
        except json.JSONDecodeError:
            logger.warning(f"🗑️ JSON corrupto recibido de {peer_id}")
        except Exception as e:
            logger.error(f"Error procesando mensaje de {peer_id}: {e}")

    def _handle_handshake_log(self, data: Dict[str, Any], peer_id: str):
        payload = data.get('payload', {})
        remote_height = payload.get('height', '?')
        remote_agent = payload.get('agent', payload.get('node_id', 'Unknown'))
        
        logger.info(f"🤝 CONEXIÓN ESTABLECIDA con [{remote_agent}] ({peer_id}) | Altura: {remote_height}")

    def _serialize(self, data: Dict[str, Any]) -> bytes:
        return json.dumps(data, cls=NetworkEncoder).encode('utf-8')

    def _resolve_advertised_host(self) -> str:
        host = self._config.host
        if host == "0.0.0.0":
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(0)
                try:
                    s.connect(('8.8.8.8', 1))
                    ip = s.getsockname()[0]
                except Exception:
                    ip = "127.0.0.1"
                finally:
                    s.close()
                return ip
            except Exception:
                return "127.0.0.1"
        return host