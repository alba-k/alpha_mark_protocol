# akm/core/models/block.py

import logging
from typing import List, Dict, Any

from akm.core.models.block_header import BlockHeader
from akm.core.models.transaction import Transaction

logger = logging.getLogger(__name__)

class Block(BlockHeader):

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
    ) -> None:
        try:
            super().__init__(
                index=index,
                timestamp=timestamp,
                previous_hash=previous_hash,
                bits=bits,
                merkle_root=merkle_root,
                nonce=nonce,
                block_hash=block_hash
            )
            
            self._transactions: List[Transaction] = transactions if transactions else []

        except Exception:
            logger.exception(f"Error crítico en la estructura del Bloque #{index}")

    @property
    def transactions(self) -> List[Transaction]: return self._transactions[:]

    @property
    def block_hash(self) -> str:
        return self._hash

    def to_dict(self) -> Dict[str, Any]:
        """
        Estructura anidada para el Repositorio.
        Separamos 'header' de 'transactions'.
        """
        return {
            "header": self.to_dict_header(),
            "transactions": [tx.to_dict() for tx in self._transactions]
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Block':
        """Reconstruye un objeto Block desde el diccionario de la DB."""
        header = data['header']
        
        # [CORRECCIÓN] Definimos explícitamente el tipo de la lista
        # Esto elimina el error "Type of append is partially unknown"
        tx_list: List[Transaction] = []
        
        if 'transactions' in data:
            for tx_data in data['transactions']:
                tx_list.append(Transaction.from_dict(tx_data))

        return Block(
            index=header['index'],
            timestamp=header['timestamp'],
            previous_hash=header['previous_hash'],
            bits=header.get('bits') or str(header.get('difficulty')), # Compatibilidad
            merkle_root=header['merkle_root'],
            nonce=header['nonce'],
            block_hash=header['hash'],
            transactions=tx_list
        )