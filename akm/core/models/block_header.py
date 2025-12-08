# akm/core/models/block_header.py
from typing import Dict, Any

class BlockHeader:
    """
    [Clase Base - Parent]
    Contiene solo los metadatos del bloque.
    Es lo único que almacena y valida el Nodo Móvil (SPV).
    """
    def __init__(
        self,
        index: int,
        timestamp: int,
        previous_hash: str,
        bits: str,
        merkle_root: str,
        nonce: int,
        block_hash: str
    ):
        self._index = index
        self._timestamp = timestamp
        self._previous_hash = previous_hash
        self._bits = bits
        self._merkle_root = merkle_root
        self._nonce = nonce
        self._hash = block_hash

    # --- Getters (Propiedades Comunes) ---
    @property
    def index(self) -> int: return self._index
    @property
    def timestamp(self) -> int: return self._timestamp
    @property
    def previous_hash(self) -> str: return self._previous_hash
    @property
    def bits(self) -> str: return self._bits
    @property
    def merkle_root(self) -> str: return self._merkle_root
    @property
    def nonce(self) -> int: return self._nonce
    @property
    def hash(self) -> str: return self._hash

    def to_dict_header(self) -> Dict[str, Any]:
        """Serializa solo la cabecera."""
        return {
            "index": self._index,
            "timestamp": self._timestamp,
            "previous_hash": self._previous_hash,
            "bits": self._bits,
            "merkle_root": self._merkle_root,
            "nonce": self._nonce,
            "hash": self._hash
        }