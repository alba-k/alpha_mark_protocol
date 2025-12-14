# akm/core/consensus/difficulty_adjuster.py
import logging

# Modelos y Configuración
from akm.core.models.block import Block
from akm.core.config.consensus_config import ConsensusConfig

# Utilidades Matemáticas
from akm.core.utils.difficulty_utils import DifficultyUtils

logger = logging.getLogger(__name__)

class DifficultyAdjuster:

    def __init__(self) -> None:
        try:
            self._config = ConsensusConfig()
        except Exception:
            logger.exception("Error al cargar configuración de consenso")

    def calculate_new_bits(self, first_block_of_epoch: Block, last_block: Block) -> str:
        
        try:
            if not first_block_of_epoch or not last_block:
                raise ValueError("Bloques de referencia nulos.")

            target_ts = self._config.difficulty_adjustment_interval * self._config.target_block_time_sec
            actual_ts = last_block.timestamp - first_block_of_epoch.timestamp

            if actual_ts < target_ts // 4:
                actual_ts = target_ts // 4
            elif actual_ts > target_ts * 4:
                actual_ts = target_ts * 4

            current_target = DifficultyUtils.bits_to_target(last_block.bits)
            new_target = (current_target * actual_ts) // target_ts

            if new_target > self._config.max_target:
                new_target = self._config.max_target

            new_bits = DifficultyUtils.target_to_bits(int(new_target))

            logger.info(
                f"Ajuste de dificultad: {last_block.bits} -> {new_bits} "
                f"(Real: {actual_ts}s | Obj: {target_ts}s)"
            )

            return new_bits

        except Exception:
            logger.exception("Bug crítico en el cálculo de ajuste de dificultad")
            return last_block.bits if last_block else "1d00ffff"