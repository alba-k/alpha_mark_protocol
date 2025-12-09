# akm/core/config/config_manager.py
from dotenv import load_dotenv
from typing import Dict, Any

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
        # Inicializamos los módulos especializados con valores por defecto (Variables de Entorno)
        self._consensus = ConsensusConfig()      # Reglas del juego
        self._persistence = PersistenceConfig()  # Base de datos
        self._network = NetworkConfig()          # Puertos e IPs
        self._mining = MiningConfig()            # Dirección de minero
        
        # NUEVO: Variable global de aplicación para identificar el rol del nodo
        self._node_type = "FULL" # Default (FULL, LIGHT, MINER)

    # --- MÉTODO DE UNIFICACIÓN (NUEVO) ---
    def load_from_json_dict(self, json_data: Dict[str, Any]) -> None:
        """
        Orquesta la carga de configuración desde el JSON completo.
        Actualiza los componentes internos respetando el encapsulamiento.
        """
        # 0. Configuración Global (Raíz) - Detectar si es LIGHT o FULL
        if "node_type" in json_data:
            self._node_type = str(json_data["node_type"]).upper()

        # 1. Red
        if "network" in json_data:
            self._network.update_from_dict(json_data["network"])

        # 2. Persistencia
        if "storage" in json_data:
            self._persistence.update_from_dict(json_data["storage"])

        # 3. Minería (Combinamos secciones 'payout' y 'performance' del JSON)
        miner_updates: dict[str, Any] = {}
        if "payout" in json_data: 
            miner_updates.update(json_data["payout"])
        if "performance" in json_data: 
            miner_updates.update(json_data["performance"])
        
        self._mining.update_from_dict(miner_updates)

        # 4. Consenso y Mempool (NUEVO)
        # Extraemos las secciones correspondientes del JSON root
        consensus_data = json_data.get("consensus", {})
        mempool_data = json_data.get("mempool", {})
        
        # Delegamos la actualización al ConsensusConfig
        self._consensus.update_from_dict(consensus_data, mempool_data)

        # Nota: La sección 'rpc' se ignora por ahora ya que no hay módulo RPC implementado.

    # --- ACCESORES ORGANIZADOS ---

    @property
    def node_type(self) -> str:
        """Tipo de nodo configurado (FULL, LIGHT, MINER)."""
        return self._node_type

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