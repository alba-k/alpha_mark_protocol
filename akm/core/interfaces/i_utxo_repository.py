# akm/core/interfaces/i_utxo_repository.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from akm.core.models.tx_output import TxOutput

class IUTXORepository(ABC):
    """
    Contrato para la persistencia del Estado (Monedas no gastadas).
    Permite consultas rápidas de saldo sin recorrer toda la cadena.
    """

    @abstractmethod
    def add_utxo(self, tx_hash: str, index: int, output: TxOutput) -> None:
        """Guarda una nueva UTXO."""
        pass

    @abstractmethod
    def remove_utxo(self, tx_hash: str, index: int) -> None:
        """Elimina una UTXO gastada."""
        pass

    @abstractmethod
    def get_utxo(self, tx_hash: str, index: int) -> Optional[TxOutput]:
        """Recupera una UTXO específica."""
        pass

    @abstractmethod
    def get_utxos_by_address(self, address: str) -> List[Dict[str, Any]]:
        """Recupera todas las UTXOs de una dirección (para Wallets)."""
        pass

    @abstractmethod
    def get_total_supply(self) -> int:
        """Calcula el circulante total."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Borra todo el estado (DANGER: Usar solo en Reorgs completos)."""
        pass