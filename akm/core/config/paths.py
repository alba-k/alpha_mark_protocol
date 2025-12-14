# akm/core/config/paths.py

import os
from pathlib import Path

class Paths:
    """
    Centraliza las rutas absolutas del proyecto.
    Soporta Inyección de Dependencias vía Variables de Entorno.
    """
    
    # 1. Detectamos la raíz del código (Fallback original)
    _CODE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
    
    # 2. LÓGICA DINÁMICA DIRECTA (Clean Code)
    # Si existe la variable de entorno, la usa. Si no, usa el default (_CODE_ROOT/data).
    DATA_DIR = Path(os.getenv("AKM_DATA_DIR", _CODE_ROOT / "data"))
    
    # 3. SUBCARPETAS (Construidas sobre la ruta dinámica)
    # Mantenemos los nombres EXACTOS para no romper importaciones en otros scripts.
    WALLETS_DIR = DATA_DIR / "wallets"
    BLOCKCHAIN_DB_DIR = DATA_DIR / "blockchain"
    MINING_DIR = DATA_DIR / "mining"
    LOGS_DIR = DATA_DIR / "logs"

    @staticmethod
    def ensure_directories_exist():
        """Crea toda la estructura de carpetas si no existe."""
        os.makedirs(Paths.WALLETS_DIR, exist_ok=True)
        os.makedirs(Paths.BLOCKCHAIN_DB_DIR, exist_ok=True)
        os.makedirs(Paths.MINING_DIR, exist_ok=True)
        os.makedirs(Paths.LOGS_DIR, exist_ok=True)
        
        # Retornamos las rutas para logs o depuración
        return {
            "root": str(Paths.DATA_DIR),
            "logs": str(Paths.LOGS_DIR)
        }

# Al importar, garantizamos existencia de carpetas inmediatamente
Paths.ensure_directories_exist()