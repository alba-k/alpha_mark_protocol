# akm/core/config/consensus_config.py
import os

class ConsensusConfig:
    """
    Configuración de las Reglas de Consenso.
    Aquí se define la economía del sistema (La verdad absoluta).
    """
    
    # --- CONSTANTES ESTÁTICAS (ACCESO GLOBAL) ---
    DECIMALS = 8
    COIN_FACTOR = 10 ** DECIMALS  # 100,000,000

    def __init__(self):
        # --- 1. POLÍTICA MONETARIA (LA REGLA MAESTRA) ---
        self._coin_factor = ConsensusConfig.COIN_FACTOR
        
        # --- 2. RECOMPENSA DE MINERÍA ---
        base_subsidy_akm = int(os.getenv("AKM_INITIAL_SUBSIDY", 50))
        self._initial_subsidy = base_subsidy_akm * self._coin_factor

        # --- 3. PARÁMETROS DE CONSENSO (POW) ---
        self._target_block_time_sec = int(os.getenv("AKM_BLOCK_TIME", 60))
        self._difficulty_adjustment_interval = int(os.getenv("AKM_DIFF_INTERVAL", 10))
        self._initial_difficulty_bits = os.getenv("AKM_INIT_BITS", "207fffff")
        self._genesis_mantissa = int(os.getenv("AKM_GENESIS_MANTISSA", 0x7fffff))
        self._genesis_exponent = int(os.getenv("AKM_GENESIS_EXPONENT", 0x20))
        
        # --- 4. LÍMITES DE RED Y MEMPOOL ---
        self._mempool_max_size = int(os.getenv("AKM_MEMPOOL_MAX", 5000))
        self._max_block_size_bytes = int(os.getenv("AKM_MAX_BLOCK_SIZE", 1000000))
        self._max_nonce = int(os.getenv("AKM_MAX_NONCE", 4294967295))
        
        # --- 5. HALVING ---
        self._halving_interval = int(os.getenv("AKM_HALVING_INTERVAL", 210000))
        self._fallback_halving_interval = 210000

    # --- PROPIEDADES PÚBLICAS (GETTERS) ---
    @property
    def coin_factor(self) -> int: return self._coin_factor
    @property
    def initial_subsidy(self) -> int: return self._initial_subsidy
    @property
    def max_target(self) -> int:
        return self._genesis_mantissa * (2 ** (8 * (self._genesis_exponent - 3)))
    @property
    def target_block_time_sec(self) -> int: return self._target_block_time_sec
    @property
    def difficulty_adjustment_interval(self) -> int: return self._difficulty_adjustment_interval
    @property
    def initial_difficulty_bits(self) -> str: return self._initial_difficulty_bits
    @property
    def mempool_max_size(self) -> int: return self._mempool_max_size
    @property
    def max_block_size_bytes(self) -> int: return self._max_block_size_bytes
    @property
    def max_nonce(self) -> int: return self._max_nonce
    @property
    def halving_interval(self) -> int: return self._halving_interval
    @property
    def fallback_halving_interval(self) -> int: return self._fallback_halving_interval