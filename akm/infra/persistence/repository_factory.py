# akm/infra/persistence/repository_factory.py

import logging
from akm.core.interfaces.i_repository import IBlockchainRepository
from akm.core.interfaces.i_utxo_repository import IUTXORepository
from akm.core.config.config_manager import ConfigManager

# Blockchain Repositories
from akm.infra.persistence.sqlite.sqlite_blockchain_repository import SqliteBlockchainRepository
from akm.infra.persistence.json.json_repository import JsonBlockchainRepository
from akm.infra.persistence.leveldb.leveldb_repository import LevelDBBlockchainRepository

# UTXO Repositories
from akm.infra.persistence.sqlite.sqlite_utxo_repository import SqliteUTXORepository

logger = logging.getLogger(__name__)

class RepositoryFactory:
    
    @staticmethod
    def get_blockchain_repository() -> IBlockchainRepository:
        """Factory para la Blockchain (Historia)."""
        config = ConfigManager()
        storage_type = config.persistence.storage_engine.lower()
        
        logger.info(f"🏗️  Blockchain DB: {storage_type.upper()}")

        if storage_type == "sqlite":
            return SqliteBlockchainRepository()
        elif storage_type == "json":
            return JsonBlockchainRepository() # pyright: ignore[reportAbstractUsage]
        elif storage_type == "leveldb":
            return LevelDBBlockchainRepository() # pyright: ignore[reportAbstractUsage]
        else:
            error_msg = f"Motor '{storage_type}' no soportado para Blockchain."
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)

    @staticmethod
    def get_utxo_repository() -> IUTXORepository:
        logger.info("🏗️  UTXO DB: SQLITE (Optimized)")
        return SqliteUTXORepository()