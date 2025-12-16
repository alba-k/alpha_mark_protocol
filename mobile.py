# mobile.py
import os
import sys
import json
import argparse
import logging
import uvicorn
from pathlib import Path
from typing import Dict, Any, Optional

# =========================================================
# ⚙️ CONFIGURACIÓN GLOBAL Y CONSTANTES
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

ROOT_DIR: Path = Path(os.getcwd())
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

DEFAULT_API_PORT: int = 8080
DEFAULT_HOST: str = "0.0.0.0"

# =========================================================
# 📦 FUNCIONES AUXILIARES
# =========================================================

def load_config(config_name: str) -> Dict[str, Any]:
    path_local = ROOT_DIR / config_name
    path_config_dir = ROOT_DIR / "config" / config_name
    target_path: Optional[Path] = None

    if path_local.exists(): target_path = path_local
    elif path_config_dir.exists(): target_path = path_config_dir

    if not target_path:
        raise FileNotFoundError(f"Config no encontrada: {config_name}")

    logger.info(f"📂 Configuración cargada: {target_path}")
    with open(target_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def configure_environment(config: Dict[str, Any], instance_name: str, port_override: Optional[int]) -> int:
    """
    Configura variables de entorno con aislamiento de datos y puerto dinámico.
    """
    # 1. Identidad y Rol
    os.environ["AKM_INSTANCE_NAME"] = instance_name
    os.environ["AKM_NODE_ROLE"] = "SPV_NODE"

    # 2. Aislamiento de Datos (Multi-Usuario)
    # Crea: data_mobile/WALLET_1, data_mobile/WALLET_2, etc.
    data_dir = ROOT_DIR / "data_mobile" / instance_name
    
    if not data_dir.exists():
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creando directorio: {e}")

    os.environ["AKM_DATA_DIR"] = str(data_dir)
    logger.info(f"💾 Directorio de datos: {data_dir}")

    # 3. Red
    os.environ["AKM_P2P_HOST"] = DEFAULT_HOST
    os.environ["AKM_API_HOST"] = DEFAULT_HOST

    # 4. Puerto API (Prioridad: CLI > JSON > Default)
    api_conf = config.get("api", {})
    json_port = api_conf.get("port_default", DEFAULT_API_PORT)
    
    final_port = port_override if port_override else json_port
    os.environ["AKM_API_PORT"] = str(final_port)

    # 5. Seeds
    net_conf = config.get("network", {})
    seeds_list = net_conf.get("seeds", [])
    if not seeds_list:
        logger.warning("⚠️ Sin seeds configuradas.")
    os.environ["AKM_SEEDS"] = ",".join(seeds_list)

    # 6. Persistencia
    os.environ["AKM_MINING_ENABLED"] = "False"
    os.environ["AKM_STORAGE_ENGINE"] = "sqlite"
    os.environ["AKM_DB_NAME"] = "wallet_mobile.db"

    return final_port

# =========================================================
# 🚀 ENTRY POINT
# =========================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="🚀 AKM Mobile Launcher")
    parser.add_argument("config", help="Archivo JSON (ej: config/spv.json)")
    parser.add_argument("--name", required=True, help="ID único (ej: usuario1)")
    # [NUEVO] Argumento vital para correr múltiples wallets a la vez
    parser.add_argument("--port", type=int, help="Puerto API (ej: 8081)") 
    
    args = parser.parse_args()

    print(f"\n📱 INICIANDO AKM MOBILE | Usuario: {args.name}")
    print("=" * 60)

    try:
        config_data = load_config(args.config)
        
        # Pasamos el puerto opcional a la configuración
        port = configure_environment(config_data, args.name, args.port)

        try:
            # Importación tardía para asegurar que las variables de entorno existen
            import akm.interface.api.server # type: ignore
        except ImportError as e:
            logger.critical(f"❌ Error importando AKM Core: {e}")
            sys.exit(1)

        print(f"✅ Entorno listo.")
        print(f"🌐 API Web: http://localhost:{port}")
        print("-" * 60)

        uvicorn.run(
            "akm.interface.api.server:app",
            host=DEFAULT_HOST,
            port=port,
            log_level="info"
        )

    except Exception as e:
        logger.exception(f"❌ Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()