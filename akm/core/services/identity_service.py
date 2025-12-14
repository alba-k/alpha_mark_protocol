# akm/core/services/identity_service.py

import datetime
import logging
from typing import Dict

from akm.infra.identity.bip39_service import BIP39Service
from akm.infra.identity.address_factory import AddressFactory
from akm.infra.crypto.software_signer import SoftwareSigner

logger = logging.getLogger(__name__)

class IdentityService:
    """
    Servicio de Dominio que orquesta la generación de una identidad criptográfica completa:
    Mnemónico -> Clave Privada -> Clave Pública -> Dirección P2PKH.
    """
    
    def create_new_identity(self) -> Dict[str, str]:
        """
        Genera y retorna la identidad con fines de serialización/almacenamiento.
        """
        try:
            logger.info("Generando nueva identidad criptográfica...")

            # 1. Generar Mnemónico y Clave Privada (Derivación BIP-39 simple)
            service_bip39 = BIP39Service()
            mnemonic = service_bip39.generate_mnemonic()
            private_key = service_bip39.derive_master_private_key(mnemonic)
            
            # 2. Generar Clave Pública (a través del Firmante)
            signer = SoftwareSigner(private_key)
            public_key = signer.get_public_key()
            
            # 3. Generar Dirección (Base58Check)
            address = AddressFactory.create_from_public_key(public_key)

            logger.info(f"Identidad creada exitosamente. Dirección: {address}")

            return {
                "created_at": datetime.datetime.now().isoformat(),
                "mnemonic": mnemonic,
                "private_key": private_key,
                "public_key": public_key,
                "address": address
            }

        except Exception:
            logger.exception("Error fatal durante la generación de identidad")
            # Devolvemos un diccionario vacío en caso de fallo crítico
            return {}