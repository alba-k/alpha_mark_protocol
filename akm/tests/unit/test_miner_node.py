# akm/tests/unit/test_miner_node.py
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from akm.core.nodes.miner_node import MinerNode
from akm.core.models.block import Block
from akm.core.config.config_manager import ConfigManager
from typing import cast, List

class TestMinerNode(unittest.TestCase):

    def setUp(self):
        # 1. Resetear Singleton
        setattr(ConfigManager, "_instance", None)

        # 2. PARCHES DE CONFIGURACIÓN (Vital para evitar errores de Génesis/Factory)
        # Parcheamos donde se usa (GenesisBlockFactory) para evitar el error de super()
        self.config_patcher = patch('akm.core.factories.genesis_block_factory.ConfigManager')
        self.MockConfig = self.config_patcher.start()
        self.MockConfig.return_value.initial_subsidy = 50
        self.MockConfig.return_value.initial_difficulty_bits = "1d00ffff"

        self.genesis_config_patcher = patch('akm.core.factories.genesis_block_factory.GenesisConfig')
        self.MockGenesisConfig = self.genesis_config_patcher.start()
        
        # Configurar valores seguros para evitar ValueError en TxInput
        mock_gen = self.MockGenesisConfig.return_value
        mock_gen.coinbase_input_prev_tx = "0" * 64
        mock_gen.coinbase_input_index = 0
        mock_gen.coinbase_message = "TEST"
        mock_gen.miner_address = "ADDR"
        mock_gen.timestamp = 123
        mock_gen.tx_fee = 0
        mock_gen.index = 0
        mock_gen.previous_hash = "0" * 64
        mock_gen.nonce = 0
        mock_gen.empty_hash_placeholder = ""

        # 3. Mockear Dependencias
        self.mock_p2p = MagicMock()
        self.mock_gossip = MagicMock()
        self.mock_blockchain = MagicMock()
        self.mock_utxo = MagicMock()
        self.mock_mempool = MagicMock()
        self.mock_consensus = MagicMock()
        self.mock_reorg = MagicMock()
        self.mock_mining_manager = MagicMock() # ¡El nuevo integrante!

        # 4. Configurar Blockchain para que no esté vacía (evitar creación de Génesis real)
        dummy_block = MagicMock(spec=Block)
        self.mock_blockchain.chain = cast(List[Block], [dummy_block])
        self.mock_blockchain.__len__.return_value = 1
        self.mock_blockchain.last_block = dummy_block

        # 5. Instanciar MinerNode
        self.node = MinerNode(
            p2p_service=self.mock_p2p,
            gossip_manager=self.mock_gossip,
            blockchain=self.mock_blockchain,
            utxo_set=self.mock_utxo,
            mempool=self.mock_mempool,
            consensus=self.mock_consensus,
            reorg_manager=self.mock_reorg,
            mining_manager=self.mock_mining_manager
        )

        # Configurar dirección de minero para el test
        self.node._miner_address = "MINER_WALLET_123" # type: ignore

    def tearDown(self):
        self.config_patcher.stop()
        self.genesis_config_patcher.stop()
        setattr(ConfigManager, "_instance", None)

    def test_mine_one_block_success_and_propagate(self):
        print("\n>> Ejecutando: test_mine_one_block_success_and_propagate...")
        
        # 1. El MiningManager devuelve un bloque nuevo
        new_block = MagicMock(spec=Block)
        new_block.hash = "NEW_BLOCK_HASH"
        new_block.to_dict.return_value = {"hash": "NEW_BLOCK_HASH", "data": "..."}
        
        self.mock_mining_manager.mine_block.return_value = new_block
        
        # 2. El Consenso acepta el bloque (Es válido)
        self.mock_consensus.add_block.return_value = True
        
        # 3. Ejecutar Minería (Un solo intento)
        result = self.node.mine_one_block()
        
        # 4. Verificaciones
        assert result is True
        
        # A. Se llamó al minero
        self.mock_mining_manager.mine_block.assert_called_once_with("MINER_WALLET_123")
        
        # B. Se intentó guardar en la cadena local
        self.mock_consensus.add_block.assert_called_once_with(new_block)
        
        # C. CRÍTICO: Se propagó a la red (Gossip)
        self.mock_gossip.propagate_block.assert_called_once()
        print("[SUCCESS] Bloque minado, validado y propagado al mundo.")

    def test_mine_one_block_consensus_rejection(self):
        print(">> Ejecutando: test_mine_one_block_consensus_rejection...")
        
        # 1. El MiningManager crea un bloque
        new_block = MagicMock(spec=Block)
        self.mock_mining_manager.mine_block.return_value = new_block
        
        # 2. PERO el Consenso lo rechaza (ej: llegó otro bloque antes / stale)
        self.mock_consensus.add_block.return_value = False
        
        # 3. Ejecutar
        result = self.node.mine_one_block()
        
        # 4. Verificaciones
        assert result is False
        
        # NO se debe propagar un bloque rechazado
        self.mock_gossip.propagate_block.assert_not_called()
        print("[SUCCESS] Bloque rechazado no se propagó.")

    def test_mining_fails_without_address(self):
        print(">> Ejecutando: test_mining_fails_without_address...")
        
        # Desconfiguramos la dirección
        self.node._miner_address = None # type: ignore
        
        result = self.node.mine_one_block()
        
        assert result is False
        self.mock_mining_manager.mine_block.assert_not_called()
        print("[SUCCESS] Minería detenida por falta de Wallet Address.")

if __name__ == "__main__":
    unittest.main()