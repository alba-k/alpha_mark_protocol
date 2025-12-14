# akm/core/services/transaction_hasher.py

import struct
import hashlib
import logging

from akm.core.interfaces.hasher_protocols import TransactionProtocol

logger = logging.getLogger(__name__)

class TransactionHasher:
    

    @staticmethod
    def calculate(transaction: TransactionProtocol) -> str:
        try:
            payload = bytearray()

            payload.extend(struct.pack('<Q', transaction.timestamp))

            # 2. Inputs
            payload.extend(struct.pack('<I', len(transaction.inputs)))
            
            for inp in transaction.inputs:
                try:
                    payload.extend(bytes.fromhex(inp.previous_tx_hash))
                except ValueError:
                    payload.extend(b'\x00' * 32)
                
                payload.extend(struct.pack('<I', inp.output_index))
                
                script_len = len(inp.script_sig)
                payload.extend(struct.pack('<I', script_len))
                payload.extend(inp.script_sig)

            # 3. Outputs
            payload.extend(struct.pack('<I', len(transaction.outputs)))
            
            for out in transaction.outputs:
                payload.extend(struct.pack('<Q', out.value_alba))
                
                script_len = len(out.script_pubkey)
                payload.extend(struct.pack('<I', script_len))
                payload.extend(out.script_pubkey)

            # 4. Fee
            payload.extend(struct.pack('<Q', transaction.fee))

            # --- DOUBLE SHA-256 ---
            h1 = hashlib.sha256(payload).digest()
            return hashlib.sha256(h1).hexdigest()

        except Exception as e:
            logger.exception(f"Error crítico de serialización en transacción: {e}")
            return ""