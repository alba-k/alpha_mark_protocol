# akm/core/validators/chain_validator.py
'''
class ChainValidator:
    Servicio de utilidad estática para validar la integridad estructural de una cadena.
    Verifica que los eslabones (hashes) conecten perfectamente.

    Methods::
        verify_chain_links(chain) -> bool:
            Recorre la lista de bloques verificando la continuidad de hashes e índices.
'''

from typing import List
from akm.core.models.block import Block

class ChainValidator:

    @staticmethod
    def verify_chain_links(chain: List[Block]) -> bool:
        if len(chain) <= 1:
            return True

        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i - 1]

            if current_block.previous_hash != previous_block.hash:
                return False

            if current_block.index != previous_block.index + 1:
                return False

        return True