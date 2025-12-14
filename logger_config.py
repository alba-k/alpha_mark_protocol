# logger_config.py
import logging
import os
import glob
import sys
from typing import List

def setup_logging():
    # 1. Definir ruta: Guardaremos en 'data/logs' para mantener el orden
    # Usamos ruta absoluta basada en este archivo
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(ROOT_DIR, "data", "logs")
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 2. Rotación de Archivos: Buscar el siguiente número (blockchain_0.log, blockchain_1.log...)
    existentes: List[str] = glob.glob(os.path.join(log_dir, "blockchain_*.log"))
    indices: List[int] = []
    for archivo in existentes:
        try:
            # Extraer el número del nombre del archivo
            num = int(archivo.split('_')[-1].split('.')[0])
            indices.append(num)
        except (ValueError, IndexError): continue
    
    siguiente: int = max(indices) + 1 if indices else 0
    nombre_archivo: str = os.path.join(log_dir, f"blockchain_{siguiente}.log")

    # 3. Configurar el Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Limpiamos handlers anteriores para evitar duplicados si se llama dos veces
    root_logger.handlers = [] 

    # --- CANAL 1: ARCHIVO (Todo el historial detallado) ---
    # encoding='utf-8' es vital para tus emojis
    fh = logging.FileHandler(nombre_archivo, encoding='utf-8')
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s]: %(message)s'))

    # --- CANAL 2: TERMINAL (Solo ERRORES o CRÍTICOS) ---
    # Esto silencia la consola para que se vea limpia, solo avisará si explota algo.
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.ERROR) 
    ch.setFormatter(logging.Formatter('\n❌ ERROR EN: %(name)s | Línea: %(lineno)d\nDetalle: %(message)s\n'))

    root_logger.addHandler(fh)
    root_logger.addHandler(ch)

    # Imprimimos esto directamente (print) para que el usuario sepa dónde buscar el log
    # ya que el logger.info no saldrá en consola por la configuración de arriba.
    print(f"📝 Log de sesión guardado en: {nombre_archivo}")