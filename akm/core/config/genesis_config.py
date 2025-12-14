import os

class GenesisConfig:
    """
    Configuración de Datos del Bloque Génesis.
    Contiene los valores "mágicos" para reconstruir el Bloque #0.
    """

    def __init__(self):
        # ==============================================================================
        # 1. PARAMETROS DEL BLOQUE (Header)
        # ==============================================================================
        
        # Altura del bloque génesis (Siempre 0).
        self._index: int = 0
        
        # Timestamp de creación.
        self._timestamp: int = int(os.getenv("AKM_GENESIS_TIMESTAMP", 1231006505))
        
        # Hash del bloque previo (Cadena de ceros).
        self._previous_hash: str = "0" * 64
        
        # Nonce "mágico".
        self._nonce: int = int(os.getenv("AKM_GENESIS_NONCE", 2083236893))
        
        self._empty_hash_placeholder: str = ""

        # ==============================================================================
        # 2. PARAMETROS DE LA TRANSACCIÓN COINBASE (Contenido)
        # ==============================================================================
        
        self._coinbase_input_prev_tx: str = "0" * 64
        self._coinbase_input_index: int = 0xFFFFFFFF
        
        self._coinbase_message: str = os.getenv(
            "AKM_GENESIS_MESSAGE", 
            "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks"
        )

        # Dirección del minero (Satoshi) para el bloque 0.
        self._miner_address: str = os.getenv(
            "AKM_GENESIS_MINER_ADDR", 
            "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa" # Satoshi Address
        )

        self._tx_fee: int = 0

    # ==============================================================================
    # 3. PROPIEDADES (GETTERS)
    # Reformateados a multilínea para evitar errores de sintaxis
    # ==============================================================================

    @property
    def index(self) -> int:
        return self._index

    @property
    def timestamp(self) -> int:
        return self._timestamp

    @property
    def previous_hash(self) -> str:
        return self._previous_hash

    @property
    def nonce(self) -> int:
        return self._nonce

    @property
    def empty_hash_placeholder(self) -> str:
        return self._empty_hash_placeholder
    
    @property
    def coinbase_input_prev_tx(self) -> str:
        return self._coinbase_input_prev_tx

    @property
    def coinbase_input_index(self) -> int:
        return self._coinbase_input_index

    @property
    def coinbase_message(self) -> str:
        return self._coinbase_message
    
    @property
    def miner_address(self) -> str:
        return self._miner_address

    @property
    def tx_fee(self) -> int:
        return self._tx_fee