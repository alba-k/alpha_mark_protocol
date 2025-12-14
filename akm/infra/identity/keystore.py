# akm/infra/identity/keystore.py
import os
import json
import base64
import logging
from typing import Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Servicios de identidad
from akm.core.services.identity_service import IdentityService

# ✅ Logger sintético para bitácora de seguridad física
logger = logging.getLogger(__name__)

class Keystore:
    
    def __init__(self, filepath: str = "wallet.dat"):
        try:
            self.filepath = filepath
            self._identity_service = IdentityService()
            logger.info(f"Keystore inicializado en: {self.filepath}")
        except Exception:
            logger.exception("Error al inicializar Keystore")

    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000, # Estándar de resistencia actual
            )
            # Retorna b64 url-safe para Fernet
            return base64.urlsafe_b64encode(kdf.derive(password.encode()))
        except Exception:
            logger.exception("Fallo técnico en la derivación de llave")
            raise

    def create_new_wallet(self, password: str) -> Dict[str, str]:
        try:
            logger.info("Iniciando creación de almacén seguro...")

            # 1. Generar identidad nueva
            identity = self._identity_service.create_new_identity()
            
            # 2. Preparar cifrado (Fernet/AES)
            salt = os.urandom(16) 
            key = self._derive_key_from_password(password, salt)
            cipher_suite = Fernet(key)
            
            # 3. Encriptar Clave Privada
            secret_bytes = identity['private_key'].encode('utf-8')
            encrypted_secret = cipher_suite.encrypt(secret_bytes)
            
            # 4. Estructura de persistencia JSON
            wallet_data: Dict[str, Any] = {
                "version": 1,
                "address": identity['address'],
                "public_key": identity['public_key'],
                "kdf_salt": base64.b64encode(salt).decode('utf-8'),
                "ciphertext": base64.b64encode(encrypted_secret).decode('utf-8')
            }
            
            # 5. Escritura en disco
            with open(self.filepath, "w") as f:
                json.dump(wallet_data, f, indent=4)
                
            logger.info(f"Billetera creada y encriptada exitosamente en {self.filepath}")
            return identity

        except Exception:
            logger.exception("Error fatal creando el archivo de billetera")
            raise

    def load_wallet(self, password: str) -> Dict[str, str]:
        if not os.path.exists(self.filepath):
            logger.info(f"Carga fallida: No existe el archivo {self.filepath}")
            raise FileNotFoundError("Archivo de billetera no encontrado.")
            
        try:
            logger.info("Intentando desbloquear almacén seguro...")
            
            with open(self.filepath, "r") as f:
                data = json.load(f)
            
            # A. Recuperar parámetros
            salt = base64.b64decode(data['kdf_salt'])
            ciphertext = base64.b64decode(data['ciphertext'])
            
            # B. Re-derivar llave
            key = self._derive_key_from_password(password, salt)
            cipher_suite = Fernet(key)
            
            # C. Desencriptar
            decrypted_bytes = cipher_suite.decrypt(ciphertext)
            private_key = decrypted_bytes.decode('utf-8')
            
            logger.info(f"Billetera desbloqueada para dirección: {data['address'][:8]}...")
            
            return {
                "address": data['address'],
                "public_key": data['public_key'],
                "private_key": private_key
            }
            
        except Exception as e:
            if "InvalidToken" in str(e) or isinstance(e, ValueError):
                logger.info("Intento de acceso fallido: Contraseña incorrecta.")
                raise ValueError("Contraseña incorrecta.")
            
            logger.exception("Error técnico al cargar la billetera")
            raise

    def wallet_exists(self) -> bool:
        return os.path.exists(self.filepath)