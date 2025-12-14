# akm/infra/identity/bip39_service.py

import logging
import binascii
import hashlib
from mnemonic import Mnemonic 

logger = logging.getLogger(__name__)

class BIP39Service:
    def __init__(self, language: str = 'english') -> None:
        try:
            self._mnemo: Mnemonic = Mnemonic(language)

            logger.info(f"Servicio BIP39 listo (Idioma: {language}).")
        except Exception:
            logger.exception("Error al inicializar el generador mnemónico")

    def generate_mnemonic(self, strength: int = 256) -> str:
        try:
            if strength not in [128, 160, 192, 224, 256]:
                raise ValueError(f"Fuerza {strength} no soportada por BIP39.")
            
            logger.info(f"Generando mnemónico de {strength} bits...")
            return self._mnemo.generate(strength=strength)

        except Exception:
            logger.exception("Fallo técnico generando frase semilla")
            raise

    def derive_master_private_key(self, mnemonic: str, passphrase: str = "") -> str:
        try:
            logger.info("Derivando clave privada desde mnemónico...")

            if not self._mnemo.check(mnemonic):
                logger.info("Derivación abortada: Mnemónico inválido.")
                raise ValueError("La frase semilla es inválida.")

            
            seed_bytes: bytes = self._mnemo.to_seed(mnemonic, passphrase)
            
            pk_bytes: bytes = hashlib.sha256(seed_bytes).digest()
            
            logger.info("Clave privada maestra derivada exitosamente.")
            
            return binascii.hexlify(pk_bytes).decode('utf-8')

        except Exception as e:
            if not isinstance(e, ValueError):
                logger.exception("Bug en el proceso de derivación criptográfica")
            raise