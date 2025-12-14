# akm/core/interfaces/hasher_protocols.py

from typing import Protocol, Sequence

class TxInputProtocol(Protocol):
    """Contrato para la serialización de entradas de transacción."""
    @property
    def previous_tx_hash(self) -> str: ...
    @property
    def output_index(self) -> int: ...
    @property
    def script_sig(self) -> bytes: ...

class TxOutputProtocol(Protocol):
    """Contrato para la serialización de salidas de transacción."""
    @property
    def value_alba(self) -> int: ...
    @property
    def script_pubkey(self) -> bytes: ...

class TransactionProtocol(Protocol):
    """
    Define la estructura mínima que debe tener una Transacción 
    para ser procesada por el TransactionHasher.
    """
    @property
    def timestamp(self) -> int: ...
    
    @property
    def fee(self) -> int: ...
    
    @property
    def inputs(self) -> Sequence[TxInputProtocol]: ...
    
    @property
    def outputs(self) -> Sequence[TxOutputProtocol]: ...

class BlockHeaderProtocol(Protocol):
    """
    Define el 'molde' binario de un bloque. 
    Permite que el BlockHasher trabaje sin depender de la clase Block completa.
    """
    @property
    def index(self) -> int: ...
    @property
    def previous_hash(self) -> str: ...
    @property
    def merkle_root(self) -> str: ...
    @property
    def timestamp(self) -> int: ...
    @property
    def bits(self) -> str: ...
    @property
    def nonce(self) -> int: ...