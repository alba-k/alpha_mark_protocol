# akm/core/services/transaction_hasher.py
import struct
import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from akm.core.models.transaction import Transaction

class TransactionHasher:
    """
    Genera el ID único (TXID) usando serialización binaria determinista (Double SHA-256).
    Reemplaza la serialización JSON para garantizar compatibilidad con firmas.
    """

    @staticmethod
    def calculate(transaction: 'Transaction') -> str:
        payload = bytearray()

        # 1. Timestamp (8 bytes, Little Endian)
        payload.extend(struct.pack('<Q', transaction.timestamp))

        # 2. Inputs (Cantidad + Contenido)
        payload.extend(struct.pack('<I', len(transaction.inputs)))
        for inp in transaction.inputs:
            # Prev Hash (32 bytes)
            try:
                payload.extend(bytes.fromhex(inp.previous_tx_hash))
            except ValueError:
                payload.extend(b'\x00' * 32)
            
            # Index + ScriptSig
            payload.extend(struct.pack('<I', inp.output_index))
            payload.extend(struct.pack('<I', len(inp.script_sig)))
            payload.extend(inp.script_sig)

        # 3. Outputs (Cantidad + Contenido)
        payload.extend(struct.pack('<I', len(transaction.outputs)))
        for out in transaction.outputs:
            # Value (Albas) + ScriptPubKey
            payload.extend(struct.pack('<Q', out.value_alba))
            payload.extend(struct.pack('<I', len(out.script_pubkey)))
            payload.extend(out.script_pubkey)

        # 4. Fee (8 bytes)
        payload.extend(struct.pack('<Q', transaction.fee))

        # Double SHA-256
        h1 = hashlib.sha256(payload).digest()
        return hashlib.sha256(h1).hexdigest()