# akm/core/nodes/miner_node.py
import logging
import threading
import time
from typing import Optional

# Herencia
from akm.core.nodes.full_node import FullNode

# Dependencias (Importadas para tipado estricto)
from akm.core.managers.mining_manager import MiningManager
from akm.infra.network.p2p_service import P2PService
from akm.core.managers.gossip_manager import GossipManager
from akm.core.models.blockchain import Blockchain
from akm.core.managers.utxo_set import UTXOSet
from akm.core.services.mempool import Mempool
from akm.core.managers.consensus_orchestrator import ConsensusOrchestrator
from akm.core.managers.chain_reorg_manager import ChainReorgManager
from akm.core.config.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO, format='[MinerNode] %(message)s')

class MinerNode(FullNode):
    """
    [LSP] Nodo Minero.
    """

    def __init__(
        self, 
        p2p_service: P2PService, 
        gossip_manager: GossipManager, 
        blockchain: Blockchain, 
        utxo_set: UTXOSet, 
        mempool: Mempool, 
        consensus: ConsensusOrchestrator, 
        reorg_manager: ChainReorgManager,
        mining_manager: MiningManager
    ):
        # Inicializar el Padre (FullNode) explícitamente
        super().__init__(
            p2p_service, gossip_manager, blockchain, utxo_set, mempool, consensus, reorg_manager
        )
        
        self.miner = mining_manager
        
        # Cargar configuración
        config = ConfigManager()
        self._miner_address: Optional[str] = config.mining.default_miner_address
        self._mining_active = False

    # ... (Resto de métodos start_mining_loop, etc. iguales que antes)

    def start_mining_loop(self, miner_address: Optional[str] = None):
        """
        Inicia el proceso de minería.
        Si se pasa una dirección, se usa esa. Si no, usa la de la configuración.
        """
        # Prioridad: Argumento > Configuración
        address_to_use = miner_address if miner_address else self._miner_address
        
        if not address_to_use:
            logging.error("❌ No se puede iniciar minería: Falta dirección de pago.")
            return

        self._miner_address = address_to_use
        self._mining_active = True
        
        mining_thread = threading.Thread(target=self._mining_worker, daemon=True)
        mining_thread.start()
        logging.info(f"⛏️ Minería ACTIVA -> {self._miner_address[:10]}...")

    def stop_mining(self):
        self._mining_active = False
        logging.info("🛑 Minería detenida.")

    def mine_one_block(self) -> bool:
        """Intenta minar un solo bloque."""
        if not self._miner_address:
            logging.error("Falta dirección de minero.")
            return False

        logging.info("🔨 Trabajando en bloque...")
        try:
            new_block = self.miner.mine_block(self._miner_address)
            
            if self.consensus.add_block(new_block):
                logging.info(f"💎 ¡BLOQUE ENCONTRADO! Hash: {new_block.hash[:8]}")
                self.gossip.propagate_block(new_block.to_dict())
                return True
            else:
                logging.warning("Bloque rechazado (Stale).")
                return False
                
        except Exception as e:
            logging.error(f"Error minería: {e}")
            return False

    def _mining_worker(self):
        while self._mining_active:
            if self.mine_one_block():
                continue
            time.sleep(1)