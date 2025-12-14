# akm/tests/unit/test_node_factory.py
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from typing import cast

# --- AJUSTE DE RUTA (PRIMERO QUE TODO) ---
# Esto debe ir ANTES de importar cualquier cosa de 'akm'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Imports del Sistema
from akm.core.factories.node_factory import NodeFactory
from akm.core.nodes.full_node import FullNode
from akm.core.nodes.miner_node import MinerNode
from akm.core.config.config_manager import ConfigManager

class TestNodeFactory(unittest.TestCase):

    def setUp(self):
        # Resetear Singleton de Configuración para limpieza
        setattr(ConfigManager, "_instance", None)

    @patch('akm.core.factories.node_factory.RepositoryFactory')
    @patch('akm.core.factories.node_factory.Blockchain')
    @patch('akm.core.factories.node_factory.UTXOSet')
    @patch('akm.core.factories.node_factory.Mempool')
    @patch('akm.core.factories.node_factory.P2PService')
    @patch('akm.core.factories.node_factory.GossipManager')
    @patch('akm.core.factories.node_factory.DifficultyAdjuster')
    @patch('akm.core.factories.node_factory.BlockRulesValidator')
    @patch('akm.core.factories.node_factory.ChainReorgManager')
    @patch('akm.core.factories.node_factory.ConsensusOrchestrator')
    @patch('akm.core.factories.node_factory.MiningManager')
    def test_create_full_node_assembly(
        self, 
        MockMiningManager: MagicMock, 
        MockConsensus: MagicMock, 
        MockReorg: MagicMock, 
        MockValidator: MagicMock, 
        MockDiffAdjuster: MagicMock, 
        MockGossip: MagicMock, 
        MockP2P: MagicMock, 
        MockMempool: MagicMock, 
        MockUTXO: MagicMock, 
        MockBlockchain: MagicMock, 
        MockRepoFactory: MagicMock
    ):
        
        print("\n>> Ejecutando: test_create_full_node_assembly...")
        
        # Ejecutar la fábrica
        node = NodeFactory.create_full_node()
        
        # Verificaciones
        self.assertIsInstance(node, FullNode)
        
        # Verificar que las dependencias se instanciaron
        # Usamos cast para ayudar al linter a saber que es un MagicMock
        cast(MagicMock, MockRepoFactory).get_repository.assert_called_once() # type: ignore
        cast(MagicMock, MockBlockchain).assert_called_once() # type: ignore
        cast(MagicMock, MockUTXO).assert_called_once() # type: ignore
        
        # Gossip recibe p2p
        cast(MagicMock, MockGossip).assert_called_once() # type: ignore
        
        print("[SUCCESS] Full Node ensamblado con éxito.")

    @patch('akm.core.factories.node_factory.RepositoryFactory')
    @patch('akm.core.factories.node_factory.Blockchain')
    @patch('akm.core.factories.node_factory.UTXOSet')
    @patch('akm.core.factories.node_factory.Mempool')
    @patch('akm.core.factories.node_factory.P2PService')
    @patch('akm.core.factories.node_factory.GossipManager')
    @patch('akm.core.factories.node_factory.DifficultyAdjuster')
    @patch('akm.core.factories.node_factory.BlockRulesValidator')
    @patch('akm.core.factories.node_factory.ChainReorgManager')
    @patch('akm.core.factories.node_factory.ConsensusOrchestrator')
    @patch('akm.core.factories.node_factory.MiningManager')
    def test_create_miner_node_assembly(
        self, 
        MockMiningManager: MagicMock, 
        MockConsensus: MagicMock, 
        MockReorg: MagicMock, 
        MockValidator: MagicMock, 
        MockDiffAdjuster: MagicMock, 
        MockGossip: MagicMock, 
        MockP2P: MagicMock, 
        MockMempool: MagicMock, 
        MockUTXO: MagicMock, 
        MockBlockchain: MagicMock, 
        MockRepoFactory: MagicMock
    ):
        
        print(">> Ejecutando: test_create_miner_node_assembly...")
        
        # Ejecutar la fábrica
        node = NodeFactory.create_miner_node()
        
        # Verificaciones
        self.assertIsInstance(node, MinerNode)
        # Un Miner ES UN FullNode por herencia
        self.assertIsInstance(node, FullNode) 
        
        # Verificar que se creó el MiningManager (la diferencia clave)
        cast(MagicMock, MockMiningManager).assert_called_once() # type: ignore
        
        print("[SUCCESS] Miner Node ensamblado con MiningManager.")

if __name__ == "__main__":
    unittest.main()