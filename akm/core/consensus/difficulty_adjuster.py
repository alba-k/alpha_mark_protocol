# akm/core/consensus/difficulty_adjuster.py
'''
class DifficultyAdjuster:
    Lógica de Consenso para el ajuste dinámico de la dificultad (Proof-of-Work)
    y la gestión de la Política Monetaria (Emisión/Halving).

    Methods::
        calculate_new_bits(prev_adj_block, last_block) -> str:
            Calcula la dificultad para el siguiente periodo.
        calculate_block_subsidy(block_index) -> int:
            Calcula la recompensa base permitida según la altura del bloque (Halving).
'''

import logging
from akm.core.models.block import Block
from akm.core.config.config_manager import ConfigManager
from akm.core.utils.difficulty_utils import DifficultyUtils

logging.basicConfig(level=logging.INFO, format='[DiffAdjuster] %(message)s')

class DifficultyAdjuster:

    def __init__(self):
        self._config = ConfigManager()
        # Ahora leemos la política monetaria desde la configuración centralizada
        # No guardamos copias locales para asegurar que siempre usamos la verdad del ConfigManager

    def calculate_new_bits(self, prev_adjustment_block: Block, last_block: Block) -> str:
        """
        Calcula los bits de dificultad basándose en el tiempo transcurrido.
        """
        if not prev_adjustment_block or not last_block:
            raise ValueError("DifficultyAdjuster: Se requieren bloques válidos para el ajuste.")

        actual_timespan = last_block.timestamp - prev_adjustment_block.timestamp
        target_timespan = self._config.difficulty_adjustment_interval * self._config.target_block_time_sec

        # Retargeting Limiting (x4 / 0.25)
        if actual_timespan < target_timespan / 4:
            actual_timespan = target_timespan / 4
        if actual_timespan > target_timespan * 4:
            actual_timespan = target_timespan * 4

        previous_target = DifficultyUtils.bits_to_target(last_block.bits)
        new_target = previous_target * actual_timespan / target_timespan
        
        return DifficultyUtils.target_to_bits(int(new_target))

    def calculate_block_subsidy(self, block_index: int) -> int:
        """
        Calcula la subvención base para un bloque dado su índice (Halving).
        Regla: La recompensa se reduce a la mitad cada 'halving_interval' bloques.
        """
        # Obtenemos los valores frescos de la configuración
        halving_interval = self._config.halving_interval
        initial_subsidy = self._config.initial_subsidy
        
        # Evitamos división por cero si la configuración está mal (<= 0)
        if halving_interval <= 0:
            # USAMOS EL VALOR DE RESPALDO DESDE CONFIGMANAGER
            # Esta propiedad expone explícitamente el valor DEFAULT_HALVING_INTERVAL = 210000
            fallback = self._config.fallback_halving_interval
            
            logging.warning(f"Intervalo de Halving inválido en config ({halving_interval}). Usando valor por defecto de seguridad: {fallback}")
            halving_interval = fallback

        halvings = block_index // halving_interval
        
        # Bitwise shift para dividir por 2^halvings
        # Ejemplo: 50 >> 1 = 25; 50 >> 2 = 12
        # Si hay demasiados halvings (64+), el subsidio llega a 0.
        if halvings >= 64:
            return 0
            
        subsidy = initial_subsidy >> halvings
        
        return subsidy