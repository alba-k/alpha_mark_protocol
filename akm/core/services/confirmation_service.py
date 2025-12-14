# akm/core/services/confirmation_service.py

import logging
from typing import Optional

from akm.core.models.blockchain import Blockchain
from akm.core.models.block import Block

logger = logging.getLogger(__name__)

class ConfirmationService:

    def __init__(self, blockchain: Blockchain) -> None:
        self._blockchain = blockchain
        logger.info("Servicio de confirmaciones activo.")

    def get_confirmations(self, block_hash: str) -> int:
        try:
            target_block: Optional[Block] = self._blockchain.get_block_by_hash(block_hash)
            if not target_block: 
                return 0

            tip = self._blockchain.last_block
            if not tip: 
                return 0 
                
            tip_height = tip.index

            if target_block.index > tip_height: 
                return 0

            confirmations = tip_height - target_block.index + 1
            
            return confirmations

        except Exception:
            logger.exception(f"Error al calcular confirmaciones para hash: {block_hash[:8]}")
            return 0