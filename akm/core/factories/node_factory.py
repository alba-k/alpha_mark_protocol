# akm/core/factories/node_factory.py
import logging
from typing import Dict, Any, cast

# Infraestructura
from akm.infra.persistence.repository_factory import RepositoryFactory
from akm.infra.network.p2p_service import P2PService

# [NUEVO] Importamos ConfigManager para inyectarlo al servicio P2P
from akm.core.config.config_manager import ConfigManager

# Core Managers
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

logging.basicConfig(level=logging.INFO, format='[NodeFactory] %(message)s')

class NodeFactory:
    """
    [Factory Pattern]
    Responsabilidad Única: Ensamblar el grafo de dependencias complejo.
    """

    @staticmethod
    def create_full_node() -> FullNode:
        logging.info("🏭 Ensamblando Full Node...")
        deps = NodeFactory._build_common_dependencies()
        
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
        deps = NodeFactory._build_common_dependencies()

        blockchain = cast(Blockchain, deps['blockchain'])
        mempool = cast(Mempool, deps['mempool'])
        diff_adjuster = cast(DifficultyAdjuster, deps['diff_adjuster'])

        mining_manager = MiningManager(
            blockchain=blockchain,
            mempool=mempool,
            difficulty_adjuster=diff_adjuster
        )

        return MinerNode(
            p2p_service=cast(P2PService, deps['p2p']),
            gossip_manager=cast(GossipManager, deps['gossip']),
            blockchain=blockchain,
            utxo_set=cast(UTXOSet, deps['utxo_set']),
            mempool=mempool,
            consensus=cast(ConsensusOrchestrator, deps['consensus']),
            reorg_manager=cast(ChainReorgManager, deps['reorg']),
            mining_manager=mining_manager
        )

    @staticmethod
    def _build_common_dependencies() -> Dict[str, Any]:
        """Construye todas las piezas compartidas."""
        
        # [CORRECCIÓN 1] Instanciamos la Configuración Central
        config_manager = ConfigManager()

        repository = RepositoryFactory.get_repository()
        blockchain = Blockchain(repository)
        utxo_set = UTXOSet()
        mempool = Mempool()
        
        # [CORRECCIÓN 2] Inyectamos la config al P2PService
        # Antes: p2p_service = P2PService() -> ERROR
        p2p_service = P2PService(config_manager)
        
        # Ahora GossipManager recibe un servicio ya configurado y válido
        gossip_manager = GossipManager(p2p_service)
        
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