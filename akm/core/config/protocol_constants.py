# akm/core/config/protocol_constants.py

from typing import Final

class ProtocolConstants:
    """
    Vocabulario inmutable del protocolo.
    Centraliza:
    1. Reglas de Transacciones (Coinbase, Estructura).
    2. Tipos de Mensajes P2P (Red).
    """

    # ==========================================================================
    # 1. METADATOS GLOBALES
    # ==========================================================================
    PROTOCOL_VERSION: Final[int] = 1
    USER_AGENT: Final[str]       = "AlphaMark/1.0-Core"

    # ==========================================================================
    # 2. REGLAS DE ESTRUCTURA DE DATOS (Lo que faltaba)
    # ==========================================================================
    
    # Identificadores de Coinbase (Para TransactionFactory y Validadores)
    # Una transacción Coinbase siempre apunta a este Hash de inputs ("0000...")
    COINBASE_PREV_HASH: Final[str] = "0" * 64
    
    # El índice siempre es el máximo entero unsigned de 4 bytes
    COINBASE_INDEX: Final[int] = 0xFFFFFFFF

    # ==========================================================================
    # 3. PROTOCOLO DE RED (Mensajes P2P)
    # ==========================================================================
    
    # --- Tipos de Mensajes Básicos ---
    MSG_HANDSHAKE: Final[str] = "HANDSHAKE"
    MSG_TX: Final[str]        = "TRANSACTION"
    MSG_BLOCK: Final[str]     = "BLOCK"
    
    # --- Protocolo de Sincronización (Nodes) ---
    MSG_SYNC_REQUEST: Final[str]  = "SYNC_REQUEST"
    MSG_SYNC_BATCH: Final[str]    = "SYNC_BATCH"
    
    # --- Protocolo SPV (Light Clients - Headers) ---
    MSG_GET_HEADERS: Final[str]      = "GET_HEADERS"
    MSG_HEADERS: Final[str]          = "HEADERS"
    
    # --- Protocolo SPV (Light Clients - Wallet Data) ---
    MSG_GET_UTXOS: Final[str]        = "GET_UTXOS"   # SPV pide sus monedas
    MSG_UTXO_SET: Final[str]         = "UTXO_SET"    # Full Node responde con monedas
    
    # --- Protocolo de Verificación de Pagos (Merkle) ---
    MSG_GET_MERKLE_PROOF: Final[str] = "GET_MERKLE_PROOF"
    MSG_MERKLE_PROOF: Final[str]     = "MERKLE_PROOF"