# akm/core/managers/wallet_manager.py
'''
class WalletManager:
    Orquestador de alto nivel para la gestión de identidad y autorización de operaciones.

    Methods:
        sign_transaction_hash(tx_hash) -> str:
            Recibe el hash de una transacción y devuelve la firma criptográfica.
        get_public_key() -> str:
            Obtiene la identidad pública (Public Key) asociada al gestor.
'''

import logging

# Importaciones de la Arquitectura
from akm.core.interfaces.i_signer import ISigner


class WalletManager:

    def __init__(self, signer: ISigner):
        self._signer: ISigner = signer

    def sign_transaction_hash(self, tx_hash: str) -> str:
        if not tx_hash:
            logging.error('WalletManager: Se intentó firmar un hash vacío.')
            raise ValueError('El hash de la transacción es inválido o vacío.')

        signature: str = self._signer.sign(tx_hash)
        
        logging.info(f'WalletManager: Hash {tx_hash[:8]}... firmado exitosamente.')
        return signature

    def get_public_key(self) -> str:
        return self._signer.get_public_key()