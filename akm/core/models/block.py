# akm/core/models/block.py
from typing import List, Dict, Any
from akm.core.models.block_header import BlockHeader
from akm.core.models.transaction import Transaction

class Block(BlockHeader):
    """
    [Clase Hija - Child]
    Representa un bloque completo. 
    Hereda los metadatos de BlockHeader y añade el cuerpo (transacciones).
    """

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
        # 1. Llamada al constructor del Padre (super)
        super().__init__(
            index=index,
            timestamp=timestamp,
            previous_hash=previous_hash,
            bits=bits,
            merkle_root=merkle_root,
            nonce=nonce,
            block_hash=block_hash
        )
        
        # 2. Atributo exclusivo de la clase Hija
        self._transactions: List[Transaction] = transactions if transactions else []

    @property
    def transactions(self) -> List[Transaction]:
        return self._transactions[:]

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa el bloque completo (Header + Body).
        """
        # Reutilizamos la lógica del padre
        data = self.to_dict_header()
        
        # Añadimos lo específico del hijo
        data["transactions"] = [tx.to_dict() for tx in self._transactions]
        return data