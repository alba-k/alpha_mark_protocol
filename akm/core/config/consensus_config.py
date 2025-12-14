# akm/core/config/consensus_config.py

import os
from typing import Dict, Any

class ConsensusConfig:
    """
    Configuración de las Reglas de Consenso.
    """
    # --- CONSTANTES ESTÁTICAS ---
    DECIMALS = 8
    COIN_FACTOR = 10 ** DECIMALS

    def __init__(self):
        self._coin_factor = ConsensusConfig.COIN_FACTOR
        
        # Valores por defecto (Env Vars)
        base_subsidy = int(os.getenv("AKM_INITIAL_SUBSIDY", 50))
        self._initial_subsidy = base_subsidy * self._coin_factor
        
        self._target_block_time_sec = int(os.getenv("AKM_BLOCK_TIME", 60))
        self._difficulty_adjustment_interval = int(os.getenv("AKM_DIFF_INTERVAL", 10))
        self._initial_difficulty_bits = os.getenv("AKM_INIT_BITS", "207fffff")
        
        # --- PARÁMETROS DE DIFICULTAD (GENESIS) ---
        # 🔥 RESTAURADO: Necesario para calcular max_target
        self._genesis_mantissa = int(os.getenv("AKM_GENESIS_MANTISSA", 0x7fffff))
        self._genesis_exponent = int(os.getenv("AKM_GENESIS_EXPONENT", 0x20))
        
        self._mempool_max_size = int(os.getenv("AKM_MEMPOOL_MAX", 5000))
        self._max_block_size_bytes = int(os.getenv("AKM_MAX_BLOCK_SIZE", 1_000_000))
        self._max_nonce = int(os.getenv("AKM_MAX_NONCE", 4294967295))
        
        self._halving_interval = int(os.getenv("AKM_HALVING_INTERVAL", 210000))
        self._fallback_halving_interval = 210000

    # --- Getters ---
    @property
    def coin_factor(self) -> int: return self._coin_factor
    @property
    def initial_subsidy(self) -> int: return self._initial_subsidy
    @property
    def target_block_time_sec(self) -> int: return self._target_block_time_sec
    @property
    def difficulty_adjustment_interval(self) -> int: return self._difficulty_adjustment_interval
    @property
    def initial_difficulty_bits(self) -> str: return self._initial_difficulty_bits
    
    # 🔥 PROPIEDAD CRÍTICA RESTAURADA
    @property
    def max_target(self) -> int:
        """Calcula el target máximo basado en los bits del génesis."""
        return self._genesis_mantissa * (2 ** (8 * (self._genesis_exponent - 3)))

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

    # --- Actualización desde JSON ---
    def update_from_dict(self, consensus_data: Dict[str, Any], mempool_data: Dict[str, Any]) -> None:
        """
        Actualiza reglas de consenso y mempool desde diccionarios externos.
        """
        # 1. Sección 'consensus'
        if consensus_data:
            if "block_time_target_sec" in consensus_data:
                self._target_block_time_sec = int(consensus_data["block_time_target_sec"])
            
            if "max_block_weight" in consensus_data:
                self._max_block_size_bytes = int(consensus_data["max_block_weight"])

        # 2. Sección 'mempool'
        if mempool_data:
            # Aquí podrías mapear configuraciones de mempool si existieran en el JSON
            pass