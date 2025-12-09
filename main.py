import argparse
import json
import sys
import os
from typing import Dict, Any

# Importamos las clases de aplicación
from src.node import Node
from src.miner import Miner

# Importamos el ConfigManager para inyectarle los datos
from akm.core.config.config_manager import ConfigManager

def load_json_config(path: str) -> Dict[str, Any]:
    """Carga el archivo JSON y retorna un diccionario."""
    if not os.path.exists(path):
        print(f"ERROR: No se encontró el archivo de configuración: {path}")
        sys.exit(1)
        
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"ERROR: El archivo {path} no es un JSON válido.")
        sys.exit(1)

def main() -> None:
    parser = argparse.ArgumentParser(description="Alpha Mark Protocol (AKM) Client")
    parser.add_argument('--mode', type=str, choices=['node', 'miner'], required=True, help='Modo de ejecución')
    parser.add_argument('--config', type=str, required=True, help='Ruta al archivo .json')
    args = parser.parse_args()

    # 1. Cargar configuración cruda del JSON
    raw_config_data = load_json_config(args.config)

    # 2. INYECCIÓN DE DEPENDENCIAS (Unificación de Cerebros)
    # Obtenemos el Singleton y le inyectamos los datos del JSON.
    # Esto actualiza las variables protegidas internamente de forma segura.
    config_manager = ConfigManager()
    config_manager.load_from_json_dict(raw_config_data)
    
    print(f"[INIT] Configuración cargada exitosamente desde {args.config}")

    # 3. Arrancar la aplicación correspondiente
    # Nota: Ya no pasamos 'raw_config_data' porque las clases lo leen del ConfigManager.
    if args.mode == 'node':
        app_node = Node()
        app_node.start()
        
    elif args.mode == 'miner':
        app_miner = Miner()
        app_miner.start()

if __name__ == "__main__":
    main()