# src/node.py
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional, Any

# --- API INTEGRATION IMPORTS ---
import uvicorn
from akm.interface.api.server import app 
from akm.interface.api.config import settings as api_settings 
from akm.interface.api import dependencies as api_dependencies # El módulo para inyectar dependencias
# ------------------------------

# 1. Configuración
from akm.core.config.config_manager import ConfigManager
# 2. Fábrica
from akm.core.factories.node_factory import NodeFactory

class NodeDashboard(BaseHTTPRequestHandler):
    node_ref: Optional['Node'] = None 

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        # Datos en tiempo real
        altura = 0
        peers = 0
        tipo = "..."
        
        if self.node_ref and hasattr(self.node_ref, 'core_node'):
            try:
                core: Any = self.node_ref.core_node
                
                if hasattr(core, 'blockchain'):
                    altura = core.blockchain.height
                elif hasattr(core, 'header_chain'):
                    altura = core.header_chain.height
                
                if hasattr(core, 'p2p_service'):
                    peers = len(core.p2p_service.get_connected_peers())
                
                tipo = self.node_ref.config_manager.node_type
            except Exception:
                pass

        html = f"""
        <html>
        <head>
            <title>AKM Dashboard</title>
            <meta http-equiv="refresh" content="5">
        </head>
        <body style="font-family: Arial; background: #34495e; color: white; text-align: center; padding: 50px;">
            <div style="background: white; color: #333; padding: 30px; border-radius: 10px; display: inline-block; min-width: 300px;">
                <h1 style="color: #16a085;">AKM {tipo} NODE</h1>
                <hr>
                <div style="font-size: 24px; margin: 20px 0;">
                    <p>📦 Altura: <strong>{altura}</strong></p>
                    <p>🔗 Peers: <strong>{peers}</strong></p>
                </div>
                <small>Dashboard Ligero</small>
            </div>
        </body>
        </html>
        """
        self.wfile.write(bytes(html, "utf-8"))

    def log_message(self, format: str, *args: Any) -> None: return 

class Node:
    def __init__(self) -> None:
        # 1. Configuración
        self.config_manager = ConfigManager()
        
        # 2. Asignación Inteligente de Puertos Web (Dashboard)
        node_type = self.config_manager.node_type
        if node_type == "FULL":
            self.web_port = 8000
        elif node_type == "LIGHT":
            self.web_port = 8001
        elif node_type == "MINER":
            self.web_port = 8002
        else:
            self.web_port = 8080
        
        # 3. Ensamblaje del Núcleo Correcto
        print(f"[INIT] 🏭 Ensamblando nodo tipo {node_type}...")
        
        self.core_node: Any = None

        if node_type == "FULL":
            self.core_node = NodeFactory.create_full_node()
        elif node_type == "MINER":
            self.core_node = NodeFactory.create_miner_node()
        elif node_type == "LIGHT":
            self.core_node = NodeFactory.create_spv_node()
        else:
            print(f"[WARN] Tipo desconocido {node_type}, usando FULL por defecto.")
            self.core_node = NodeFactory.create_full_node()
            
        # 🔥 CRÍTICO: INYECCIÓN DE DEPENDENCIA CORREGIDA
        # Usamos el método set_instance() de NodeContainer
        api_dependencies.NodeContainer.set_instance(self.core_node)
            
    # --- MÉTODO NUEVO: Iniciar Servidor API ---
    def _start_api_server(self) -> None:
        """Lanza el servidor FastAPI/Uvicorn en un hilo separado."""
        
        # 🔥 CORRECCIÓN FINAL: Cálculo dinámico para evitar colisión de puertos API
        base_p2p_port = 9333  # Puerto base del Full Node
        base_api_port = 8080  # Puerto base de la API
        
        # dynamic_api_port: 8080 (Full), 8081 (Miner), 8082 (Light)
        port_offset = self.config_manager.network.port - base_p2p_port
        dynamic_api_port = base_api_port + port_offset
        
        host = api_settings.host

        print(f"🌐 [API] Servidor listo en: http://{host}:{dynamic_api_port}")

        # Iniciar Uvicorn
        uvicorn.run(
            app, 
            host=host, 
            port=dynamic_api_port, # Usamos el puerto calculado
            log_level="warning"
        )
        
    def iniciar_dashboard(self) -> None:
        NodeDashboard.node_ref = self 
        try:
            server = HTTPServer(("localhost", self.web_port), NodeDashboard)
            print(f"[WEB] Dashboard: http://localhost:{self.web_port}")
            server.serve_forever()
        except OSError:
            print(f"[WEB] Puerto {self.web_port} ocupado. Intenta cerrar otros nodos.")

    def start(self) -> None:
        print(f"\n[SISTEMA] Arrancando Motor P2P en puerto {self.config_manager.network.port}...")
        
        # 1. Arrancar servicios de Red (P2P)
        if self.core_node:
            self.core_node.start() 
        
        # 2. Arrancar Servidor API (para Transacciones)
        api_thread = threading.Thread(target=self._start_api_server, daemon=True)
        api_thread.start()
        
        # 3. Dashboard
        dashboard_thread = threading.Thread(target=self.iniciar_dashboard, daemon=True)
        dashboard_thread.start()

        print(f">>> NODO {self.config_manager.node_type} OPERATIVO <<<")
        try:
            while True:
                time.sleep(1) 
        except KeyboardInterrupt:
            print("\n[SHUTDOWN] Deteniendo servicios...")
            if self.core_node:
                self.core_node.stop()