import os
import time
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Any, Optional

# --- CLASE PARA EL SERVIDOR WEB (DASHBOARD) ---
class NodeDashboard(BaseHTTPRequestHandler):
    # TIPADO: Definimos que esta variable puede ser un objeto 'Node' O puede ser None.
    # Usamos comillas 'Node' porque la clase Node aún no se ha leído (Forward Reference).
    node_ref: Optional['Node'] = None 

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        # Leemos el estado actual del nodo de forma segura
        estado: str = "DESCONOCIDO"
        
        # TIPADO: Python ahora sabe que si node_ref existe, tiene un atributo .node_type
        if self.node_ref:
            estado = self.node_ref.node_type

        # Datos seguros (si es None, ponemos '...')
        puerto_display = self.node_ref.port if self.node_ref else '...'
        dir_display = self.node_ref.data_dir if self.node_ref else '...'

        # Creamos una página web simple en HTML
        html = f"""
        <html>
        <head><title>AKM Dashboard</title></head>
        <body style="font-family: Arial; background-color: #f0f0f0; text-align: center; padding: 50px;">
            <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); display: inline-block;">
                <h1 style="color: #2c3e50;">ALPHA MARK PROTOCOL</h1>
                <hr>
                <h2>Estado del Nodo: <span style="color: green;">EN LINEA</span></h2>
                <p><strong>Tipo:</strong> {estado}</p>
                <p><strong>Puerto P2P:</strong> {puerto_display}</p>
                <p><strong>Directorio de Datos:</strong> {dir_display}</p>
                <br>
                <button onclick="location.reload()">Actualizar Estado</button>
            </div>
        </body>
        </html>
        """
        self.wfile.write(bytes(html, "utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        return # Silenciar logs

# --- TU CLASE NODO ORIGINAL (AHORA CON TIPADO) ---
class Node:
    # TIPADO: Exigimos que config sea un diccionario
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config: Dict[str, Any] = config
        
        # Validamos que lo que sacamos del diccionario sea texto o usemos un default
        self.node_type: str = str(config.get("node_type", "FULL"))
        
        # Aquí asumimos que estos datos existen en el config (podría dar error si falta en el JSON)
        self.port: int = int(config["network"]["p2p_port"])
        self.data_dir: str = str(config["storage"]["data_dir"])
        
        # Configuración del Dashboard Web
        # Lógica matemática simple
        self.web_port: int = 8000 + (1 if self.node_type == "LIGHT" else 0)

    def iniciar_dashboard(self) -> None:
        """Inicia el servidor web en un hilo separado"""
        # Conectamos las clases
        NodeDashboard.node_ref = self 
        
        server = HTTPServer(("localhost", self.web_port), NodeDashboard)
        print(f"[WEB] Dashboard disponible en: http://localhost:{self.web_port}")
        
        # Abrir navegador automáticamente
        webbrowser.open(f"http://localhost:{self.web_port}")
        
        server.serve_forever()

    def start(self) -> None:
        print(f"\n[SISTEMA] Arrancando NODO tipo: {self.node_type}")
        
        # 1. Iniciamos el Dashboard en paralelo
        hilo_web = threading.Thread(target=self.iniciar_dashboard)
        hilo_web.daemon = True 
        hilo_web.start()

        # 2. Lógica normal del nodo
        if self.node_type == "LIGHT":
            print(">>> MODO LIGERO ACTIVADO <<<")
        else:
            print(">>> MODO FULL NODE ACTIVADO <<<")

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        print("[INFO] Nodo operativo. Mira tu navegador.\n")
        try:
            # Tipado: Este bucle no retorna nada, corre por siempre
            while True:
                time.sleep(1) 
        except KeyboardInterrupt:
            print("Deteniendo nodo...")