# akm/core/models/block.py
'''
class Block:
    Entidad central de la cadena. Contenedor inmutable de transacciones confirmadas.

    Attributes::
        index (int): Altura del bloque.
        timestamp (float): Momento de minado.
        previous_hash (str): Enlace al bloque anterior (Chain).
        bits (str): Dificultad objetivo.
        merkle_root (str): Resumen de transacciones.
        nonce (int): Número aleatorio para PoW.
        hash (str): Identificador único del bloque (PoW result).
        transactions (List[Transaction]): Cuerpo del bloque.
'''

from typing import List, Dict, Any
from akm.core.models.transaction import Transaction

class Block:

    def __init__(
        self,
        index: int,
        timestamp: int,
        previous_hash: str,
        bits: str,
        merkle_root: str,
        nonce: int,
        block_hash: str,
        transactions: List[Transaction]
    ):
        self._index: int = index
        self._timestamp: int = timestamp
        self._previous_hash: str = previous_hash
        self._bits: str = bits
        self._merkle_root: str = merkle_root
        self._nonce: int = nonce
        self._hash: str = block_hash
        self._transactions: List[Transaction] = transactions if transactions else []


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

    @property
    def transactions(self) -> List[Transaction]:
        return self._transactions[:]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self._index,
            "timestamp": self._timestamp,
            "previous_hash": self._previous_hash,
            "bits": self._bits,
            "merkle_root": self._merkle_root,
            "nonce": self._nonce,
            "hash": self._hash,
            "transactions": [tx.to_dict() for tx in self._transactions]
        }