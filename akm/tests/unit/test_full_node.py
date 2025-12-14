# akm/tests/unit/test_full_node.py
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from typing import Any

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Imports
from akm.core.nodes.full_node import FullNode
from akm.core.models.block import Block
from akm.core.config.config_manager import ConfigManager

class TestFullNode(unittest.TestCase):

    def setUp(self):
        # 1. Resetear Singleton Config
        setattr(ConfigManager, "_instance", None)

        # 2. PARCHE DE CONFIGURACIÓN (Donde se usa: factories)
        self.config_patcher = patch('akm.core.factories.genesis_block_factory.ConfigManager')
        self.MockConfig = self.config_patcher.start()
        
        # Configurar valores de retorno para ConfigManager simulado
        self.MockConfig.return_value.initial_subsidy = 50
        self.MockConfig.return_value.initial_difficulty_bits = "1d00ffff"

        # 3. PARCHE DE GENESIS CONFIG (Donde se usa: factories)
        self.genesis_config_patcher = patch('akm.core.factories.genesis_block_factory.GenesisConfig')
        self.MockGenesisConfig = self.genesis_config_patcher.start()

        # --- CORRECCIÓN CRÍTICA: Configurar valores del Mock GenesisConfig ---
        # Esto evita el ValueError en TxInput si se llega a ejecutar create_genesis_block
        mock_gen_conf = self.MockGenesisConfig.return_value
        mock_gen_conf.coinbase_input_prev_tx = "0" * 64  # String válido, no Mock
        mock_gen_conf.coinbase_input_index = 0xFFFFFFFF
        mock_gen_conf.coinbase_message = "TEST_GENESIS"
        mock_gen_conf.miner_address = "TEST_MINER_ADDR"
        mock_gen_conf.timestamp = 1234567890
        mock_gen_conf.tx_fee = 0
        mock_gen_conf.index = 0
        mock_gen_conf.previous_hash = "0" * 64
        mock_gen_conf.nonce = 0
        mock_gen_conf.empty_hash_placeholder = ""

        # 4. Mockear dependencias del Nodo
        self.mock_p2p = MagicMock()
        self.mock_gossip = MagicMock()
        
        self.mock_blockchain = MagicMock()
        self.mock_utxo = MagicMock()
        self.mock_mempool = MagicMock()
        self.mock_consensus = MagicMock()
        self.mock_reorg = MagicMock()
        
        # 5. Configurar estado inicial de Blockchain Mock
        dummy_block = MagicMock(spec=Block)
        self.mock_blockchain.chain = [dummy_block] 
        self.mock_blockchain.last_block = dummy_block
        
        # --- CORRECCIÓN CRÍTICA 2: Configurar len() ---
        # Hacemos que len(blockchain) devuelva 1. 
        # Así FullNode sabe que NO está vacío y NO intenta crear el Génesis.
        self.mock_blockchain.__len__.return_value = 1
        
        # 6. Instanciar el Nodo bajo prueba
        self.node = FullNode(
            p2p_service=self.mock_p2p,
            gossip_manager=self.mock_gossip,
            blockchain=self.mock_blockchain,
            utxo_set=self.mock_utxo,
            mempool=self.mock_mempool,
            consensus=self.mock_consensus,
            reorg_manager=self.mock_reorg
        )

    def tearDown(self):
        self.config_patcher.stop()
        self.genesis_config_patcher.stop()
        setattr(ConfigManager, "_instance", None)

    def test_initialization_hydrates_state(self):
        print("\n>> Ejecutando: test_initialization_hydrates_state...")
        
        # Al tener len > 0, debe llamar a hidratación (apply_block_to_state)
        self.mock_reorg.apply_block_to_state.assert_called()
        
        print("[SUCCESS] Estado hidratado correctamente.")

    def test_process_valid_transaction_from_network(self):
        print(">> Ejecutando: test_process_valid_transaction_from_network...")
        
        tx_payload: dict[str, Any] = {
            "tx_hash": "tx_123",
            "timestamp": 1234567890,
            "inputs": [],
            "outputs": [],
            "fee": 10
        }
        
        # Mockeamos el Mapper dentro de full_node para aislar la prueba
        with patch('akm.core.nodes.full_node.NodeMapper') as MockMapper:
            mock_tx_obj = MagicMock()
            mock_tx_obj.tx_hash = "tx_123"
            MockMapper.reconstruct_transaction.return_value = mock_tx_obj
            
            self.mock_mempool.add_transaction.return_value = True
            
            # Ejecutar método protegido (simulando recepción de red)
            self.node._process_payload("TX", tx_payload, "peer_1") # type: ignore
            
            # Verificaciones
            self.mock_mempool.add_transaction.assert_called_once_with(mock_tx_obj)
            self.mock_gossip.propagate_transaction.assert_called_with(tx_payload, origin_peer="peer_1")
        
        print("[SUCCESS] TX procesada y retransmitida.")

    def test_process_valid_block_from_network(self):
        print(">> Ejecutando: test_process_valid_block_from_network...")
        
        block_payload: dict[str, Any] = {
            "index": 5,
            "hash": "block_hash",
            "transactions": []
        }
        
        with patch('akm.core.nodes.full_node.NodeMapper') as MockMapper:
            mock_block_obj = MagicMock()
            mock_block_obj.index = 5
            MockMapper.reconstruct_block.return_value = mock_block_obj
            
            self.mock_consensus.add_block.return_value = True
            
            self.node._process_payload("BLOCK", block_payload, "peer_3") # type: ignore
            
            self.mock_consensus.add_block.assert_called_once_with(mock_block_obj)
            self.mock_gossip.propagate_block.assert_called_with(block_payload, origin_peer="peer_3")
        
        print("[SUCCESS] Bloque aceptado y propagado.")

if __name__ == "__main__":
    unittest.main()