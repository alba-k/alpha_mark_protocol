# core/scripting/opcodes.py

from enum import IntEnum, unique

@unique  # Decorador que evita valores duplicados por accidente
class Opcodes(IntEnum):
    """
    Definición de Operaciones de la Stack Machine.
    Heredar de IntEnum permite que se comporten como enteros en comparaciones.
    """
    
    # --- CONSTANTES ---
    OP_0 = 0x00
    OP_TRUE = 0x51  # 1
    
    # --- MANIPULACIÓN DE PILA ---
    OP_DROP = 0x75
    OP_DUP = 0x76
    
    # --- OPERADORES LÓGICOS ---
    OP_EQUAL = 0x87
    OP_EQUALVERIFY = 0x88
    
    # --- CRIPTOGRAFÍA ---
    OP_HASH160 = 0xa9
    OP_CHECKSIG = 0xac

    @classmethod
    def get_name(cls, code: int) -> str:
        """
        Devuelve el nombre legible del opcode.
        Ejemplo: get_name(0x76) -> 'OP_DUP'
        """
        try:
            return cls(code).name
        except ValueError:
            return f"OP_UNKNOWN({code})"