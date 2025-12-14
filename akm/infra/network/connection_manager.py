# akm/infra/network/connection_manager.py

import socket
import threading
import logging
from typing import Dict, Callable, Optional, List

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(
        self, 
        host: str, 
        port: int, 
        max_connections: int,
        max_buffer_size: int,
        on_message_received: Callable[[str, str], None]
    ) -> None:
        try:
            self.host = host
            self.port = port
            self.max_connections = max_connections 
            self.max_buffer_size = max_buffer_size
            self.on_message_received = on_message_received
            
            self._server_socket: Optional[socket.socket] = None
            self._peers: Dict[str, socket.socket] = {}
            self._lock = threading.Lock()
            self._running = False
            self._delimiter = b'\n'
            
            logger.info("Gestor de conexiones TCP preparado.")
        except Exception:
            logger.exception("Error al inicializar ConnectionManager")

    def start_server(self) -> None:
        try:
            self._running = True
            threading.Thread(target=self._accept_loop, daemon=True).start()
            logger.info(f"TCPServer: Escuchando en {self.host}:{self.port}")
        except Exception:
            logger.exception("Fallo al arrancar TCPServer")

    def connect_outbound(self, ip: str, port: int) -> bool:
        peer_id = f"{ip}:{port}"
        
        with self._lock:
            if peer_id in self._peers: return True
            if len(self._peers) >= self.max_connections:
                logger.info(f"NET: Límite de pares alcanzado. Rechazando {peer_id}")
                return False

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ip, port))
            sock.settimeout(None)
            
            self._register_peer(sock, peer_id)
            logger.info(f"NET: Conexión saliente exitosa a {peer_id}")
            return True
        except Exception:
            # Aquí no usamos exception para no ensuciar la terminal con fallos de red normales
            logger.info(f"NET: No se pudo conectar a {peer_id}")
            return False

    def broadcast(self, data: bytes, exclude_peer: Optional[str] = None) -> None:
        """Envía datos a toda la red conocida (Gossip)."""
        packet = data + self._delimiter
        
        with self._lock:
            peers_copy = list(self._peers.items())
        
        for peer_id, sock in peers_copy:
            if exclude_peer and peer_id == exclude_peer: continue
            try:
                sock.sendall(packet)
            except Exception:
                logger.info(f"NET: Fallo de envío a {peer_id}. Desconectando.")
                self._disconnect(peer_id)

    def send_direct(self, peer_id: str, data: bytes) -> bool:
        """Envía un mensaje directo a un par específico (Sync/SPV)."""
        packet = data + self._delimiter
        
        with self._lock:
            sock = self._peers.get(peer_id)
        
        if sock:
            try:
                sock.sendall(packet)
                return True
            except Exception:
                logger.info(f"NET: Fallo en envío directo a {peer_id}.")
                self._disconnect(peer_id)
                return False
        return False

    def stop(self) -> None:
        try:
            self._running = False
            if self._server_socket: self._server_socket.close()
            
            with self._lock:
                for peer_id in list(self._peers.keys()):
                    self._disconnect(peer_id)
            logger.info("TCPServer: Servicios detenidos.")
        except Exception:
            logger.exception("Error durante el apagado de red")

    def get_active_peers(self) -> List[str]:
        """Retorna una lista de IDs de peers conectados."""
        with self._lock:
            return list(self._peers.keys())

    # --- MÉTODOS DE FLUJO (Privados) ---

    def _accept_loop(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen(5)
            self._server_socket = server
            
            while self._running:
                client, addr = server.accept()
                peer_id = f"{addr[0]}:{addr[1]}"
                
                with self._lock:
                    if len(self._peers) >= self.max_connections:
                        logger.info(f"NET: Rechazando entrada {peer_id} (Servidor lleno).")
                        client.close()
                        continue

                logger.info(f"NET: +1 Par conectado: {peer_id}")
                self._register_peer(client, peer_id)
        except OSError: pass # Salida normal al cerrar socket
        except Exception:
            logger.exception("Bug en el bucle de aceptación de red")

    def _listen_peer(self, sock: socket.socket, peer_id: str):
        buffer = b""
        while self._running:
            try:
                data = sock.recv(4096)
                if not data: break
                
                buffer += data
                if len(buffer) > self.max_buffer_size:
                    logger.info(f"🛡️ NET: DoS prevenido. Buffer excedido por {peer_id}.")
                    break

                while self._delimiter in buffer:
                    message_chunk, buffer = buffer.split(self._delimiter, 1)
                    if message_chunk:
                        try:
                            self.on_message_received(peer_id, message_chunk.decode('utf-8'))
                        except UnicodeDecodeError:
                            logger.info(f"NET: Mensaje malformado de {peer_id}")
            except Exception:
                break
        self._disconnect(peer_id)

    def _register_peer(self, sock: socket.socket, peer_id: str):
        with self._lock:
            self._peers[peer_id] = sock
        threading.Thread(target=self._listen_peer, args=(sock, peer_id), daemon=True).start()

    def _disconnect(self, peer_id: str):
        with self._lock:
            if peer_id in self._peers:
                try: self._peers[peer_id].close()
                except: pass
                del self._peers[peer_id]
                logger.info(f"NET: -1 Par desconectado: {peer_id}")