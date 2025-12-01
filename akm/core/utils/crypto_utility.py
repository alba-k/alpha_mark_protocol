# akm/core/utils/crypto_utility.py
'''
class CryptoUtility:
    Herramienta criptográfica estática de bajo nivel.

    Methods::
        sha256(data) -> str:
            Aplica SHA-256 simple sobre una cadena.
        double_sha256(data) -> str:
            Aplica Doble SHA-256 (Hash(Hash(data))), estándar de Bitcoin.
'''

import hashlib

class CryptoUtility:

    @staticmethod
    def sha256(data: str) -> str:
        encoded_data = data.encode('utf-8')
        return hashlib.sha256(encoded_data).hexdigest()

    @staticmethod
    def double_sha256(data: str) -> str:
        encoded_data = data.encode('utf-8')
        first_hash_bytes = hashlib.sha256(encoded_data).digest()
        second_hash_hex = hashlib.sha256(first_hash_bytes).hexdigest()
        return second_hash_hex