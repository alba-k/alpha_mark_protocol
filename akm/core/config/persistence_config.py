# akm/core/config/persistence_config.py
import os

class PersistenceConfig:
    """
    Configuración de Persistencia.
    Ahora soporta inyección por Variables de Entorno para facilitar Testing y Despliegue.
    """
    
    def __init__(self):
        # -----------------------------------------------------------
        # 1. MOTOR DE ALMACENAMIENTO
        # Default: "sqlite". Opciones: "sqlite", "json", "leveldb"
        # -----------------------------------------------------------
        self._storage_engine = os.getenv("AKM_STORAGE_ENGINE", "sqlite").lower()

        # -----------------------------------------------------------
        # 2. NOMBRE DE LA BASE DE DATOS
        # Default: "blockchain_oficial.db"
        # -----------------------------------------------------------
        self._db_name = os.getenv("AKM_DB_NAME", "blockchain_oficial.db")
        
        # Cache de escritura (Default: 64MB)
        self._write_buffer_size = int(os.getenv("AKM_WRITE_BUFFER_SIZE", 64 * 1024 * 1024))

    @property
    def db_name(self) -> str:
        return self._db_name

    @property
    def storage_engine(self) -> str:
        return self._storage_engine
        
    @property
    def write_buffer_size(self) -> int:
        return self._write_buffer_size