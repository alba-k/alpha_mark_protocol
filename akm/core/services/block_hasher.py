# akm/core/services/block_hasher.py
'''
class BlockHasher:
    Calcula el hash del encabezado del bloque.

    Methods::
        calculate(block) -> str:
            Serializa la cabecera y aplica Doble SHA-256.
'''

import json
from typing import Dict, Any
from akm.core.models.block import Block
from akm.core.utils.crypto_utility import CryptoUtility

class BlockHasher:

    @staticmethod
    def calculate(block: Block) -> str:
        header_data: Dict[str, Any] = {
            "index": block.index,
            "timestamp": block.timestamp,
            "previous_hash": block.previous_hash,
            "bits": block.bits,
            "merkle_root": block.merkle_root,
            "nonce": block.nonce
        }

        serialized_header = json.dumps(header_data, sort_keys=True)
        return CryptoUtility.double_sha256(serialized_header)