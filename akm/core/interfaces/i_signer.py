# akm/core/interfaces/i_signer.py
'''
class ISigner:
    Contrato abstracto que define la capacidad de firmar digitalmente y exponer identidad pública.

    Methods::
        sign(tx_hash) -> str:
            Recibe un hash hexadecimal y retorna una firma ECDSA hexadecimal.
        get_public_key() -> str:
            Retorna la Clave Pública en formato hexadecimal comprimido.
'''

from abc import ABC, abstractmethod

class ISigner(ABC):

    @abstractmethod
    def sign(self, tx_hash: str) -> str:
        pass

    @abstractmethod
    def get_public_key(self) -> str:
        pass