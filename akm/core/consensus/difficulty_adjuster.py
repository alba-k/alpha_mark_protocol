# akm/core/consensus/difficulty_adjuster.py
'''
class DifficultyAdjuster:
    Lógica de Consenso para el ajuste dinámico de la dificultad (Proof-of-Work).
    Mantiene el tiempo de bloque estable ajustando el Target según la potencia de la red.

    Methods::
        calculate_new_bits(prev_adj_block, last_block) -> str:
            Calcula los bits de dificultad para el siguiente periodo basándose en el tiempo transcurrido.
'''

import logging
from akm.core.models.block import Block
from akm.core.config.config_manager import ConfigManager
from akm.core.utils.difficulty_utils import DifficultyUtils

# Configuración de logs
logging.basicConfig(level=logging.INFO, format='[DiffAdjuster] %(message)s')

class DifficultyAdjuster:

    def __init__(self):
        self._config = ConfigManager()

    def calculate_new_bits(self, prev_adjustment_block: Block, last_block: Block) -> str:

        # 1. Validación de Integridad
        if not prev_adjustment_block or not last_block:
            raise ValueError("DifficultyAdjuster: Se requieren bloques válidos para el ajuste.")

        # 2. Calcular Tiempo Real Transcurrido (Actual Timespan)
        # Diferencia entre el último bloque del ciclo y el bloque donde empezó el ciclo.
        actual_timespan = last_block.timestamp - prev_adjustment_block.timestamp
        
        # 3. Calcular Tiempo Esperado (Target Timespan)
        # Ej: 100 bloques * 60 seg = 6000 segundos esperados
        target_timespan = self._config.difficulty_adjustment_interval * self._config.target_block_time_sec

        # --- PROTECCIÓN CONTRA VARIACIÓN EXTREMA (Retargeting Limiting) ---
        # Para evitar oscilaciones violentas, limitamos el ajuste (como Bitcoin: máx x4, mín /4).
        if actual_timespan < target_timespan / 4:
            actual_timespan = target_timespan / 4
        if actual_timespan > target_timespan * 4:
            actual_timespan = target_timespan * 4

        # 4. Calcular Nuevo Target
        # Fórmula: Nuevo = Viejo * (Tiempo Real / Tiempo Esperado)
        # Si tardaron mucho (Real > Esperado) -> Ratio > 1 -> Target aumenta (Dificultad baja/más fácil).
        # Si tardaron poco (Real < Esperado) -> Ratio < 1 -> Target disminuye (Dificultad sube/más difícil).
        
        previous_target = DifficultyUtils.bits_to_target(last_block.bits)
        new_target = previous_target * actual_timespan / target_timespan
        
        # 5. Convertir a entero y Formatear
        return DifficultyUtils.target_to_bits(int(new_target))