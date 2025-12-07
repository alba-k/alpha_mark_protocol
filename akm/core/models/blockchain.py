# akm/core/models/blockchain.py
from typing import List, Optional
from akm.core.models.block import Block
from akm.core.interfaces.i_repository import IBlockchainRepository

class Blockchain:
    """
    Modelo de Dominio que representa la Cadena de Bloques.
    Ahora actúa como un Proxy/Fachada hacia la capa de persistencia.
    Ya no guarda datos en RAM, todo va al disco.
    """

    def __init__(self, repository: IBlockchainRepository):
        # Inyección de Dependencia: La Blockchain necesita un lugar donde vivir (DB)
        self._repository = repository

    def add_block(self, block: Block) -> None:
        """Persiste un nuevo bloque en la base de datos."""
        self._repository.save_block(block)

    def replace_chain(self, new_chain: List[Block]) -> None:
        """
        Manejo de Reorg (Complejo).
        En una implementación real con DB, esto implica borrar bloques huerfanos 
        y escribir los nuevos. Por ahora, asumimos que el repositorio maneja la lógica
        o que simplemente añadimos los nuevos si la altura es mayor.
        """
        # Nota: En sistemas productivos con DB, 'replace_chain' no suele sobrescribir todo,
        # sino hacer un 'rollback' hasta el punto de fork y agregar los nuevos.
        # Para mantenerlo simple ahora, guardamos los nuevos bloques.
        for block in new_chain:
            self._repository.save_block(block)

    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        """Busca un bloque por su hash en la DB."""
        return self._repository.get_block_by_hash(block_hash)

    def get_block_by_index(self, index: int) -> Optional[Block]:
        """
        Busca un bloque por altura.
        Nota: Los repositorios SQL suelen optimizar esto.
        """
        # Como IRepository tiene get_blocks_range, pedimos solo 1 bloque en ese índice
        blocks = self._repository.get_blocks_range(start_index=index, limit=1)
        if blocks:
            return blocks[0]
        return None

    @property
    def last_block(self) -> Optional[Block]:
        """Obtiene el Tip de la cadena desde el disco."""
        return self._repository.get_last_block()

    @property
    def chain(self) -> List[Block]:
        """
        ADVERTENCIA: Cargar toda la cadena en RAM puede ser pesado.
        Usar con precaución o para propósitos de test/debug.
        """
        # Traemos todo desde el bloque 0 hasta el final
        total = len(self)
        if total == 0:
            return []
        return self._repository.get_blocks_range(0, total)
    
    def __len__(self) -> int:
        """Retorna la altura actual de la cadena."""
        return self._repository.count()