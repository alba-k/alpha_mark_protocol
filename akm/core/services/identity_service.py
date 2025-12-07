# akm/core/services/identity_service.py
import datetime
from typing import Dict

from akm.infra.identity.bip39_service import BIP39Service
from akm.infra.identity.address_factory import AddressFactory
from akm.infra.crypto.software_signer import SoftwareSigner

class IdentityService:
    """
    Servicio de Dominio para la gestión de identidades.
    Centraliza la creación de claves, semillas y direcciones.
    """
    
    def create_new_identity(self) -> Dict[str, str]:
        # 1. Generar Mnemónico y Clave Privada
        service_bip39 = BIP39Service()
        mnemonic = service_bip39.generate_mnemonic()
        private_key = service_bip39.derive_master_private_key(mnemonic)
        
        # 2. Derivar Clave Pública y Dirección
        signer = SoftwareSigner(private_key)
        public_key = signer.get_public_key()
        address = AddressFactory.create_from_public_key(public_key)

        return {
            "created_at": datetime.datetime.now().isoformat(),
            "mnemonic": mnemonic,
            "private_key": private_key,
            "public_key": public_key,
            "address": address
        }