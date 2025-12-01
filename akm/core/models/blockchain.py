# akm/core/models/blockchain.py
'''
class Blockchain:
    Gestor principal de la historia.

    Attributes::
        _chain (List[Block]): La secuencia ordenada de bloques.

    Methods::
        add_block(block) -> None:
            Añade un nuevo bloque a la punta de la cadena.
        replace_chain(new_chain) -> None:
            Mecanismo de consenso para reemplazar la historia local por una más larga (Reorg).
        last_block (Property) -> Optional[Block]:
            Acceso rápido al último bloque (Tip of the chain).
        chain (Property) -> List[Block]:
            Retorna una copia defensiva de la cadena completa.
'''

from typing import List, Optional
from akm.core.models.block import Block

class Blockchain:

    def __init__(self):
        self._chain: List[Block] = []

    def add_block(self, block: Block) -> None:
        self._chain.append(block)

    def replace_chain(self, new_chain: List[Block]) -> None:
        self._chain = new_chain[:] 

    @property
    def last_block(self) -> Optional[Block]:
        if not self._chain:
            return None
        return self._chain[-1]

    @property
    def chain(self) -> List[Block]:
        return self._chain[:]
    
    def __len__(self) -> int:
        return len(self._chain)