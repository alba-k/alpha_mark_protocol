# akm/core/services/transaction_hasher.py
import struct
import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from akm.core.models.transaction import Transaction

class TransactionHasher:
    """
    Genera el ID único (TXID) usando serialización BINARIA determinista.
    Reemplaza JSON para garantizar que las firmas digitales sean válidas.
    """

    @staticmethod
    def calculate(transaction: 'Transaction') -> str:
        payload = bytearray()

        # 1. Timestamp (8 bytes, Little Endian unsigned long long)
        payload.extend(struct.pack('<Q', transaction.timestamp))

        # 2. Inputs (Cantidad + Contenido)
        payload.extend(struct.pack('<I', len(transaction.inputs)))
        for inp in transaction.inputs:
            # Prev Hash (32 bytes) - Asumimos hex string
            try:
                payload.extend(bytes.fromhex(inp.previous_tx_hash))
            except ValueError:
                payload.extend(b'\x00' * 32)
            
            # Index (4 bytes)
            payload.extend(struct.pack('<I', inp.output_index))
            
            # ScriptSig Length + Content (Bytes puros)
            script_len = len(inp.script_sig)
            payload.extend(struct.pack('<I', script_len))
            payload.extend(inp.script_sig)

        # 3. Outputs (Cantidad + Contenido)
        payload.extend(struct.pack('<I', len(transaction.outputs)))
        for out in transaction.outputs:
            # Value (8 bytes - Albas)
            payload.extend(struct.pack('<Q', out.value_alba))
            
            # ScriptPubKey Length + Content (Bytes puros)
            script_len = len(out.script_pubkey)
            payload.extend(struct.pack('<I', script_len))
            payload.extend(out.script_pubkey)

        # 4. Fee (8 bytes)
        payload.extend(struct.pack('<Q', transaction.fee))

        # --- DOUBLE SHA-256 (Estándar Bitcoin) ---
        h1 = hashlib.sha256(payload).digest()
        return hashlib.sha256(h1).hexdigest()