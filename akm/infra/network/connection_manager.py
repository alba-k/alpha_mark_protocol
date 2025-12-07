# akm/infra/network/connection_manager.py
import socket
import threading
import logging
from typing import Dict, Callable, Optional, List

class ConnectionManager:
    """
    Responsabilidad Única: Gestionar conexiones TCP de bajo nivel (Transport Layer).
    Thread-Safe y protegido contra ataques DoS mediante límites inyectados.
    """
    
    def __init__(
        self, 
        host: str, 
        port: int, 
        max_connections: int,   # Límite inyectado
        max_buffer_size: int,   # Límite inyectado
        on_message_received: Callable[[str, str], None]
    ):
        self.host = host
        self.port = port
        # Inyección de Dependencias: Los límites vienen de fuera (Config)
        self.max_connections = max_connections 
        self.max_buffer_size = max_buffer_size
        
        self.on_message_received = on_message_received
        
        self._server_socket: Optional[socket.socket] = None
        self._peers: Dict[str, socket.socket] = {}
        self._lock = threading.Lock()
        self._running = False
        self._delimiter = b'\n'

    def start_server(self):
        """Inicia el servidor TCP."""
        self._running = True
        t = threading.Thread(target=self._accept_loop, daemon=True)
        t.start()
        logging.info(f"📡 [NET] Servidor TCP activo y escuchando en {self.host}:{self.port}")

    def connect_outbound(self, ip: str, port: int) -> bool:
        """Establece una conexión saliente, respetando el límite de conexiones."""
        peer_id = f"{ip}:{port}"
        
        # 1. Protección de concurrencia y límites
        with self._lock:
            if peer_id in self._peers: return True
            
            if len(self._peers) >= self.max_connections:
                logging.warning(f"[NET] ⚠️ Límite ({self.max_connections}) alcanzado. Rechazando salida a {peer_id}")
                return False

        # 2. Conexión de red
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ip, port))
            sock.settimeout(None)
            
            self._register_peer(sock, peer_id)
            
            logging.info(f"✅ [NET] Conexión saliente exitosa a {peer_id}")
            return True
        except Exception as e:
            logging.error(f"❌ [NET] Fallo al conectar a {peer_id} - {e}")
            return False

    def broadcast(self, data: bytes, exclude_peer: Optional[str] = None):
        """Envía bytes a todos, con delimitador."""
        packet = data + self._delimiter
        
        with self._lock:
            # Copia atómica para iterar sin bloquear
            peers_copy = list(self._peers.items())
        
        for peer_id, sock in peers_copy:
            if exclude_peer and peer_id == exclude_peer:
                continue

            try:
                sock.sendall(packet)
            except Exception:
                logging.warning(f"⚠️ [NET] Error enviando a {peer_id}. Cerrando conexión.")
                self._disconnect(peer_id)

    # 🔥 NUEVO MÉTODO AGREGADO: Envío directo (Unicast)
    def send_direct(self, peer_id: str, data: bytes) -> bool:
        """
        Envía un mensaje directo a un solo peer específico (Unicast).
        Retorna True si se envió, False si falló.
        """
        packet = data + self._delimiter
        
        sock = None
        # Usamos el lock para leer el diccionario de forma segura
        with self._lock:
            sock = self._peers.get(peer_id)
        
        if sock:
            try:
                sock.sendall(packet)
                return True
            except Exception:
                logging.warning(f"⚠️ [NET] Error enviando directo a {peer_id}.")
                self._disconnect(peer_id)
                return False
        
        logging.warning(f"⚠️ [NET] Intento de envío a peer desconocido: {peer_id}")
        return False

    def get_active_peers(self) -> List[str]:
        with self._lock:
            return list(self._peers.keys())

    def stop(self):
        self._running = False
        if self._server_socket:
            try: self._server_socket.close()
            except: pass
        
        with self._lock:
            for peer_id in list(self._peers.keys()):
                self._disconnect(peer_id)

    # --- MÉTODOS INTERNOS (Privados) ---

    def _accept_loop(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind((self.host, self.port))
            server.listen(5)
        except Exception as e:
            logging.critical(f"🔥 [NET] No se pudo abrir el puerto {self.port}: {e}")
            return
        
        while self._running:
            try:
                client, addr = server.accept()
                peer_id = f"{addr[0]}:{addr[1]}"
                
                # Validación de límite en conexiones entrantes
                with self._lock:
                    if len(self._peers) >= self.max_connections:
                        logging.warning(f"[NET] 🚫 Rechazando {peer_id}: Servidor lleno ({self.max_connections}).")
                        client.close()
                        continue

                logging.info(f"🔗 [NET] Nueva conexión entrante desde {peer_id}")
                self._register_peer(client, peer_id)
            except OSError:
                break # Socket cerrado
            except Exception:
                break

    def _register_peer(self, sock: socket.socket, peer_id: str):
        with self._lock:
            self._peers[peer_id] = sock
            
        threading.Thread(target=self._listen_peer, args=(sock, peer_id), daemon=True).start()

    def _listen_peer(self, sock: socket.socket, peer_id: str):
        buffer = b""
        while self._running:
            try:
                data = sock.recv(4096)
                if not data: break
                
                buffer += data
                
                # Protección DoS: Buffer Overflow
                if len(buffer) > self.max_buffer_size:
                    logging.warning(f"[NET] 🛡️ Buffer excedido ({self.max_buffer_size} bytes) por {peer_id}. Desconectando.")
                    break

                while self._delimiter in buffer:
                    message_chunk, buffer = buffer.split(self._delimiter, 1)
                    if message_chunk:
                        # Decodificación segura
                        try:
                            msg_str = message_chunk.decode('utf-8')
                            self.on_message_received(peer_id, msg_str)
                        except UnicodeDecodeError:
                            logging.warning(f"[NET] Mensaje malformado de {peer_id}")
            except Exception:
                break
        
        self._disconnect(peer_id)

    def _disconnect(self, peer_id: str):
        with self._lock:
            if peer_id in self._peers:
                try: self._peers[peer_id].close()
                except: pass
                del self._peers[peer_id]
                logging.info(f"🔌 [NET] Desconectado de {peer_id}")