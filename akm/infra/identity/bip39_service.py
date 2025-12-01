# akm/infra/identity/bip39_service.py
'''
class BIP39Service:
    Servicio de infraestructura para la gestión de frases mnemotécnicas y derivación de claves.

    Methods::
        generate_mnemonic(strength) -> str:
            Genera una nueva frase semilla (12/24 palabras).
        derive_master_private_key(mnemonic, passphrase) -> str:
            Deriva la clave privada maestra en formato Hex desde la semilla.
'''

import logging
import binascii
import hashlib
from typing import Any
from mnemonic import Mnemonic

class BIP39Service:

    def __init__(self, language: str = 'english'):
        # Usamos Any o ignoramos tipos si el linter se queja de la librería externa
        self._mnemo: Any = Mnemonic(language)

    def generate_mnemonic(self, strength: int = 256) -> str:
        # 256 bits = 24 palabras
        return self._mnemo.generate(strength=strength)

    def derive_master_private_key(self, mnemonic: str, passphrase: str = "") -> str:
        if not self._mnemo.check(mnemonic):
            logging.error('BIP39Service: Mnemónico inválido detectado.')
            raise ValueError('La frase semilla es inválida.')

        # Generar Seed binaria (BIP-39)
        seed_bytes: bytes = self._mnemo.to_seed(mnemonic, passphrase)
        
        # Derivación simple para obtener una clave privada ECDSA válida (32 bytes)
        pk_bytes: bytes = hashlib.sha256(seed_bytes).digest()
        
        return binascii.hexlify(pk_bytes).decode('utf-8')