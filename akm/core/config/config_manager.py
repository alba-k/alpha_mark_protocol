# akm/core/config/config_manager.py
'''
class ConfigManager:
    Gestor centralizado de parámetros de configuración (Singleton implícito).
    Permite modificar las reglas de consenso sin alterar el código fuente (OCP).

    Attributes::
        _target_block_time_sec (int): Tiempo esperado entre bloques (ej: 600s).
        _difficulty_adjustment_interval (int): Cada cuántos bloques se ajusta la dificultad.
        _initial_difficulty_bits (int): Dificultad inicial (Compact format).
        _mempool_max_size (int): Cantidad máxima de transacciones en espera.
        _max_block_size_bytes (int): Tamaño máximo de un bloque en bytes.
    
    Methods::
        (Properties): Accesores de solo lectura para los parámetros.
'''

import os

class ConfigManager:

    def __init__(self):
        
        # Tiempo objetivo entre bloques (Default: 60 segundos para pruebas rápidas)
        self._target_block_time_sec: int = int(os.getenv("AKM_BLOCK_TIME", 60))
        
        # Intervalo de ajuste de dificultad (Default: Cada 100 bloques)
        self._difficulty_adjustment_interval: int = int(os.getenv("AKM_DIFF_INTERVAL", 100))
        
        # Dificultad inicial (simulada en bits compactos hexadecimales)
        self._initial_difficulty_bits: str = os.getenv("AKM_INIT_BITS", "1d00ffff")

        # --- LÍMITES DE MEMORIA Y BLOQUE (Nuevos) ---
        
        # Máximo de transacciones en memoria (ej. 5000 txs)
        self._mempool_max_size: int = int(os.getenv("AKM_MEMPOOL_MAX", 5000))
        
        # Tamaño máximo del bloque (ej. 1 MB = 1000000 bytes)
        # Esto limita cuántas transacciones caben en un bloque.
        self._max_block_size_bytes: int = int(os.getenv("AKM_MAX_BLOCK_SIZE", 1000000))

    @property
    def target_block_time_sec(self) -> int:
        return self._target_block_time_sec

    @property
    def difficulty_adjustment_interval(self) -> int:
        return self._difficulty_adjustment_interval

    @property
    def initial_difficulty_bits(self) -> str:
        return self._initial_difficulty_bits

    @property
    def mempool_max_size(self) -> int:
        return self._mempool_max_size

    @property
    def max_block_size_bytes(self) -> int:
        return self._max_block_size_bytes