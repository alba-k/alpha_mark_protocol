# akm/core/managers/mining_manager.py

import struct
import hashlib
import logging

from akm.core.interfaces.hasher_protocols import BlockHeaderProtocol

logger = logging.getLogger(__name__)

class BlockHasher:

    @staticmethod
    def calculate(header: BlockHeaderProtocol) -> str:
        try:
            payload = bytearray()

            # 1. Index / Altura (4 bytes unsigned int)
            payload.extend(struct.pack('<I', header.index))

            # 2. Previous Hash (32 bytes)
            if header.previous_hash == "0": 
                payload.extend(b'\x00' * 32)
            else:
                try:
                    payload.extend(bytes.fromhex(header.previous_hash))
                except ValueError:
                    payload.extend(b'\x00' * 32)

            # 3. Merkle Root (32 bytes)
            try:
                payload.extend(bytes.fromhex(header.merkle_root))
            except ValueError:
                payload.extend(b'\x00' * 32)

            # 4. Timestamp (8 bytes unsigned long long)
            payload.extend(struct.pack('<Q', header.timestamp))

            # 5. Bits / Dificultad (4 bytes hex a bytes)
            try:
                payload.extend(bytes.fromhex(header.bits))
            except ValueError:
                payload.extend(b'\x00\x00\x00\x00')

            # 6. Nonce (4 bytes unsigned int)
            payload.extend(struct.pack('<I', header.nonce))

            # --- DOBLE SHA-256 ---
            h1 = hashlib.sha256(payload).digest()
            return hashlib.sha256(h1).hexdigest()

        except Exception:
            # Usamos getattr por seguridad si el objeto falla, aunque el protocolo lo garantiza
            idx = getattr(header, 'index', 'Unknown')
            logger.exception(f"Error crítico de serialización en Bloque #{idx}")
            return ""