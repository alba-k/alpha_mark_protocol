# akm/infra/persistence/repository_factory.py
import logging
from akm.core.interfaces.i_repository import IBlockchainRepository
from akm.core.config.config_manager import ConfigManager

# Tus implementaciones (Drivers)
from akm.infra.persistence.sqlite.sqlite_blockchain_repository import SqliteBlockchainRepository
from akm.infra.persistence.json.json_repository import JsonBlockchainRepository
from akm.infra.persistence.leveldb.leveldb_repository import LevelDBBlockchainRepository

class RepositoryFactory:
    
    @staticmethod
    def get_repository() -> IBlockchainRepository:
        # 1. Leemos TU configuración manual
        config = ConfigManager()
        # Convertimos a minúsculas por si escribiste "SQLite"
        storage_type = config.persistence.storage_engine.lower()
        
        logging.info(f"🏗️  Iniciando motor seleccionado: {storage_type.upper()}")

        # 2. Selección automática
        if storage_type == "sqlite":
            return SqliteBlockchainRepository()

        elif storage_type == "json":
            return JsonBlockchainRepository()
        
        elif storage_type == "leveldb":
            return LevelDBBlockchainRepository()

        else:
            raise ValueError(f"❌ Error: El motor '{storage_type}' no existe. Revisa persistence_config.py")