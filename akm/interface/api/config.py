# akm/interface/api/config.py

import os
import logging 
from dataclasses import dataclass

# Importamos ConsensusConfig 
from akm.core.config.consensus_config import ConsensusConfig 

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class ApiConfig:
    host: str
    port: int
    title: str
    version: str
    db_name: str
    debug_mode: bool
    mining_enabled: bool
    coin_scale: int 

    @classmethod
    def load(cls) -> 'ApiConfig':

        # 1. Leemos del entorno (Infraestructura)
        host = os.getenv("AKM_API_HOST", "0.0.0.0")
        port = int(os.getenv("AKM_API_PORT", 8080))
        title = os.getenv("AKM_API_TITLE", "Alpha Mark Protocol API")
        version = "0.1.0"
        db_name = os.getenv("AKM_DB_NAME", "api_node.db") 
        debug = os.getenv("AKM_DEBUG", "False").lower() == "true"
        mining = os.getenv("AKM_MINING_ENABLED", "False").lower() == "true"

        # 2. Leemos del Núcleo (Dominio)
        scale = 100_000_000 # Default Fallback
        try:
            # ⚡ CORRECCIÓN: Usamos ConsensusConfig
            core_conf = ConsensusConfig()
            scale = core_conf.coin_factor 
            logger.debug(f"⚙️  Factor de escala cargado de ConsensusConfig: {scale}")
        except Exception:
            logger.warning("⚠️ No se pudo cargar ConsensusConfig. Usando coin_scale de fallback.")
            
        config = cls(
            host=host,
            port=port,
            title=title,
            version=version,
            db_name=db_name,
            debug_mode=debug,
            mining_enabled=mining,
            coin_scale=scale
        )
        
        logger.info("⚙️  Configuración de la API cargada:")
        logger.info(f"   URL: http://{config.host}:{config.port}")
        logger.info(f"   Título: {config.title} v{config.version}")
        logger.info(f"   Mining: {'ACTIVO' if config.mining_enabled else 'INACTIVO'}")
        logger.debug(f"   Debug: {config.debug_mode} | Scale: {config.coin_scale}")
        
        return config

# Instancia Singleton inmutable
settings = ApiConfig.load()