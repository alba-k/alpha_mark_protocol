# akm/core/utils/difficulty_utils.py
'''
class DifficultyUtils:
    Contiene la lógica pura para manejar la dificultad (Bits y Target).
    Ahora obtiene el MAX_TARGET dinámicamente de la configuración.
'''

from akm.core.config.config_manager import ConfigManager

class DifficultyUtils:
    
    # Eliminamos constantes estáticas hardcodeadas.
    # Usamos un método helper para obtener el valor fresco.

    @staticmethod
    def _get_max_target() -> int:
        """Helper privado para obtener el techo de dificultad actual."""
        # Instanciamos ConfigManager (es Singleton) y accedemos a consensus.max_target
        return ConfigManager().consensus.max_target

    @staticmethod
    def bits_to_target(bits: str) -> int:
        """
        Convierte 'bits' a Target numérico.
        """
        # Obtenemos el límite real de la configuración
        limit = DifficultyUtils._get_max_target()

        try:
            if not bits or len(bits) != 8:
                return limit

            exp = int(bits[:2], 16)
            mant = int(bits[2:], 16)
            
            target = mant * (1 << (8 * (exp - 3)))
            
            # PROTECCIÓN: Si el target calculado es más fácil que el límite, lo topamos.
            if target > limit:
                return limit
                
            return target

        except (ValueError, TypeError):
            return limit

    @staticmethod
    def target_to_bits(target: int) -> str:
        """
        Convierte Target numérico a 'bits'.
        """
        limit = DifficultyUtils._get_max_target()

        if target < 0:
            raise ValueError('DifficultyUtils: Target no puede ser negativo.')
        if target == 0:
            return '00000000'
            
        # Si la dificultad es demasiado baja (número muy grande), la ajustamos al límite.
        if target > limit:
            target = limit

        target_bytes = target.to_bytes((target.bit_length() + 7) // 8, 'big')
        exponent = len(target_bytes)
        
        if exponent > 3:
            mantissa_bytes = target_bytes[:3]
        else:
            mantissa_bytes = target_bytes.rjust(3, b'\x00')
            
        if mantissa_bytes[0] > 0x7f:
            mantissa_bytes = b'\x00' + mantissa_bytes[:2]
            exponent += 1

        mant_hex = mantissa_bytes.hex().zfill(6)
        if len(mant_hex) > 6:
             mant_hex = mant_hex[:6]

        exp_hex = f'{exponent:02x}'
        
        return f'{exp_hex}{mant_hex}'