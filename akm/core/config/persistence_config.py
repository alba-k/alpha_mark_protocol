import os
from typing import Dict, Any

class PersistenceConfig:
    """
    Configuración de Persistencia.
    """
    def __init__(self):
        self._storage_engine = os.getenv("AKM_STORAGE_ENGINE", "sqlite").lower()
        self._db_name = os.getenv("AKM_DB_NAME", "blockchain_oficial.db")
        self._data_dir = os.getenv("AKM_DATA_DIR", "./data")
        self._write_buffer_size = int(os.getenv("AKM_WRITE_BUFFER_SIZE", 64 * 1024 * 1024))
        # NUEVO: Modo Poda (para Light Nodes)
        self._prune_mode = os.getenv("AKM_PRUNE_MODE", "False").lower() == "true"

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
    def db_path(self) -> str:
        return os.path.join(self._data_dir, self._db_name)

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        if not data: return
        if "data_dir" in data: 
            self._data_dir = str(data["data_dir"])
        if "db_cache_mb" in data:
            self._write_buffer_size = int(data["db_cache_mb"]) * 1024 * 1024
        # NUEVO: Leer prune_mode del JSON
        if "prune_mode" in data:
            self._prune_mode = bool(data["prune_mode"])