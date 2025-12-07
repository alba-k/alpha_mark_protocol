# akm/core/nodes/full_node.py
import logging
from typing import Dict, Any

# Herencia y Utilería
from akm.core.nodes.base_node import BaseNode
from akm.core.utils.node_mapper import NodeMapper

# Infraestructura e Interfaces
from akm.infra.network.p2p_service import P2PService
from akm.core.managers.gossip_manager import GossipManager

# Core Managers y Modelos
from akm.core.models.blockchain import Blockchain
from akm.core.models.transaction import Transaction 
from akm.core.managers.utxo_set import UTXOSet
from akm.core.services.mempool import Mempool
from akm.core.managers.consensus_orchestrator import ConsensusOrchestrator
from akm.core.managers.chain_reorg_manager import ChainReorgManager
from akm.core.factories.genesis_block_factory import GenesisBlockFactory

logging.basicConfig(level=logging.INFO, format='[FullNode] %(message)s')

class FullNode(BaseNode):
    """
    [LSP] Nodo Completo (Validating Node).
    Mantiene una copia completa de la Blockchain y valida reglas de consenso.
    """

    def __init__(
        self, 
        p2p_service: P2PService, 
        gossip_manager: GossipManager,
        blockchain: Blockchain,
        utxo_set: UTXOSet,
        mempool: Mempool,
        consensus: ConsensusOrchestrator,
        reorg_manager: ChainReorgManager
    ):
        # 1. Inicializar Red (Padre)
        super().__init__(p2p_service, gossip_manager)
        
        # 2. Inicializar Estado (Hijo)
        self.blockchain = blockchain
        self.utxo_set = utxo_set
        self.mempool = mempool
        self.consensus = consensus
        self.reorg_manager = reorg_manager
        
        # 3. Restaurar Estado al nacer
        self._hydrate_and_check_genesis()

    def _hydrate_and_check_genesis(self):
        """Recupera el estado desde el disco (Cold Start)."""
        if self.blockchain.chain:
            logging.info(f"📚 Hidratando estado desde {len(self.blockchain)} bloques...")
            self.utxo_set.clear()
            for block in self.blockchain.chain:
                self.reorg_manager.apply_block_to_state(block)
        
        if len(self.blockchain) == 0:
            logging.warning("⚠️ Blockchain vacía. Creando Génesis...")
            genesis = GenesisBlockFactory.create_genesis_block()
            if self.consensus.add_block(genesis):
                logging.info(f"🌍 GÉNESIS CREADO: {genesis.hash[:16]}")
        else:
            tip = self.blockchain.last_block
            if tip:
                logging.info(f"✅ Nodo Sincronizado. Altura: {tip.index}")

    def _process_payload(self, msg_type: str, payload: Dict[str, Any], peer_id: str):
        """
        Reacciona a mensajes validados que llegan de la red.
        """
        if msg_type == "BLOCK":
            logging.info(f"📨 [Consenso] Bloque recibido de {peer_id[:8]}...")
            try:
                # Usamos el Mapper para convertir JSON -> Objeto
                block = NodeMapper.reconstruct_block(payload)
                
                # Validar y Guardar
                if self.consensus.add_block(block):
                    logging.info(f"✅ Bloque #{block.index} ACEPTADO.")
                    # [Clean Code] Propagar payload puro. GossipManager se encarga del 'envelope'.
                    self.gossip.propagate_block(payload, origin_peer=peer_id)
                else:
                    logging.info("🗑️ Bloque rechazado.")
            except Exception as e:
                logging.error(f"Error procesando bloque: {e}")

        elif msg_type == "TX":
            logging.info(f"📨 [Consenso] TX recibida de {peer_id[:8]}...")
            try:
                tx = NodeMapper.reconstruct_transaction(payload)
                
                if self.mempool.add_transaction(tx):
                    logging.info(f"✅ TX {tx.tx_hash[:8]} en Mempool.")
                    # [Clean Code] Propagar payload puro.
                    self.gossip.propagate_transaction(payload, origin_peer=peer_id)
            except Exception as e:
                logging.error(f"Error procesando TX: {e}")
    
    def submit_transaction(self, tx: Transaction) -> bool:
        """
        Recibe una TX local (Wallet), la guarda y la propaga.
        """
        if self.mempool.add_transaction(tx):
            logging.info(f"🚀 Transacción aceptada localmente: {tx.tx_hash[:8]}")
            
            # [CORRECCIÓN IMPORTANTE]
            # Ya NO creamos el diccionario {"type": "TX"}. 
            # Pasamos los datos crudos y dejamos que GossipManager haga su trabajo.
            self.gossip.propagate_transaction(tx.to_dict()) 
            return True
        
        logging.warning("TX rechazada por Mempool local.")
        return False
        
    def get_balance(self, address: str) -> int:
        """Rol de Wallet: Consultar saldo."""
        return self.utxo_set.get_balance_for_address(address)