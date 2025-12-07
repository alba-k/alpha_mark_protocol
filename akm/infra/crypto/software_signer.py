# akm/infra/crypto/software_signer.py
'''
class SoftwareSigner:
    Implementación concreta de ISigner utilizando la librería 'ecdsa'.
    Adaptado para el stack actual con supresión de errores de linter.

    Methods::
        sign(tx_hash) -> str:
            Firma el hash usando la clave privada interna y retorna firma DER en Hex.
        get_public_key() -> str:
            Retorna la clave pública exportada en Hex (formato comprimido).
'''

import logging
import binascii
from typing import Any

# Importamos la librería legacy ecdsa silenciando errores de tipado
from ecdsa import SigningKey, SECP256k1, util # type: ignore

# Importación del contrato
from akm.core.interfaces.i_signer import ISigner

class SoftwareSigner(ISigner):

    def __init__(self, private_key_hex: str):
        self._sk: Any = None 
        try:
            # Convertimos el string hex a bytes para la librería
            priv_key_bytes = binascii.unhexlify(private_key_hex)
            
            # Cargamos la clave privada (Curva secp256k1)
            self._sk = SigningKey.from_string(priv_key_bytes, curve=SECP256k1) # type: ignore
        except Exception as e:
            logging.critical(f'SoftwareSigner: Error al importar clave privada: {e}')
            raise ValueError('Formato de clave privada inválido.')

    def sign(self, tx_hash: str) -> str:
        try:
            hash_bytes = binascii.unhexlify(tx_hash)
            
            # Firmamos el digest (hash) 
            signature_bytes = self._sk.sign_digest(hash_bytes, sigencode=util.sigencode_der ) # type: ignore
        
            return binascii.hexlify(signature_bytes).decode('utf-8')

        except Exception as e:
            logging.error(f'SoftwareSigner: Fallo al firmar transacción: {e}')
            raise ValueError('Error criptográfico al firmar con ecdsa.')

    def get_public_key(self) -> str:
        try:
            vk = self._sk.verifying_key
            # Exportamos en formato comprimido (33 bytes)
            pub_key_bytes = vk.to_string(encoding="compressed") # type: ignore
            
            return binascii.hexlify(pub_key_bytes).decode('utf-8')
        except Exception as e:
            logging.error(f'SoftwareSigner: Error exportando clave pública: {e}')
            raise ValueError('Error al obtener identidad pública.')