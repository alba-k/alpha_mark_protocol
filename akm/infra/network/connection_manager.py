# akm/infra/network/connection_manager.py

import socket
import threading
import logging
from typing import Dict, Callable, Optional, List

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Gestor de Transporte TCP de Bajo Nivel.
    
    Responsabilidad (SRP): Manejar sockets, conexiones, bufferes y streaming de bytes.
    No conoce nada sobre el protocolo de aplicación (Handshakes, Bloques, etc), 
    solo entrega mensajes de texto limpios.
    """

    def __init__(
        self, 
        host: str, 
        port: int, 
        max_connections: int,
        max_buffer_size: int,
        on_message_received: Callable[[str, str], None]
    ) -> None:
        """
        Inicializa el gestor de conexiones.

        :param on_message_received: Callback (peer_id, mensaje_str) -> None.
        """
        self._host = host
        self._port = port
        self._max_connections = max_connections 
        self._max_buffer_size = max_buffer_size
        self._on_message_received = on_message_received
        
        # Estado Interno Protegido
        self._server_socket: Optional[socket.socket] = None
        self._peers: Dict[str, socket.socket] = {}
        self._lock = threading.RLock() # Reentrant lock es más seguro para métodos anidados
        self._running = False
        self._delimiter = b'\n' # Protocolo delimitado por líneas (Line-based JSON)
        
        logger.info(f"✅ ConnectionManager inicializado. Config: MaxConn={max_connections}, Buffer={max_buffer_size}B")

    # --- Propiedades Públicas (Encapsulamiento) ---
    
    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    # --- Ciclo de Vida ---

    def start_server(self) -> None:
        """Inicia el socket servidor en un hilo demonio."""
        if self._running:
            logger.warning("TCPServer ya está corriendo.")
            return

        try:
            self._running = True
            thread = threading.Thread(target=self._accept_loop, daemon=True, name="TCPAcceptLoop")
            thread.start()
            logger.info(f"🚀 TCPServer escuchando en {self._host}:{self._port}")
        except Exception:
            self._running = False
            logger.exception("❌ Fallo crítico al arrancar TCPServer")
            raise

    def stop(self) -> None:
        """Detiene el servidor y cierra todas las conexiones activas."""
        logger.info("🛑 Deteniendo servicios de red...")
        self._running = False
        
        # 1. Cerrar socket servidor para desbloquear accept()
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception as e:
                logger.warning(f"Error cerrando server socket: {e}")
            self._server_socket = None
            
        # 2. Desconectar a todos los pares
        with self._lock:
            active_peers = list(self._peers.keys())
            for peer_id in active_peers:
                self._disconnect(peer_id, reason="Shutdown del nodo")
        
        logger.info("✅ Servicios de red detenidos correctamente.")

    # --- Gestión de Conexiones ---

    def connect_outbound(self, ip: str, port: int) -> bool:
        """Establece una conexión saliente (Cliente -> Servidor)."""
        peer_id = f"{ip}:{port}"
        
        # Verificación de estado y límites
        with self._lock:
            if peer_id in self._peers:
                return True # Ya conectado
            if len(self._peers) >= self._max_connections:
                logger.debug(f"NET: Límite de conexiones alcanzado. No se puede conectar a {peer_id}")
                return False

        try:
            # Configuración del Socket Cliente
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0) # Timeout para el handshake TCP inicial
            
            # Conexión
            sock.connect((ip, port))
            
            # Post-Conexión: Configurar socket para modo streaming
            sock.settimeout(None) # Modo bloqueante para el loop de lectura
            self._configure_socket(sock)
            
            self._register_peer(sock, peer_id, inbound=False)
            logger.info(f"🔗 Conexión SALIENTE exitosa: {peer_id}")
            return True

        except (socket.timeout, ConnectionRefusedError):
            # Errores comunes, logging nivel bajo
            logger.debug(f"NET: No se pudo conectar a {peer_id} (Timeout/Refused)")
            return False
        except Exception as e:
            logger.warning(f"NET: Error de conexión con {peer_id}: {e}")
            return False

    def broadcast(self, data: bytes, exclude_peer: Optional[str] = None) -> None:
        """Envía datos crudos a todos los pares conectados."""
        packet = data + self._delimiter
        
        # Copia superficial para iterar sin bloquear el lock mucho tiempo
        with self._lock:
            peers_copy = list(self._peers.items())
        
        for peer_id, sock in peers_copy:
            if exclude_peer and peer_id == exclude_peer:
                continue
            
            self._send_packet_safe(sock, peer_id, packet)

    def send_direct(self, peer_id: str, data: bytes) -> bool:
        """Envía datos crudos a un par específico."""
        packet = data + self._delimiter
        
        with self._lock:
            sock = self._peers.get(peer_id)
        
        if sock:
            return self._send_packet_safe(sock, peer_id, packet)
        
        logger.debug(f"NET: Intento de envío a par desconectado {peer_id}")
        return False

    def get_active_peers(self) -> List[str]:
        with self._lock:
            return list(self._peers.keys())

    # --- Internals & Threading ---

    def _configure_socket(self, sock: socket.socket) -> None:
        """
        Aplica optimizaciones de socket para P2P.
        TCP_NODELAY: Desactiva algoritmo Nagle para menor latencia en mensajes pequeños.
        SO_KEEPALIVE: Mantiene la conexión viva y detecta caídas.
        """
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except Exception:
            logger.warning("No se pudieron establecer opciones avanzadas de socket.")

    def _send_packet_safe(self, sock: socket.socket, peer_id: str, packet: bytes) -> bool:
        """Envío seguro con manejo de errores centralizado."""
        try:
            sock.sendall(packet)
            return True
        except Exception:
            logger.warning(f"NET: Error enviando a {peer_id}. Cerrando conexión.")
            self._disconnect(peer_id, reason="Fallo de escritura")
            return False

    def _accept_loop(self):
        """Bucle principal de aceptación de conexiones entrantes."""
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self._host, self._port))
            server.listen(5)
            self._server_socket = server
            
            while self._running:
                try:
                    client, addr = server.accept()
                    peer_id = f"{addr[0]}:{addr[1]}"
                    
                    with self._lock:
                        if len(self._peers) >= self._max_connections:
                            logger.info(f"NET: Rechazando {peer_id} (Servidor lleno).")
                            client.close()
                            continue
                    
                    self._configure_socket(client)
                    logger.info(f"🔌 Conexión ENTRANTE aceptada: {peer_id}")
                    self._register_peer(client, peer_id, inbound=True)
                    
                except OSError:
                    # Ocurre normalmente al cerrar el socket servidor desde stop()
                    if self._running:
                        logger.error("Error en accept()", exc_info=True)
                    break
                    
        except Exception:
            logger.exception("Crash en bucle de aceptación")

    def _register_peer(self, sock: socket.socket, peer_id: str, inbound: bool):
        with self._lock:
            self._peers[peer_id] = sock
        
        # Iniciar hilo de escucha dedicado para este par
        thread_name = f"Reader-{peer_id}"
        threading.Thread(target=self._listen_peer, args=(sock, peer_id), daemon=True, name=thread_name).start()

    def _listen_peer(self, sock: socket.socket, peer_id: str):
        """
        Bucle de lectura robusto.
        Soluciona la fragmentación TCP y aísla errores de aplicación.
        """
        buffer = b""
        chunk_size = 4096
        
        try:
            while self._running:
                try:
                    data = sock.recv(chunk_size)
                    if not data:
                        logger.info(f"NET: Fin de conexión por {peer_id}")
                        break
                    
                    buffer += data
                    
                    # 🛡️ Protección Anti-DoS (Buffer Overflow)
                    if len(buffer) > self._max_buffer_size:
                        logger.warning(f"🛡️ DoS detectado: {peer_id} excedió límite de buffer ({len(buffer)} bytes).")
                        break

                    # Procesamiento de tramas completas
                    while self._delimiter in buffer:
                        # 1. Split Binario (Seguro)
                        message_chunk, buffer = buffer.split(self._delimiter, 1)
                        
                        if not message_chunk:
                            continue # Líneas vacías (KeepAlive implícito)

                        # 2. Decodificación (Solo cuando tenemos la trama completa)
                        try:
                            decoded_msg = message_chunk.decode('utf-8')
                        except UnicodeDecodeError:
                            logger.error(f"🗑️ Trama corrupta (No UTF-8) de {peer_id}")
                            continue # Ignoramos la trama mala, pero mantenemos conexión (opcional)

                        # 3. Entrega a Capa Superior (Aislado de errores de negocio)
                        try:
                            self._on_message_received(peer_id, decoded_msg)
                        except Exception as e:
                            # CRÍTICO: Si la app falla procesando el mensaje, NO desconectamos al par.
                            logger.error(f"⚠️ Error de aplicación procesando mensaje de {peer_id}: {e}", exc_info=False)
                            
                except ConnectionResetError:
                    logger.info(f"NET: Conexión reseteada por {peer_id}")
                    break
                except Exception as e:
                    logger.error(f"NET: Error de socket leyendo de {peer_id}: {e}")
                    break
                    
        finally:
            self._disconnect(peer_id, reason="Fin de bucle de lectura")

    def _disconnect(self, peer_id: str, reason: str = "Desconocida"):
        """Cierra la conexión y limpia recursos de manera atómica."""
        with self._lock:
            if peer_id in self._peers:
                sock = self._peers.pop(peer_id)
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()
                except Exception:
                    pass # Socket probablemente ya cerrado
                logger.info(f"💔 Par desconectado: {peer_id} | Motivo: {reason}")