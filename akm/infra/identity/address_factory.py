# akm/infra/identity/address_factory.py
import hashlib
import binascii
import logging
import base58 

logger = logging.getLogger(__name__)

class AddressFactory:

    @staticmethod
    def create_from_public_key(public_key_hex: str) -> str:
        try:
            pub_key_bytes: bytes = binascii.unhexlify(public_key_hex)

            # 1. HASH160 (SHA256 seguido de RIPEMD160)
            sha256_bpk = hashlib.sha256(pub_key_bytes).digest()
            ripemd160_bpk = hashlib.new('ripemd160')
            ripemd160_bpk.update(sha256_bpk)
            ripemd160_digest = ripemd160_bpk.digest()

            # 2. Versionado (Prefijo \x00 para Mainnet)
            versioned_payload: bytes = b'\x00' + ripemd160_digest

            # 3. Checksum (Doble SHA256, tomamos los primeros 4 bytes)
            first_sha = hashlib.sha256(versioned_payload).digest()
            checksum_full = hashlib.sha256(first_sha).digest()
            checksum = checksum_full[:4]

            # 4. Codificación Base58Check
            binary_address = versioned_payload + checksum
            address: str = base58.b58encode(binary_address).decode('utf-8')

            logger.info(f"Dirección generada: {address[:8]}...")
            
            return address

        except Exception:
            logger.exception("Error crítico derivando dirección desde clave pública")
            raise ValueError("Clave pública corrupta o inválida.")