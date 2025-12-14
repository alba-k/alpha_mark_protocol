# akm/core/validators/chain_validator.py

import logging
from typing import List
from akm.core.models.block import Block

logger = logging.getLogger(__name__)

class ChainValidator:

    @staticmethod
    def verify_chain_links(chain: List[Block]) -> bool:
        try:
            if len(chain) <= 1:
                return True

            for i in range(1, len(chain)):
                current_block = chain[i]
                previous_block = chain[i - 1]

                if current_block.previous_hash != previous_block.hash:
                    logger.info(
                        f"Quiebre de enlace en bloque #{current_block.index}: "
                        f"Hash previo incorrecto."
                    )
                    return False
                
                if current_block.index != previous_block.index + 1:
                    logger.info(
                        f"Quiebre de secuencia: Bloque #{current_block.index} "
                        f"no sigue al #{previous_block.index}."
                    )
                    return False

            logger.info(f"Integridad de cadena verificada ({len(chain)} bloques).")
            return True

        except Exception:
            logger.exception("Bug detectado durante la verificación de enlaces de cadena")
            return False