# akm/core/config/network_config.py

import os
from typing import Dict, Any, List

class NetworkConfig:
    """
    Configuración específica para la capa de Red P2P.
    Aisla los detalles de infraestructura (Host, Port, Seeds) de la lógica de consenso.
    """
    def __init__(self) -> None:
        # Valores por defecto desde Variables de Entorno (Cerebro 1)
        self._host: str = os.getenv("AKM_P2P_HOST", "0.0.0.0")
        self._port: int = int(os.getenv("AKM_P2P_PORT", 5000))
        
        seeds_env = os.getenv("AKM_SEEDS", "")
        # Filtramos cadenas vacías para evitar seeds inválidos
        self._seeds: List[str] = [s.strip() for s in seeds_env.split(",") if s.strip()]
        
        self._max_connections: int = int(os.getenv("AKM_NET_MAX_CONNS", 50))
        self._max_buffer_size: int = int(os.getenv("AKM_NET_MAX_BUFFER", 5 * 1024 * 1024))

    # --- Getters Públicos (Solo Lectura) ---
    @property
    def host(self) -> str: return self._host
    @property
    def port(self) -> int: return self._port
    @property
    def seeds(self) -> List[str]: return self._seeds
    @property
    def max_connections(self) -> int: return self._max_connections
    @property
    def max_buffer_size(self) -> int: return self._max_buffer_size

    # --- Método de Actualización Controlada ---
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """
        Inyecta configuración externa (JSON) respetando el encapsulamiento.
        """
        if not data: return
        
        if "p2p_port" in data: 
            self._port = int(data["p2p_port"])
        
        if "max_peers" in data: 
            self._max_connections = int(data["max_peers"])
        
        if "seed_nodes" in data and isinstance(data["seed_nodes"], list):
            self._seeds = data["seed_nodes"]