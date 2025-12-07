# akm/interface/api/config.py
import os
from dataclasses import dataclass

# Importamos el ConfigManager del núcleo solo aquí (Encapsulamiento)
from akm.core.config.config_manager import ConfigManager

@dataclass(frozen=True)
class ApiConfig:
    """
    Objeto de Configuración Inmutable (Pattern: Configuration Object).
    Encapsula toda la configuración externa y del núcleo necesaria para la API.
    """
    host: str
    port: int
    title: str
    version: str
    db_name: str
    debug_mode: bool
    mining_enabled: bool
    coin_scale: int  # <--- Nuevo campo encapsulado

    @classmethod
    def load(cls) -> 'ApiConfig':
        """
        Factory Method: Centraliza la lógica de carga de configuración.
        """
        # 1. Leemos del entorno (Infraestructura)
        host = os.getenv("AKM_API_HOST", "0.0.0.0")
        port = int(os.getenv("AKM_API_PORT", 8000))
        title = os.getenv("AKM_API_TITLE", "Alpha Mark Protocol API")
        version = "0.1.0"
        db_name = os.getenv("AKM_DB_NAME", "api_node.db")
        debug = os.getenv("AKM_DEBUG", "False").lower() == "true"
        mining = os.getenv("AKM_MINING_ENABLED", "False").lower() == "true"

        # 2. Leemos del Núcleo (Dominio)
        # Encapsulamos aquí la dependencia con el Core Config.
        # Si el núcleo cambia, solo tocamos este archivo.
        try:
            core_conf = ConfigManager()
            # Usamos getattr por seguridad si consensus no está inicializado
            scale = getattr(core_conf.consensus, 'coin_factor', 100_000_000)
        except Exception:
            scale = 100_000_000 # Fallback seguro

        return cls(
            host=host,
            port=port,
            title=title,
            version=version,
            db_name=db_name,
            debug_mode=debug,
            mining_enabled=mining,
            coin_scale=scale
        )

# Instancia Singleton inmutable
settings = ApiConfig.load()