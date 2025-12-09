# akm/core/models/blockchain.py
from typing import List, Optional, Iterator, Dict, Any
from akm.core.models.block import Block
from akm.core.models.block_header import BlockHeader
from akm.core.interfaces.i_repository import IBlockchainRepository
from akm.core.interfaces.i_chain import IChain

class Blockchain(IChain):
    """
    Modelo de Dominio que representa la Cadena de Bloques.
    Proxy eficiente hacia la persistencia.
    """

    def __init__(self, repository: IBlockchainRepository):
        self._repository = repository

    # --- Implementación IChain (Interfaz Nueva para Polimorfismo) ---
    
    @property
    def height(self) -> int:
        """Altura de la cadena (Alias para count)."""
        return self._repository.count()

    @property
    def tip(self) -> Optional[BlockHeader]:
        """
        Último encabezado conocido.
        Devuelve un Block, pero como Block hereda de BlockHeader, es válido.
        """
        return self._repository.get_last_block()

    def add_header(self, header: BlockHeader) -> bool:
        """
        FullNode no acepta headers sueltos sin transacciones.
        """
        return False 

    # --- Métodos Propios de FullNode (Soporte y Lógica) ---

    @property
    def last_block(self) -> Optional[Block]:
        """
        Alias necesario para que ConsensusOrchestrator funcione.
        """
        return self._repository.get_last_block()

    def add_block(self, block: Block) -> None:
        self._repository.save_block(block)

    def replace_chain(self, new_chain: List[Block]) -> None:
        self._repository.save_blocks_atomic(new_chain)

    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        return self._repository.get_block_by_hash(block_hash)

    def get_block_by_index(self, index: int) -> Optional[Block]:
        blocks = self._repository.get_blocks_range(start_index=index, limit=1)
        if blocks:
            return blocks[0]
        return None
    
    # 🔥 MÉTODO AÑADIDO: Proxy directo para IBD (Necesario para FullNode)
    def get_blocks_range(self, start_index: int, limit: int) -> List[Block]:
        """
        Recupera un lote de bloques de forma consecutiva.
        Necesario para la lógica de sincronización (IBD).
        """
        return self._repository.get_blocks_range(start_index, limit)

    def get_history_iterator(self, start_index: int = 0, batch_size: int = 100) -> Iterator[Block]:
        """Iterador eficiente para no cargar toda la DB en RAM."""
        current = start_index
        while True:
            # [VERIFICADO] El método repository.get_blocks_range existe en la capa de persistencia.
            batch = self._repository.get_blocks_range(current, batch_size)
            if not batch:
                break
            yield from batch
            current += len(batch)

    # [SPV] Soporte para Light Clients
    def get_headers(self, start_hash: str, limit: int = 2000) -> List[Dict[str, Any]]:
        return self._repository.get_headers_range(start_hash, limit)

    def __len__(self) -> int:
        """Soporte para len(blockchain)."""
        return self._repository.count()