# akm/core/factories/node_factory.py
import logging
from typing import Dict, Any, cast

# Configuración e Infraestructura
from akm.core.config.config_manager import ConfigManager
from akm.infra.persistence.repository_factory import RepositoryFactory
from akm.infra.network.p2p_service import P2PService

# Gestores y Servicios del Dominio
from akm.core.managers.gossip_manager import GossipManager
from akm.core.managers.utxo_set import UTXOSet
from akm.core.services.mempool import Mempool
from akm.core.managers.chain_reorg_manager import ChainReorgManager
from akm.core.validators.block_rules_validator import BlockRulesValidator
from akm.core.consensus.difficulty_adjuster import DifficultyAdjuster
from akm.core.managers.consensus_orchestrator import ConsensusOrchestrator
from akm.core.managers.mining_manager import MiningManager

# Modelos
from akm.core.models.blockchain import Blockchain

# Nodos
from akm.core.nodes.full_node import FullNode
from akm.core.nodes.miner_node import MinerNode
from akm.core.nodes.spv_node import SPVNode

logging.basicConfig(level=logging.INFO, format='[NodeFactory] %(message)s')

class NodeFactory:
    """
    Factory centralizada para la creación y ensamblaje de nodos.
    Se encarga de la Inyección de Dependencias (DI).
    """

    @staticmethod
    def create_spv_node() -> SPVNode:
        logging.info("📱 Fabricando SPV Node (Mobile)...")
        config_manager = ConfigManager()
        
        # El nodo SPV usa una configuración de red ligera
        p2p_service = P2PService(config_manager)
        
        # SPV usa GossipManager en modo "sin blockchain completa"
        gossip_manager = GossipManager(p2p_service)
        
        return SPVNode(p2p_service, gossip_manager)

    @staticmethod
    def create_full_node() -> FullNode:
        logging.info("🏭 Ensamblando Full Node...")
        
        # Construimos todas las dependencias compartidas
        deps = NodeFactory._build_server_dependencies()
        
        return FullNode(
            p2p_service=cast(P2PService, deps['p2p']),
            gossip_manager=cast(GossipManager, deps['gossip']),
            blockchain=cast(Blockchain, deps['blockchain']),
            utxo_set=cast(UTXOSet, deps['utxo_set']),
            mempool=cast(Mempool, deps['mempool']),
            consensus=cast(ConsensusOrchestrator, deps['consensus']),
            reorg_manager=cast(ChainReorgManager, deps['reorg'])
        )

    @staticmethod
    def create_miner_node() -> MinerNode:
        logging.info("🏭 Ensamblando Miner Node...")
        
        # Reutilizamos las dependencias de servidor
        deps = NodeFactory._build_server_dependencies()
        
        # Creamos el gestor de minería específico para este nodo
        mining_manager = MiningManager(
            blockchain=cast(Blockchain, deps['blockchain']),
            mempool=cast(Mempool, deps['mempool']),
            difficulty_adjuster=cast(DifficultyAdjuster, deps['diff_adjuster'])
        )

        return MinerNode(
            p2p_service=cast(P2PService, deps['p2p']),
            gossip_manager=cast(GossipManager, deps['gossip']),
            blockchain=cast(Blockchain, deps['blockchain']),
            utxo_set=cast(UTXOSet, deps['utxo_set']),
            mempool=cast(Mempool, deps['mempool']),
            consensus=cast(ConsensusOrchestrator, deps['consensus']),
            reorg_manager=cast(ChainReorgManager, deps['reorg']),
            mining_manager=mining_manager
        )

    @staticmethod
    def _build_server_dependencies() -> Dict[str, Any]:
        """
        Construye el grafo de dependencias común para FullNodes y Miners.
        """
        # 1. Configuración y Persistencia
        config_manager = ConfigManager()
        blockchain_repo = RepositoryFactory.get_blockchain_repository()
        utxo_repo = RepositoryFactory.get_utxo_repository()
        
        # 2. Estado Base
        blockchain = Blockchain(blockchain_repo)
        utxo_set = UTXOSet(utxo_repo)
        mempool = Mempool()
        
        # 3. Red y Comunicación
        p2p_service = P2PService(config_manager)
        
        # Inyectamos el servicio P2P al Gossip
        gossip_manager = GossipManager(p2p_service)
        # Importante: El Gossip necesita acceso a la Blockchain para responder consultas (GetBlocks, etc.)
        gossip_manager.set_blockchain(blockchain) 
        
        # 4. Consenso y Reglas
        diff_adjuster = DifficultyAdjuster()
        rules_validator = BlockRulesValidator(utxo_set)
        reorg_manager = ChainReorgManager(blockchain, utxo_set, mempool)
        
        consensus = ConsensusOrchestrator(
            blockchain, utxo_set, mempool, reorg_manager, rules_validator
        )

        return {
            'p2p': p2p_service,
            'gossip': gossip_manager,
            'blockchain': blockchain,
            'utxo_set': utxo_set,
            'mempool': mempool,
            'consensus': consensus,
            'reorg': reorg_manager,
            'diff_adjuster': diff_adjuster
        }