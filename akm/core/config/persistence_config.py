# akm/core/config/persistence_config.py
import os
from typing import Dict, Any

# Importamos Paths para sincronizar las rutas
from akm.core.config.paths import Paths

class PersistenceConfig:
    """
    Configuración de Persistencia.
    Responsable de definir dónde se guardan los datos (DB y Wallet).
    """
    def __init__(self):
        self._storage_engine = os.getenv("AKM_STORAGE_ENGINE", "sqlite").lower()
        self._db_name = os.getenv("AKM_DB_NAME", "blockchain_oficial.db")
        
        # [DINÁMICO] Usamos la ruta centralizada de Paths
        # Esto asegura que obedezca al launcher o al default sin romper lógica.
        self._data_dir = str(Paths.DATA_DIR)
        
        self._write_buffer_size = int(os.getenv("AKM_WRITE_BUFFER_SIZE", 64 * 1024 * 1024))
        self._prune_mode = os.getenv("AKM_PRUNE_MODE", "False").lower() == "true"
        
        # Nombre de archivo de wallet configurable
        self._wallet_filename = "node_wallet.dat"

    # --- Propiedades (Mantenemos nombres para compatibilidad) ---
    @property
    def db_name(self) -> str: return self._db_name
    @property
    def storage_engine(self) -> str: return self._storage_engine
    @property
    def data_dir(self) -> str: return self._data_dir
    @property
    def write_buffer_size(self) -> int: return self._write_buffer_size
    @property
    def prune_mode(self) -> bool: return self._prune_mode
    @property
    def wallet_filename(self) -> str: return self._wallet_filename
    
    @property
    def db_path(self) -> str:
        """
        Retorna la ruta completa al archivo DB.
        Ahora apunta correctamente a data/blockchain/nombre.db
        """
        return os.path.join(str(Paths.BLOCKCHAIN_DB_DIR), self._db_name)

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Actualiza la configuración desde un diccionario externo (JSON)."""
        if not data: return
        
        # Permitimos sobrescribir data_dir manualmente si viene en el JSON
        if "data_dir" in data: 
            self._data_dir = str(data["data_dir"])
            
        if "db_cache_mb" in data:
            self._write_buffer_size = int(data["db_cache_mb"]) * 1024 * 1024
            
        if "prune_mode" in data:
            self._prune_mode = bool(data["prune_mode"])

        if "wallet_file" in data:
            self._wallet_filename = str(data["wallet_file"])