import os
import json
import base64
import logging
from typing import Dict, Any, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Servicios de identidad
from akm.core.services.identity_service import IdentityService

logger = logging.getLogger(__name__)

class Keystore:
    
    def __init__(self, filename: str = "wallet.dat", filepath: Optional[str] = None):
        """
        Inicializa el Keystore.
        Puede recibir un 'filepath' explícito (usado por la API) 
        o construirlo basado en 'filename' y 'AKM_DATA_DIR'.
        """
        try:
            self._identity_service = IdentityService()

            # LÓGICA CORREGIDA:
            if filepath:
                # Caso 1: La API nos pasa la ruta completa
                self.filepath = filepath
                self.data_dir = os.path.dirname(filepath)
            else:
                # Caso 2: Comportamiento por defecto (Directorios de entorno)
                self.data_dir = os.environ.get("AKM_DATA_DIR", ".")
                self.filepath = os.path.join(self.data_dir, filename)
            
            # Asegurar que el directorio existe (en ambos casos)
            if self.data_dir and not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir, exist_ok=True)

            logger.info(f"🔐 Keystore activo en: {self.filepath}")

        except Exception:
            logger.exception("Error al inicializar Keystore")

    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000, 
            )
            return base64.urlsafe_b64encode(kdf.derive(password.encode()))
        except Exception:
            logger.exception("Fallo técnico en la derivación de llave")
            raise

    def create_new_wallet(self, password: str) -> Dict[str, str]:
        try:
            logger.info("Creando nueva identidad...")

            identity = self._identity_service.create_new_identity()
            
            salt = os.urandom(16) 
            key = self._derive_key_from_password(password, salt)
            cipher_suite = Fernet(key)
            
            secret_bytes = identity['private_key'].encode('utf-8')
            encrypted_secret = cipher_suite.encrypt(secret_bytes)
            
            wallet_data: Dict[str, Any] = {
                "version": 1,
                "address": identity['address'],
                "public_key": identity['public_key'],
                "kdf_salt": base64.b64encode(salt).decode('utf-8'),
                "ciphertext": base64.b64encode(encrypted_secret).decode('utf-8')
            }
            
            # Guardamos en la ruta definida
            with open(self.filepath, "w") as f:
                json.dump(wallet_data, f, indent=4)
                
            logger.info(f"✅ Billetera guardada: {self.filepath}")
            return identity

        except Exception:
            logger.exception("Error fatal creando wallet")
            raise

    def load_wallet(self, password: str) -> Dict[str, str]:
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"No existe wallet en {self.filepath}")
            
        try:
            with open(self.filepath, "r") as f:
                data = json.load(f)
            
            salt = base64.b64decode(data['kdf_salt'])
            ciphertext = base64.b64decode(data['ciphertext'])
            
            key = self._derive_key_from_password(password, salt)
            cipher_suite = Fernet(key)
            
            decrypted_bytes = cipher_suite.decrypt(ciphertext)
            private_key = decrypted_bytes.decode('utf-8')
            
            logger.info(f"🔓 Wallet desbloqueada: {data['address'][:8]}...")
            
            return {
                "address": data['address'],
                "public_key": data['public_key'],
                "private_key": private_key
            }
            
        except Exception as e:
            if "InvalidToken" in str(e) or isinstance(e, ValueError):
                raise ValueError("Contraseña incorrecta.")
            logger.exception("Error cargando wallet")
            raise

    def wallet_exists(self) -> bool:
        return os.path.exists(self.filepath)