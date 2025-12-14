# akm/core/scripting/opcodes.py

import logging
from enum import IntEnum, unique

logger = logging.getLogger(__name__)

@unique
class Opcodes(IntEnum):
    
    # --- CONSTANTES ---
    OP_0 = 0x00         # Empuja un 0 a la pila
    OP_TRUE = 0x51      # Empuja un 1 (True) a la pila

    # --- MANIPULACIÓN DE PILA ---
    OP_DROP = 0x75      # Elimina el elemento superior
    OP_DUP = 0x76       # Duplica el elemento superior
    
    # --- OPERADORES LÓGICOS ---
    OP_EQUAL = 0x87     # Compara los dos elementos superiores
    OP_EQUALVERIFY = 0x88 # OP_EQUAL seguido de una interrupción si es falso
    
    # --- CRIPTOGRAFÍA ---
    OP_HASH160 = 0xa9   # RIPEMD160(SHA256(item))
    OP_CHECKSIG = 0xac  # Verifica firma ECDSA contra clave pública

    @classmethod
    def get_name(cls, code: int) -> str:
        try:
            return cls(code).name
        except ValueError:
            logger.exception(f"Instrucción de script inválida detectada: {hex(code)}")
            return f"OP_UNKNOWN({hex(code)})"