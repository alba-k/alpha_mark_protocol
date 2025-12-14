# akm/core/interfaces/i_signer.py

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class ISigner(ABC):
    """
    [Abstracción de Seguridad]
    Contrato que define la capacidad de firmar digitalmente.
    
    Permite desacoplar la lógica de construcción de transacciones 
    del almacenamiento sensible de las claves privadas.
    """

    @abstractmethod
    def sign(self, message_hash: str) -> str:
        """
        Firma criptográficamente un hash.
        
        En la implementación:
        - Registro en log: 'Firma digital generada.'
        - Registro en terminal: Solo si el motor ECDSA falla (Exception).
        
        Args:
            message_hash: El hash hexadecimal de los datos a firmar.
            
        Returns:
            str: La firma ECDSA en formato hexadecimal (DER).
        """
        pass

    @abstractmethod
    def get_public_key(self) -> str:
        """
        Expone la identidad pública del firmante.
        
        Returns:
            str: Clave Pública en formato hexadecimal.
        """
        pass