# akm/core/config/protocol_constants.py
from typing import Final

class ProtocolConstants:
    """
    Vocabulario inmutable del protocolo P2P.
    Centraliza los tipos de mensajes con tipado estricto para evitar errores.
    """
    # --- Tipos de Mensajes ---
    MSG_HANDSHAKE: Final[str] = "HANDSHAKE"
    MSG_TX: Final[str]        = "TRANSACTION"
    MSG_BLOCK: Final[str]     = "BLOCK"
    
    # (Opcionales para futuro uso en sincronización)
    MSG_INV: Final[str]       = "INVENTORY"   
    MSG_GET_DATA: Final[str]  = "GET_DATA"    
    
    # --- Metadatos del Nodo ---
    PROTOCOL_VERSION: Final[int] = 1
    # Usamos el nombre "Core" para identificar que es el nodo completo
    USER_AGENT: Final[str]       = "AlphaMark/1.0-Core"