# akm/core/utils/crypto_utility.py

import hashlib
import logging
from typing import Union

logger = logging.getLogger(__name__)

class CryptoUtility:
    @staticmethod
    def sha256(data: Union[str, bytes]) -> str:
        """Retorna el hash SHA-256 hexadecimal."""
        try:
            data_bytes = CryptoUtility._to_bytes(data)
            return hashlib.sha256(data_bytes).hexdigest()
        except Exception:
            logger.exception("Error en cálculo SHA256")
            return ""

    @staticmethod
    def double_sha256(data: Union[str, bytes]) -> str:
        """Aplica Doble SHA-256 (estándar PoW)."""
        try:
            data_bytes = CryptoUtility._to_bytes(data)
            first_hash = hashlib.sha256(data_bytes).digest()
            return hashlib.sha256(first_hash).hexdigest()
        except Exception:
            logger.exception("Error en cálculo Double SHA256")
            return ""

    @staticmethod
    def hash160(data: Union[str, bytes]) -> str:
        """RIPEMD160(SHA256(data)) para direcciones."""
        try:
            data_bytes = CryptoUtility._to_bytes(data)
            
            # 1. SHA-256
            sha_hash_bytes = hashlib.sha256(data_bytes).digest()
            
            # 2. RIPEMD-160
            ripemd_obj = hashlib.new('ripemd160')
            ripemd_obj.update(sha_hash_bytes)
            
            return ripemd_obj.hexdigest()
        except Exception:
            
            logger.exception("Error en cálculo HASH160")
            return ""

    @staticmethod
    def _to_bytes(data: Union[str, bytes]) -> bytes:
        """Normaliza entrada a bytes de forma segura."""
        if isinstance(data, str):
            return data.encode('utf-8')
        if isinstance(data, bytes):
            return data
        raise TypeError(f"Tipo no soportado para hashing: {type(data)}")