# akm/core/factories/node_factory.py

import logging
from typing import Dict, Any, cast, Union

# Configuración
from akm.core.config.consensus_config import ConsensusConfig
from akm.core.config.network_config import NetworkConfig
from akm.core.config.mining_config import MiningConfig

# Infraestructura
from akm.infra.persistence.repository_factory import RepositoryFactory
from akm.infra.network.p2p_service import P2PService

# Gestores
from akm.core.managers.gossip_manager import GossipManager
from akm.core.managers.utxo_set import UTXOSet
from akm.core.services.mempool import Mempool
from akm.core.managers.chain_reorg_manager import ChainReorgManager
from akm.core.validators.block_rules_validator import BlockRulesValidator
from akm.core.managers.consensus_orchestrator import ConsensusOrchestrator
from akm.core.managers.mining_manager import MiningManager

# Lógica Pura
from akm.core.consensus.difficulty_adjuster import DifficultyAdjuster
from akm.core.consensus.subsidy_calculator import SubsidyCalculator

# Nodos
from akm.core.models.blockchain import Blockchain
from akm.core.nodes.full_node import FullNode
from akm.core.nodes.miner_node import MinerNode
from akm.core.nodes.spv_node import SPVNode

logger = logging.getLogger(__name__)

class NodeFactory:
    """
    Fábrica Central de Nodos.
    Encapsula la complejidad de instanciar todo el grafo de dependencias
    para cada tipo de nodo (SPV, Full, Miner).
    """

    @staticmethod
    def create_node(role: str) -> Union[FullNode, MinerNode, SPVNode]:
        """
        Factory Method Principal: Despacha la creación según el rol.
        Usado por main.py (Headless) y server.py (SPV API).
        """
        logger.info(f"🏭 NodeFactory: Solicitud de creación para rol '{role}'")
        
        if role == "SPV_NODE":
            return NodeFactory.create_spv_node()
        elif role == "MINER":
            return NodeFactory.create_miner_node()
        elif role == "FULL_NODE":
            return NodeFactory.create_full_node()
        else:
            logger.critical(f"Rol de nodo desconocido: {role}")
            raise ValueError(f"Rol de nodo no soportado: {role}")

    @staticmethod
    def create_spv_node() -> SPVNode:
        try:
            logger.info("Fabricando SPV Node (Cliente Ligero)...")
            
            network_config = NetworkConfig()
            p2p_service = P2PService(network_config) 
            gossip_manager = GossipManager(p2p_service)
            
            node = SPVNode(p2p_service, gossip_manager)
            logger.info("SPV Node ensamblado.")
            return node
            
        except Exception:
            logger.exception("Fallo al ensamblar SPV Node")
            raise

    @staticmethod
    def create_full_node() -> FullNode:
        try:
            logger.info("Fabricando Full Node (Servidor de Validación)...")
            deps = NodeFactory._build_server_dependencies()
            
            node = FullNode(
                p2p_service=cast(P2PService, deps['p2p']),
                gossip_manager=cast(GossipManager, deps['gossip']),
                blockchain=cast(Blockchain, deps['blockchain']),
                utxo_set=cast(UTXOSet, deps['utxo_set']),
                mempool=cast(Mempool, deps['mempool']),
                consensus=cast(ConsensusOrchestrator, deps['consensus']),
                reorg_manager=cast(ChainReorgManager, deps['reorg'])
            )
            logger.info("Full Node ensamblado.")
            return node
            
        except Exception:
            logger.exception("Fallo al ensamblar Full Node")
            raise

    @staticmethod
    def create_miner_node() -> MinerNode:
        try:
            logger.info("Fabricando Miner Node (Trabajador PoW)...")
            deps = NodeFactory._build_server_dependencies()
            
            # Instanciar configuración de minería
            mining_config = MiningConfig()

            mining_manager = MiningManager(
                blockchain=cast(Blockchain, deps['blockchain']),
                mempool=cast(Mempool, deps['mempool']),
                difficulty_adjuster=cast(DifficultyAdjuster, deps['diff_adjuster']),
                subsidy_calculator=cast(SubsidyCalculator, deps['subsidy_calculator'])
            )

            node = MinerNode(
                p2p_service=cast(P2PService, deps['p2p']),
                gossip_manager=cast(GossipManager, deps['gossip']),
                blockchain=cast(Blockchain, deps['blockchain']),
                utxo_set=cast(UTXOSet, deps['utxo_set']),
                mempool=cast(Mempool, deps['mempool']),
                consensus=cast(ConsensusOrchestrator, deps['consensus']),
                reorg_manager=cast(ChainReorgManager, deps['reorg']),
                mining_manager=mining_manager,
                mining_config=mining_config 
            )
            logger.info("Miner Node ensamblado.")
            return node

        except Exception:
            logger.exception("Fallo al ensamblar Miner Node")
            raise

    @staticmethod
    def _build_server_dependencies() -> Dict[str, Any]:
        """
        Construye el grafo de dependencias común para nodos de servidor (Full y Miner).
        """
        try:
            # 1. Configuración
            consensus_config = ConsensusConfig()
            network_config = NetworkConfig()
            
            # 2. Persistencia (Repositorios)
            blockchain_repo = RepositoryFactory.get_blockchain_repository()
            utxo_repo = RepositoryFactory.get_utxo_repository()
            
            # 3. Estado Base
            blockchain = Blockchain(blockchain_repo)
            utxo_set = UTXOSet(utxo_repo)
            mempool = Mempool()
            
            # 4. Servicios de Red
            p2p_service = P2PService(network_config) 
            gossip_manager = GossipManager(p2p_service)
            gossip_manager.set_blockchain(blockchain) 
            
            # 5. Lógica de Consenso y Economía
            subsidy_calculator = SubsidyCalculator(consensus_config)
            diff_adjuster = DifficultyAdjuster()
            
            # 6. Validadores y Orquestadores
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
                'diff_adjuster': diff_adjuster,
                'subsidy_calculator': subsidy_calculator
            }
        except Exception:
            logger.exception("Error crítico en el grafo de dependencias")
            raise