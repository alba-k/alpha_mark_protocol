# akm/core/config/network_config.py
import os

class NetworkConfig:
    """
    Configuración inmutable de la capa de red P2P.
    Centraliza puertos, semillas y límites de seguridad (Anti-DoS).
    """
    
    def __init__(self) -> None:
        # --- Conectividad ---
        self._host: str = os.getenv("AKM_P2P_HOST", "0.0.0.0")
        self._port: int = int(os.getenv("AKM_P2P_PORT", 5000))
        
        # Semillas iniciales (Bootstrap Nodes)
        seeds_env = os.getenv("AKM_SEEDS", "")
        self._seeds: list[str] = seeds_env.split(",") if seeds_env else []

        # --- Seguridad (Anti-DoS) ---
        # Máximo de conexiones concurrentes
        self._max_connections: int = int(os.getenv("AKM_NET_MAX_CONNS", 50))
        
        # Tamaño máximo de mensaje (5 MB)
        self._max_buffer_size: int = int(os.getenv("AKM_NET_MAX_BUFFER", 5 * 1024 * 1024))

    @property
    def host(self) -> str: return self._host
    
    @property
    def port(self) -> int: return self._port
    
    @property
    def seeds(self) -> list[str]: return self._seeds
    
    @property
    def max_connections(self) -> int: return self._max_connections
    
    @property
    def max_buffer_size(self) -> int: return self._max_buffer_size