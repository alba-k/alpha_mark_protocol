# akm/core/services/transaction_hasher.py

import struct
import hashlib
import logging
from typing import TYPE_CHECKING, Any, Union

# Importamos solo para chequeo de tipos estáticos
if TYPE_CHECKING:
    from akm.core.models.transaction import Transaction # type: ignore

logger = logging.getLogger(__name__)

class TransactionHasher:
    
    @staticmethod
    def _safe_hex_to_bytes(hex_str: Union[str, bytes], length: int = 32) -> bytes:
        """
        Intenta convertir un string a bytes desde hexadecimal con longitud fija.
        """
        if not hex_str:
            return b'\x00' * length
        
        try:
            # BLOQUE 1: Manejo estricto de BYTES
            if isinstance(hex_str, bytes):
                return hex_str[:length].rjust(length, b'\x00')

            # BLOQUE 2: Manejo estricto de STRING
            if isinstance(hex_str, str):
                clean_hex = hex_str.replace("0x", "")
                padded_hex = clean_hex.zfill(length * 2)
                result = bytes.fromhex(padded_hex)
                return result[:length]

            # Si llega algo raro
            return b'\x00' * length

        except ValueError as e:
            logger.warning(f"⚠️ [Hasher] Error convirtiendo Hex a Bytes: {hex_str} - {e}")
            return b'\x00' * length

    @staticmethod
    def _ensure_script_bytes(data: Union[str, bytes]) -> bytes:
        """
        [FIX CRÍTICO] Convierte dinámicamente el script a bytes reales.
        """
        # Caso 1: Ya es bytes
        if isinstance(data, bytes):
            return data
            
        # Caso 2: Es string (Texto Hexadecimal)
        if isinstance(data, str):
            try:
                return bytes.fromhex(data)
            except ValueError:
                logger.error(f"❌ [Hasher] Error decodificando script inválido: {data[:20]}...")
                return b''
                
        # Caso 3: Tipo desconocido
        logger.warning(f"⚠️ [Hasher] Tipo de dato desconocido para script: {type(data)}")
        return b''

    @staticmethod
    def calculate(transaction: Any) -> str: 
        """
        Calcula el hash doble SHA-256 de la transacción.
        """
        try:
            payload = bytearray()

            # 1. Timestamp (8 bytes, Little Endian)
            payload.extend(struct.pack('<Q', int(transaction.timestamp)))

            # 2. Inputs Count (4 bytes)
            payload.extend(struct.pack('<I', len(transaction.inputs)))
            
            # --- CORRECCIÓN LÍNEA 82 ---
            # Quitamos 'enumerate' porque 'i' no se usa
            for inp in transaction.inputs:
                
                # A. Previous TX Hash (32 bytes fijos)
                prev_tx_bytes = TransactionHasher._safe_hex_to_bytes(
                    inp.previous_tx_hash, 32
                )
                payload.extend(prev_tx_bytes)

                # B. Output Index (4 bytes)
                payload.extend(struct.pack('<I', inp.output_index))
                
                # C. Script Sig (Var Int / Length Prefixed)
                script_sig_bytes = TransactionHasher._ensure_script_bytes(inp.script_sig)
                
                payload.extend(struct.pack('<I', len(script_sig_bytes)))
                payload.extend(script_sig_bytes)

            # 3. Outputs Count (4 bytes)
            payload.extend(struct.pack('<I', len(transaction.outputs)))
            
            # --- CORRECCIÓN LÍNEA 107 ---
            # Quitamos 'enumerate' aquí también
            for out in transaction.outputs:
                # A. Value (8 bytes)
                payload.extend(struct.pack('<Q', int(out.value_alba)))
                
                # B. Script Pubkey (Var Int / Length Prefixed)
                script_pubkey_bytes = TransactionHasher._ensure_script_bytes(out.script_pubkey)

                payload.extend(struct.pack('<I', len(script_pubkey_bytes)))
                payload.extend(script_pubkey_bytes)

            # 4. Fee (8 bytes)
            fee_val = int(getattr(transaction, 'fee', 0))
            payload.extend(struct.pack('<Q', fee_val))

            # --- DOUBLE SHA-256 ---
            h1 = hashlib.sha256(payload).digest()
            tx_hash = hashlib.sha256(h1).hexdigest()
            
            return tx_hash

        except Exception as e:
            logger.exception(f"❌ [Hasher] Error CRÍTICO calculando hash: {e}")
            return ""