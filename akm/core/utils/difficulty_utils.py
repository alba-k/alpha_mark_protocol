# akm/core/utils/difficulty_utils.py
'''
class DifficultyUtils:
    Contiene la lógica pura para manejar la dificultad (Bits y Target).
    
    Attributes::
        MAX_TARGET (int): Dificultad mínima aceptada (el target más alto posible),
                          derivada de la configuración central.
    
    Methods::
        bits_to_target(bits) -> int: Convierte bits compactos a número.
        target_to_bits(target) -> str: Convierte número a bits compactos.
'''

from akm.core.config.config_manager import ConfigManager

class DifficultyUtils:
    
    # Target máximo permitido (dificultad más fácil).
    _config = ConfigManager()
    
    # Constantes explícitas para la dificultad inicial estándar ('1d00ffff')
    _GENESIS_MANTISSA: int = 0x00ffff
    _GENESIS_EXPONENT: int = 0x1d
    
    # Cálculo manual seguro del MAX_TARGET
    MAX_TARGET: int = _GENESIS_MANTISSA * (2 ** (8 * (_GENESIS_EXPONENT - 3)))

    @staticmethod
    def bits_to_target(bits: str) -> int:
        """
        Convierte el formato compacto 'bits' al Target numérico.
        """
        try:
            if not bits or len(bits) != 8:
                return DifficultyUtils.MAX_TARGET

            exp = int(bits[:2], 16)
            mant = int(bits[2:], 16)
            
            target = mant * (1 << (8 * (exp - 3)))
            
            # PROTECCIÓN 1: Al leer bits, no permitimos targets mayores al límite
            if target > DifficultyUtils.MAX_TARGET:
                return DifficultyUtils.MAX_TARGET
                
            return target

        except (ValueError, TypeError):
            return DifficultyUtils.MAX_TARGET

    @staticmethod
    def target_to_bits(target: int) -> str:
        """
        Convierte el Target numérico de vuelta al formato compacto 'bits'.
        """
        if target < 0:
            raise ValueError('DifficultyUtils: Target no puede ser negativo.')
        if target == 0:
            return '00000000'
            
        if target > DifficultyUtils.MAX_TARGET:
            target = DifficultyUtils.MAX_TARGET

        # 1. Convertir el Target a bytes (big-endian)
        target_bytes = target.to_bytes((target.bit_length() + 7) // 8, 'big')
        
        exponent = len(target_bytes)
        
        # 2. Normalizar la mantisa a 3 bytes
        if exponent > 3:
            mantissa_bytes = target_bytes[:3]
        else:
            mantissa_bytes = target_bytes.rjust(3, b'\x00')
            
        # 3. Manejo de desbordamiento de signo (Bit más significativo)
        if mantissa_bytes[0] > 0x7f:
            mantissa_bytes = b'\x00' + mantissa_bytes[:2]
            exponent += 1

        # 4. Formateo final
        mant_hex = mantissa_bytes.hex().zfill(6)
        if len(mant_hex) > 6:
             mant_hex = mant_hex[:6]

        exp_hex = f'{exponent:02x}'
        
        return f'{exp_hex}{mant_hex}'