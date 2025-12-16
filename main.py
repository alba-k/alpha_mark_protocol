import os
import sys
import json
import argparse
import logging
import time

# Importamos uvicorn para el servidor API (Solo se usa en modo SPV)
import uvicorn

from typing import Any

# =========================================================
# ⚡ CONFIGURACIÓN INICIAL DEL SISTEMA
# =========================================================

# 1. Forzar UTF-8 en la consola de Windows (Emojis)
sys.stdout.reconfigure(encoding='utf-8') # type: ignore
sys.stderr.reconfigure(encoding='utf-8') # type: ignore

# 2. Configuración de Logs (Safe Import)
logger_config = None
try:
    import logger_config
except ImportError:
    pass  # Se manejará más abajo

if logger_config:
    logger_config.setup_logging()
else:
    # Fallback si no existe logger_config.py
    print("⚠️ ADVERTENCIA: logger_config.py no encontrado. Usando logs básicos.")
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# 3. Obtener el logger raíz ya configurado
logger = logging.getLogger()

# 4. Configurar el Path del Proyecto
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

# --- IMPORTS DEL CORE (Después de configurar el path) ---
from akm.core.config.paths import Paths
from akm.core.factories.node_factory import NodeFactory

# =========================================================
# 🛠️ FUNCIONES DE UTILIDAD
# =========================================================

def load_config(config_name: str) -> dict[str, Any]:
    """Carga el archivo JSON de configuración."""
    config_path = os.path.join(ROOT_DIR, 'config', config_name)
    
    if not os.path.exists(config_path):
        if os.path.exists(config_name):
            config_path = config_name
        else:
            logger.critical(f"❌ No existe el archivo de configuración: {config_path}")
            sys.exit(1)
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.critical(f"❌ JSON Corrupto en {config_name}: {e}")
        sys.exit(1)

def inject_environment(config: dict[str, Any], instance_name: str, overrides: dict[str, Any]):
    """Inyecta la configuración en Variables de Entorno."""
    logger.info(f"🔧 Configurando entorno para: {instance_name}")

    os.environ["AKM_INSTANCE_NAME"] = instance_name
    os.environ["AKM_NODE_ROLE"] = config.get("role", "FULL_NODE")
    
    data_dir = os.path.join(ROOT_DIR, "data", instance_name)
    os.environ["AKM_DATA_DIR"] = data_dir
    
    Paths.ensure_directories_exist()
    
    net = config.get("network", {})
    
    # ==============================================================================
    # 🛠️ CORRECCIÓN CRÍTICA DE RED
    # Forzamos "0.0.0.0" para que Windows no cierre el programa por error de IP.
    # Ignoramos lo que diga el archivo JSON en 'p2p_host'.
    # ==============================================================================
    # os.environ["AKM_P2P_HOST"] = net.get("p2p_host", "0.0.0.0")  <-- LÍNEA ORIGINAL COMENTADA
    os.environ["AKM_P2P_HOST"] = "0.0.0.0"                        # <-- NUEVA LÍNEA FORZADA
    # ==============================================================================

    p2p_port = overrides.get("p2p_port") or net.get("p2p_port_default", 5000)
    os.environ["AKM_P2P_PORT"] = str(p2p_port)

    seeds = overrides.get("seeds")
    if not seeds:
        seeds_list = net.get("seeds", [])
        seeds = ",".join(seeds_list)
    os.environ["AKM_SEEDS"] = seeds

    cons = config.get("consensus", {})
    os.environ["AKM_MINING_ENABLED"] = str(cons.get("mining_enabled", False))
    os.environ["AKM_MINER_ADDRESS"] = cons.get("miner_address", "")
    
    pers = config.get("persistence", {})
    os.environ["AKM_STORAGE_ENGINE"] = pers.get("engine", "sqlite")
    os.environ["AKM_DB_NAME"] = pers.get("db_name", "blockchain.db")

    api = config.get("api", {})
    os.environ["AKM_API_HOST"] = api.get("host", "0.0.0.0")
    api_port = overrides.get("api_port") or api.get("port_default", 8000)
    os.environ["AKM_API_PORT"] = str(api_port)

    return api_port

def run_headless_node(role: str):
    """
    Arranca un nodo de infraestructura (Full Node o Minero) en modo silencioso.
    """
    node = None
    try:
        print("\n" + "="*60)
        print(f"🏭 INICIANDO INFRAESTRUCTURA REAL ({role})")
        print("   (Modo Headless: Sin API, Solo P2P y Consenso)")
        if logger_config:
            print(f"   📝 Revisa la carpeta 'data/logs' para ver la actividad.")
        print("="*60 + "\n")

        node = NodeFactory.create_node(role)
        
        if hasattr(node, 'start'):
            node.start()
        
        logger.info(f"✅ Nodo {role} corriendo exitosamente.")
        print(f"✅ Nodo {role} activo. Presiona Ctrl+C para detener.")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("🛑 Deteniendo nodo por solicitud del usuario...")
        if node and hasattr(node, 'stop'):
            node.stop()
        print("\n👋 Nodo detenido correctamente.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"❌ Error fatal en el nodo: {e}", exc_info=True)
        sys.exit(1)

# =========================================================
# 🚀 ENTRY POINT PRINCIPAL
# =========================================================

def main():
    parser = argparse.ArgumentParser(description="Lanzador Alpha Mark Protocol")
    
    parser.add_argument("config", help="Nombre del archivo JSON en config/")
    parser.add_argument("--name", required=True, help="Nombre único de la instancia")
    parser.add_argument("--p2p", type=int, help="Forzar puerto P2P")
    parser.add_argument("--api", type=int, help="Forzar puerto API (Solo SPV)")
    parser.add_argument("--seeds", type=str, help="Lista de seeds")

    args = parser.parse_args()

    config_data = load_config(args.config)
    
    overrides = {
        "p2p_port": args.p2p, 
        "api_port": args.api, 
        "seeds": args.seeds
    }
    final_api_port = inject_environment(config_data, args.name, overrides)

    role = os.environ["AKM_NODE_ROLE"]

    if role == "SPV_NODE":
        # --- MODO CLIENTE (WALLET) ---
        print("\n" + "="*60)
        print(f"📱 INICIANDO CLIENTE SPV (WALLET): {args.name}")
        print(f"🌐 API Disponible en: http://0.0.0.0:{final_api_port}")
        print("="*60 + "\n")
        
        uvicorn.run(
            "akm.interface.api.server:app", 
            host="0.0.0.0", 
            port=final_api_port, 
            log_level="info"
        )
    
    else:
        # --- MODO INFRAESTRUCTURA (SERVER) ---
        run_headless_node(role)

if __name__ == "__main__":
    main()