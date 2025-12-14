# akm/infra/crypto/software_signer.py
import logging
import binascii
from typing import Any

from ecdsa import SigningKey, SECP256k1, util # type: ignore

# Importación del contrato
from akm.core.interfaces.i_signer import ISigner

logger = logging.getLogger(__name__)

class SoftwareSigner(ISigner):

    def __init__(self, private_key_hex: str) -> None:
        self._sk: Any = None 
        try:
            priv_key_bytes = binascii.unhexlify(private_key_hex)
            self._sk = SigningKey.from_string(priv_key_bytes, curve=SECP256k1) # type: ignore
            
            logger.info("Firmante de software inicializado.")
        except Exception:
            logger.exception("Fallo al cargar la clave privada en SoftwareSigner")
            raise ValueError("Formato de clave privada inválido.")

    def sign(self, message_hash: str) -> str:
        try:
            # Decodificamos el hash hexadecimal a bytes
            hash_bytes = binascii.unhexlify(message_hash)
            
            # Generamos la firma usando el estándar de Bitcoin (DER)
            signature_bytes: bytes = self._sk.sign_digest(
                hash_bytes, 
                sigencode=util.sigencode_der # type: ignore
            )
        
            logger.info(f"Firma generada para hash {message_hash[:8]}...")
            
            return binascii.hexlify(signature_bytes).decode('utf-8')

        except Exception:
            logger.exception("Error criptográfico durante el proceso de firma")
            raise ValueError("Error al firmar con ecdsa.")

    def get_public_key(self) -> str:
        try:
            vk = self._sk.verifying_key
            pub_key_bytes: bytes = vk.to_string(encoding="compressed") # type: ignore
            
            return binascii.hexlify(pub_key_bytes).decode('utf-8')
        except Exception:
            logger.exception("Error exportando clave pública")
            raise ValueError("No se pudo obtener la identidad pública.")