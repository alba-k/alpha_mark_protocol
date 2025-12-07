# akm/core/services/confirmation_service.py
'''
class ConfirmationService:
    Servicio de consulta de seguridad (Finalidad).
    Calcula la profundidad de un bloque en la cadena canónica.

    Methods::
        get_confirmations(block_hash) -> int:
            Retorna número de confirmaciones (0 = no confirmado/huerfano).
'''

from typing import Optional
from akm.core.models.blockchain import Blockchain
from akm.core.models.block import Block

class ConfirmationService:

    def __init__(self, blockchain: Blockchain):
        self._blockchain = blockchain

    def get_confirmations(self, block_hash: str) -> int:
    
        # 1. Buscar el bloque en la cadena principal
        target_block: Optional[Block] = None
        
        # En producción esto usaría un índice hash->altura O(1)
        for block in self._blockchain.chain:
            if block.hash == block_hash:
                target_block = block
                break
        
        # Si no está en la cadena principal (es huérfano o desconocido)
        if not target_block:
            return 0

        # 2. Calcular profundidad
        # Si la cadena tiene bloques, obtenemos el índice del último
        last_block = self._blockchain.last_block
        tip_height = last_block.index if last_block else 0
        
        confirmations = tip_height - target_block.index + 1
        return confirmations