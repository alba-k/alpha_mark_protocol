# akm/core/utils/difficulty_utils.py

import logging
from akm.core.config.consensus_config import ConsensusConfig

logger = logging.getLogger(__name__)

class DifficultyUtils:
    @staticmethod
    def _get_max_target() -> int:
        try:
            return ConsensusConfig().max_target
        except Exception:
            # Fallback seguro: Dificultad máxima (Target más alto posible)
            return 0x00000000FFFF0000000000000000000000000000000000000000000000000000

    @staticmethod
    def bits_to_target(bits: str) -> int:
        limit = DifficultyUtils._get_max_target()

        try:
            if not bits or len(bits) != 8:
                return limit

            # Desglose: [Exponente (2)][Mantisa (6)]
            exp = int(bits[:2], 16)
            mant = int(bits[2:], 16)
            
            # Cálculo de dificultad
            target = mant * (1 << (8 * (exp - 3)))
            
            # El target no puede ser más fácil que el límite del Génesis
            return min(target, limit)

        except (ValueError, TypeError, Exception):
            logger.exception(f"Error convirtiendo bits: {bits}")
            return limit

    @staticmethod
    def target_to_bits(target: int) -> str:
        limit = DifficultyUtils._get_max_target()

        try:
            if target < 0:
                raise ValueError("Target negativo.")
            if target == 0:
                return '00000000'
            
            if target > limit:
                target = limit

            # Serialización a bytes (Big Endian)
            target_bytes = target.to_bytes((target.bit_length() + 7) // 8, 'big')
            exponent = len(target_bytes)
            
            # Normalización de la mantisa
            if exponent > 3:
                mantissa_bytes = target_bytes[:3]
            else:
                mantissa_bytes = target_bytes.rjust(3, b'\x00')
                
            # Manejo del bit de signo para evitar targets negativos
            if mantissa_bytes[0] > 0x7f:
                mantissa_bytes = b'\x00' + mantissa_bytes[:2]
                exponent += 1

            # Construcción del string hex final
            mant_hex = mantissa_bytes.hex()[:6].zfill(6)
            exp_hex = f'{exponent:02x}'
            
            return f'{exp_hex}{mant_hex}'

        except Exception:
            logger.exception(f"Fallo técnico calculando bits para target: {target}")
            return "1d00ffff" # Retornamos dificultad por defecto