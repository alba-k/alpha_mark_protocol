# akm/core/config/config_manager.py
from dotenv import load_dotenv

# Cargar variables de entorno si existen
load_dotenv()

# Importar las 4 piezas de configuración
from akm.core.config.consensus_config import ConsensusConfig   
from akm.core.config.persistence_config import PersistenceConfig
from akm.core.config.network_config import NetworkConfig
from akm.core.config.mining_config import MiningConfig

class ConfigManager:
    """
    Gestor Maestro de Configuración (Singleton).
    Centraliza el acceso a todos los parámetros del sistema.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Inicializamos los módulos especializados
        self._consensus = ConsensusConfig()      # Reglas del juego
        self._persistence = PersistenceConfig()  # Base de datos
        self._network = NetworkConfig()          # Puertos e IPs
        self._mining = MiningConfig()            # Dirección de minero

    # --- ACCESORES ORGANIZADOS ---

    @property
    def consensus(self) -> ConsensusConfig:
        """Acceso a reglas de protocolo (tiempos, dificultad, subsidio)."""
        return self._consensus

    @property
    def persistence(self) -> PersistenceConfig:
        """Acceso a configuración de base de datos."""
        return self._persistence

    @property
    def network(self) -> NetworkConfig:
        """Acceso a configuración de red P2P."""
        return self._network
    
    @property
    def mining(self) -> MiningConfig:
        """Acceso a configuración de minería."""
        return self._mining

    # --- DELEGACIÓN (Atajos de compatibilidad) ---
    # Mantenemos estos getters para no romper el código existente que llama a 
    # config.target_block_time_sec directamente, pero internamente redirigen.
    
    @property
    def target_block_time_sec(self) -> int: return self._consensus.target_block_time_sec
    @property
    def difficulty_adjustment_interval(self) -> int: return self._consensus.difficulty_adjustment_interval
    @property
    def initial_difficulty_bits(self) -> str: return self._consensus.initial_difficulty_bits
    @property
    def mempool_max_size(self) -> int: return self._consensus.mempool_max_size
    @property
    def max_block_size_bytes(self) -> int: return self._consensus.max_block_size_bytes
    @property
    def max_nonce(self) -> int: return self._consensus.max_nonce
    @property
    def initial_subsidy(self) -> int: return self._consensus.initial_subsidy
    @property
    def halving_interval(self) -> int: return self._consensus.halving_interval
    @property
    def fallback_halving_interval(self) -> int: return self._consensus.fallback_halving_interval