import argparse
import json
import sys
import os
from typing import Dict, Any # <--- Importamos herramientas de tipado

# Importamos las clases de la carpeta src
# (Asumiendo que Node y Miner también están bien construidos)
from src.node import Node
from src.miner import Miner

# 1. Definimos: "path" debe ser texto (str) y retorna un Diccionario (Dict)
def load_config(path: str) -> Dict[str, Any]:
    """
    Carga el archivo JSON y retorna un diccionario con la configuración.
    """
    if not os.path.exists(path):
        print(f"ERROR: No se encontró el archivo de configuración: {path}")
        sys.exit(1)
        
    try:
        with open(path, 'r') as f:
            data: Dict[str, Any] = json.load(f)
            return data
    except json.JSONDecodeError:
        print(f"ERROR: El archivo {path} no es un JSON válido.")
        sys.exit(1)

def main() -> None:
    # 2. Configurar los argumentos que recibe el programa
    parser = argparse.ArgumentParser(description="Alpha Mark Protocol (AKM) Client")
    
    # Aquí argparse ya fuerza el tipo internamente, pero es bueno ser explícito
    parser.add_argument('--mode', type=str, choices=['node', 'miner'], required=True, help='Modo de ejecución')
    parser.add_argument('--config', type=str, required=True, help='Ruta al archivo .json')
    
    args = parser.parse_args()

    # 3. Cargar la configuración seleccionada
    # La variable config_data ahora el IDE sabe que es un diccionario
    config_data: Dict[str, Any] = load_config(args.config)

    # 4. Decidir qué arrancar
    if args.mode == 'node':
        print("[INIT] Iniciando modo Nodo...")
        app_node = Node(config_data)
        app_node.start()
        
    elif args.mode == 'miner':
        print("[INIT] Iniciando modo Minero...")
        app_miner = Miner(config_data)
        app_miner.start()

if __name__ == "__main__":
    main()