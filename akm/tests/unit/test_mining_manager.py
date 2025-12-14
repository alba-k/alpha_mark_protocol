# akm/tests/unit/test_mining_manager.py
'''
Test Suite para MiningManager:
    Verifica la orquestación de la minería, el cálculo de recompensas (fees + subsidio)
    y la correcta creación del bloque candidato.
'''

import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from akm.core.managers.mining_manager import MiningManager
from akm.core.models.block import Block
from akm.core.models.transaction import Transaction

class TestMiningManager(unittest.TestCase):

    def setUp(self):
        self.mock_blockchain = MagicMock()
        self.mock_mempool = MagicMock()
        self.mock_diff_adjuster = MagicMock()
        
        self.miner = MiningManager(
            self.mock_blockchain,
            self.mock_mempool,
            self.mock_diff_adjuster
        )

    @patch('akm.core.managers.mining_manager.BlockBuilder')
    @patch('akm.core.managers.mining_manager.TransactionFactory')
    def test_mine_block_orchestration(self, MockTxFactory: MagicMock, MockBlockBuilder: MagicMock):
        print("\n>> Ejecutando: test_mine_block_orchestration...")
        
        # 1. Configurar estado de la Blockchain (Tip actual)
        last_block = MagicMock(spec=Block)
        last_block.index = 100
        last_block.hash = "hash_previo_0000"
        
        # CORRECCIÓN: El manager lee esto si no hay ajuste de dificultad
        last_block.bits = "1d00ffff" 
        
        self.mock_blockchain.last_block = last_block
        # Simulamos que si busca por índice, retorna el mismo bloque (para simplificar)
        self.mock_blockchain.get_block_by_index.return_value = last_block

        # 2. Configurar Difficulty Adjuster
        self.mock_diff_adjuster.calculate_new_bits.return_value = "1d00ffff"
        self.mock_diff_adjuster.calculate_block_subsidy.return_value = 50 

        # 3. Configurar Mempool
        tx1 = MagicMock(spec=Transaction)
        tx1.fee = 5
        tx2 = MagicMock(spec=Transaction)
        tx2.fee = 10
        self.mock_mempool.get_transactions_for_block.return_value = [tx1, tx2]

        # 4. Configurar Factories
        coinbase_tx = MagicMock(spec=Transaction)
        coinbase_tx.is_coinbase = True
        MockTxFactory.create_coinbase.return_value = coinbase_tx
        
        final_block = MagicMock(spec=Block)
        final_block.hash = "hash_nuevo_bloque_minado"
        final_block.nonce = 12345
        MockBlockBuilder.build.return_value = final_block

        # --- EJECUCIÓN ---
        miner_addr = "MINER_WALLET_ADDRESS"
        block = self.miner.mine_block(miner_addr)

        # --- VERIFICACIONES ---
        self.assertEqual(block, final_block)

        MockTxFactory.create_coinbase.assert_called_with(
            miner_pubkey_hash=miner_addr,
            block_height=101, 
            total_reward=65
        )

        _, kwargs = MockBlockBuilder.build.call_args
        
        assert kwargs['previous_hash'] == "hash_previo_0000"
        assert kwargs['index'] == 101
        assert kwargs['bits'] == "1d00ffff" # Ahora esto funcionará

        print("[SUCCESS] Orquestación de minería correcta (Reward = 50+15=65).")

if __name__ == "__main__":
    try:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestMiningManager)
        unittest.TextTestRunner(verbosity=0).run(suite)
        print("\nTODOS LOS TESTS DE MINERÍA PASARON")
    except Exception as e:
        print(f"\nERROR: {e}")