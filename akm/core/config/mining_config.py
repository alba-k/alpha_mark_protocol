# akm/core/config/mining_config.py
import os

class MiningConfig:
    """
    Configuración específica para el Rol de Minero.
    Define a dónde van las recompensas por defecto.
    """
    def __init__(self):
        # Dirección de la Wallet donde caerán las recompensas (Coinbase)
        # Ideal para nodos desatendidos (Docker/Servidores)
        self._default_miner_address = os.getenv("AKM_MINER_ADDRESS", "")
        
        # Opcional: Cantidad de hilos para minar (CPU Power)
        self._mining_threads = int(os.getenv("AKM_MINING_THREADS", 1))

    @property
    def default_miner_address(self) -> str:
        return self._default_miner_address

    @property
    def mining_threads(self) -> int:
        return self._mining_threads