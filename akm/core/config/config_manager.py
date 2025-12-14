# akm/core/config/config_manager.py
'''
class ConfigManager:
    Orquesta y centraliza el acceso a la configuración de todos los módulos (Consenso, Red, Persistencia y Minería), cargando valores desde el entorno o JSON.

    Methods:
        __new__(cls): Implementa el patrón Singleton para asegurar una única instancia.
        _initialize(self): Inicializa y carga las configuraciones especializadas (Consensus, Network, etc.) con valores por defecto/entorno.
        load_from_json_dict(self, json_data: Dict[str, Any]) -> None: Orquesta la actualización de todas las sub-configuraciones a partir de un diccionario JSON completo.

'''

from dotenv import load_dotenv
from typing import Dict, Any

# Cargar variables de entorno si existen
load_dotenv()

# Importar piezas de configuración
from akm.core.config.consensus_config import ConsensusConfig   
from akm.core.config.persistence_config import PersistenceConfig
from akm.core.config.network_config import NetworkConfig
from akm.core.config.mining_config import MiningConfig

class ConfigManager:
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._consensus = ConsensusConfig()      # Reglas del juego
        self._persistence = PersistenceConfig()  # Base de datos
        self._network = NetworkConfig()          # Puertos e IPs
        self._mining = MiningConfig()            # Dirección de minero
        self._node_type = "FULL" # Default (FULL, LIGHT, MINER)

    def load_from_json_dict(self, json_data: Dict[str, Any]) -> None:

        # Configuración 
        if "node_type" in json_data:
            self._node_type = str(json_data["node_type"]).upper()

        # Red
        if "network" in json_data:
            self._network.update_from_dict(json_data["network"])

        # Persistencia
        if "storage" in json_data:
            self._persistence.update_from_dict(json_data["storage"])

        # Minería (Combinamos secciones 'payout' y 'performance' 
        miner_updates: dict[str, Any] = {}
        if "payout" in json_data: 
            miner_updates.update(json_data["payout"])
        if "performance" in json_data: 
            miner_updates.update(json_data["performance"])
        
        self._mining.update_from_dict(miner_updates)

        consensus_data = json_data.get("consensus", {})
        mempool_data = json_data.get("mempool", {})
        
        self._consensus.update_from_dict(consensus_data, mempool_data)

    # --- ACCESORES ORGANIZADOS ---

    @property
    def node_type(self) -> str:
        return self._node_type

    @property
    def consensus(self) -> ConsensusConfig:
        return self._consensus

    @property
    def persistence(self) -> PersistenceConfig:
        return self._persistence

    @property
    def network(self) -> NetworkConfig:
        return self._network
    
    @property
    def mining(self) -> MiningConfig:
        return self._mining

    # --- DELEGACIÓN (Atajos de compatibilidad) ---
    
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