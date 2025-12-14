# akm/infra/persistence/wallet_repository.py

import json
import os
import logging
from typing import Dict, Any
# Importamos la configuración de rutas
from akm.core.config.paths import Paths 

logger = logging.getLogger(__name__)

class WalletRepository:
    """
    Gestiona el almacenamiento de claves en la carpeta 'data/wallets'.
    """
    
    def __init__(self):
        self.wallet_dir = Paths.WALLETS_DIR
        logger.info(f"📂 WalletRepository activo. Directorio: {self.wallet_dir}")

    def save_wallet(self, alias: str, wallet_data: Dict[str, Any], password: str) -> str:
        filename = f"{alias}.json"
        filepath = os.path.join(self.wallet_dir, filename)
        
        logger.info(f"💾 Guardando billetera '{alias}'...")

        protected_data: Dict[str, Any] = {
            "version": 1,
            "alias": alias,
            "crypto": { "cipher": "aes-128-ctr", "ciphertext": "TODO_ENCRYPT_THIS" },
            "payload": wallet_data 
        }

        try:
            with open(filepath, 'w') as f:
                json.dump(protected_data, f, indent=4)
            
            logger.info(f"✅ Billetera guardada exitosamente en: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"❌ Error al escribir el archivo de billetera '{alias}': {e}")
            raise

    def load_wallet(self, alias: str) -> Dict[str, Any]:
        filename = f"{alias}.json"
        filepath = os.path.join(self.wallet_dir, filename)
        
        logger.info(f"🔍 Intentando cargar billetera: {alias}")

        if not os.path.exists(filepath):
            error_msg = f"No se encontró la billetera '{alias}' en {self.wallet_dir}"
            logger.error(f"❌ {error_msg}")
            raise FileNotFoundError(error_msg)
            
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            logger.info(f"🔓 Billetera '{alias}' cargada correctamente.")
            return data["payload"]
        except json.JSONDecodeError:
            logger.error(f"❌ El archivo de la billetera '{alias}' está corrupto o no es un JSON válido.")
            raise
        except Exception:
            logger.exception(f"❌ Error inesperado cargando la billetera '{alias}'")
            raise