# akm/core/config/protocol_constants.py
from typing import Final

class ProtocolConstants:
    """
    Vocabulario inmutable del protocolo P2P.
    Centraliza los tipos de mensajes con tipado estricto.
    """
    # --- Tipos de Mensajes Básicos ---
    MSG_HANDSHAKE: Final[str] = "HANDSHAKE"
    MSG_TX: Final[str]        = "TRANSACTION"
    MSG_BLOCK: Final[str]     = "BLOCK"
    
    # --- Protocolo SPV (Light Clients) ---
    MSG_GET_HEADERS: Final[str]      = "GET_HEADERS"      # Móvil pide headers
    MSG_HEADERS: Final[str]          = "HEADERS"          # Nodo responde con headers
    
    # --- Protocolo de Verificación de Pagos (Merkle) ---
    MSG_GET_MERKLE_PROOF: Final[str] = "GET_MERKLE_PROOF" # Móvil pide probar una TX
    MSG_MERKLE_PROOF: Final[str]     = "MERKLE_PROOF"     # Nodo entrega la prueba
    
    # --- Metadatos ---
    PROTOCOL_VERSION: Final[int] = 1
    USER_AGENT: Final[str]       = "AlphaMark/1.0-Core"