# akm/infra/identity/address_factory.py
import hashlib
import binascii
import logging
import base58 

class AddressFactory:

    @staticmethod
    def create_from_public_key(public_key_hex: str) -> str:
        try:
            pub_key_bytes: bytes = binascii.unhexlify(public_key_hex)

            # 1. SHA-256
            sha256_bpk = hashlib.sha256(pub_key_bytes).digest()

            # 2. RIPEMD-160
            ripemd160_bpk = hashlib.new('ripemd160')
            ripemd160_bpk.update(sha256_bpk)
            ripemd160_digest = ripemd160_bpk.digest()

            # 3. Versionado (Mainnet) y Checksum
            versioned_payload: bytes = b'\x00' + ripemd160_digest
            checksum_full = hashlib.sha256(hashlib.sha256(versioned_payload).digest()).digest()
            checksum = checksum_full[:4]

            # 4. Codificación Base58
            binary_address = versioned_payload + checksum
            address: str = base58.b58encode(binary_address).decode('utf-8')

            return address

        except Exception as e:
            logging.error(f'AddressFactory: Error generando dirección: {e}')
            raise ValueError('No se pudo generar la dirección desde la clave pública.')