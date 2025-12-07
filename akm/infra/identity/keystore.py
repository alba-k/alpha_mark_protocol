# akm/infra/identity/keystore.py
'''
Gestor de Almacenamiento Seguro (Keystore).
Responsabilidad: Persistir la identidad del usuario de forma encriptada (AES).
Usa PBKDF2HMAC para derivar una clave fuerte a partir de la contraseña del usuario.
'''

import os
import json
import base64
from typing import Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Importamos nuestro servicio generador de identidades
from akm.core.services.identity_service import IdentityService

class Keystore:
    
    def __init__(self, filepath: str = "wallet.dat"):
        self.filepath = filepath
        self._identity_service = IdentityService()

    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """
        Convierte una contraseña humana en una llave criptográfica de 32 bytes
        usando un 'Salt' aleatorio para evitar ataques de diccionario.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000, # Alto número de iteraciones para seguridad (estándar 2023+)
        )
        # Fernet requiere codificación base64 url-safe
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def create_new_wallet(self, password: str) -> Dict[str, str]:
        """
        1. Genera una nueva identidad (Private/Public Key + Address).
        2. Encripta la Private Key con la contraseña.
        3. Guarda todo en un archivo JSON seguro.
        """
        # A. Generar Identidad Limpia
        identity = self._identity_service.create_new_identity()
        
        # B. Preparar Encriptación
        salt = os.urandom(16) # Generar sal aleatoria
        key = self._derive_key_from_password(password, salt)
        cipher_suite = Fernet(key)
        
        # C. Encriptar el Secreto (Private Key)
        secret_bytes = identity['private_key'].encode('utf-8')
        encrypted_secret = cipher_suite.encrypt(secret_bytes)
        
        # D. Preparar Datos para Guardar (JSON)
        # Guardamos el Salt (público) y el Cifrado (secreto)
        wallet_data: Dict[str, Any] = {
            "version": 1,
            "address": identity['address'],
            "public_key": identity['public_key'],
            "kdf_salt": base64.b64encode(salt).decode('utf-8'),
            "ciphertext": base64.b64encode(encrypted_secret).decode('utf-8')
        }
        
        # E. Escribir en Disco
        with open(self.filepath, "w") as f:
            json.dump(wallet_data, f, indent=4)
            
        print(f"🔐 [Keystore] Billetera creada y encriptada en: {self.filepath}")
        return identity

    def load_wallet(self, password: str) -> Dict[str, str]:
        """
        Lee el archivo, pide contraseña, y si es correcta, devuelve la Private Key desencriptada.
        """
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"No existe el archivo de billetera: {self.filepath}")
            
        with open(self.filepath, "r") as f:
            data = json.load(f)
            
        try:
            # A. Recuperar Salt y Datos Encriptados
            salt = base64.b64decode(data['kdf_salt'])
            ciphertext = base64.b64decode(data['ciphertext'])
            
            # B. Regenerar la llave con la contraseña ingresada
            key = self._derive_key_from_password(password, salt)
            cipher_suite = Fernet(key)
            
            # C. Intentar Desencriptar
            decrypted_bytes = cipher_suite.decrypt(ciphertext)
            private_key = decrypted_bytes.decode('utf-8')
            
            print(f"🔓 [Keystore] Billetera desbloqueada exitosamente: {data['address']}")
            
            return {
                "address": data['address'],
                "public_key": data['public_key'],
                "private_key": private_key
            }
            
        except Exception:
            # Si Fernet falla, es porque la contraseña es incorrecta (o el archivo está corrupto)
            raise ValueError("❌ Contraseña incorrecta. No se pudo desencriptar la billetera.")

    def wallet_exists(self) -> bool:
        return os.path.exists(self.filepath)