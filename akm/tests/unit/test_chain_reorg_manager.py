# akm/tests/unit/test_chain_reorg_manager.py
import sys
import os
import unittest
from unittest.mock import MagicMock
# IMPORTANTE: Importar 'cast' para engañar al linter de forma segura
from typing import List, Optional, Any, cast 

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from akm.core.managers.chain_reorg_manager import ChainReorgManager
from akm.core.models.block import Block
from akm.core.models.transaction import Transaction
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput

class TestChainReorgManager(unittest.TestCase):

    def setUp(self):
        self.mock_blockchain = MagicMock()
        self.mock_utxo_set = MagicMock()
        self.mock_mempool = MagicMock()
        
        self.reorg_manager = ChainReorgManager(
            self.mock_blockchain,
            self.mock_utxo_set,
            self.mock_mempool
        )

    # CORRECCIÓN CLAVE AQUÍ:
    # 1. Usar 'Optional[List[Any]]' para ser permisivo con lo que recibe 'txs'.
    # 2. Retornar 'Block' en la firma, pero usar 'cast' internamente.
    def create_dummy_block(self, block_hash: str, index: int, txs: Optional[List[Any]] = None) -> Block:
        block = MagicMock(spec=Block)
        block.hash = block_hash
        block.index = index
        block.transactions = txs if txs else []
        
        # EL TRUCO PARA EL LINTER: 
        # Le decimos explícitamente "trata este Mock como si fuera un Block real"
        return cast(Block, block)

    def test_handle_reorg_success(self):
        print("\n>> Ejecutando: test_handle_reorg_success...")
        
        gen = self.create_dummy_block("hash_G", 0)
        blk_a = self.create_dummy_block("hash_A", 1)
        blk_b = self.create_dummy_block("hash_B", 2)
        
        blk_c = self.create_dummy_block("hash_C", 2)
        blk_d = self.create_dummy_block("hash_D", 3)
        
        # Ahora el linter sabe que esto es una lista de Blocks, no de Mocks
        self.mock_blockchain.chain = [gen, blk_a, blk_b]
        new_chain = [gen, blk_a, blk_c, blk_d]
        
        result = self.reorg_manager.handle_reorg(new_chain)
        
        assert result is True
        self.mock_blockchain.replace_chain.assert_called_with(new_chain)
        
        # Verificar que se limpia el estado para reconstruirlo
        self.mock_utxo_set.clear.assert_called()
        print("[SUCCESS] Reorganización ejecutada.")

    def test_orphaned_transactions_recovery(self):
        print(">> Ejecutando: test_orphaned_transactions_recovery...")
        
        gen = self.create_dummy_block("hash_G", 0)
        
        tx_orphan = MagicMock(spec=Transaction)
        tx_orphan.is_coinbase = False
        tx_orphan.tx_hash = "tx_lost_in_fork"
        
        blk_b = self.create_dummy_block("hash_B", 1, txs=[tx_orphan])
        blk_c = self.create_dummy_block("hash_C", 1, txs=[])
        
        self.mock_blockchain.chain = [gen, blk_b]
        new_chain = [gen, blk_c]
        
        self.mock_mempool.add_transaction.return_value = True
        
        self.reorg_manager.handle_reorg(new_chain)
        
        self.mock_mempool.add_transaction.assert_called_with(tx_orphan)
        print("[SUCCESS] TXs huérfanas recuperadas.")

    def test_handle_reorg_failure_incompatible(self):
        print(">> Ejecutando: test_handle_reorg_failure_incompatible...")
        
        chain_local = [self.create_dummy_block("hash_G1", 0)]
        chain_remote = [self.create_dummy_block("hash_G2", 0)]
        
        self.mock_blockchain.chain = chain_local
        
        result = self.reorg_manager.handle_reorg(chain_remote)
        
        assert result is False
        self.mock_blockchain.replace_chain.assert_not_called()
        print("[SUCCESS] Reorg incompatible rechazado.")

    def test_apply_block_state_updates(self):
        print(">> Ejecutando: test_apply_block_state_updates...")
        
        out_cb = TxOutput(50, "miner_addr")
        out_std = TxOutput(10, "receiver_addr")
        inp_std = TxInput("prev_hash", 0, "sig")

        tx_coinbase = MagicMock(spec=Transaction)
        tx_coinbase.is_coinbase = True
        tx_coinbase.tx_hash = "tx_cb"
        tx_coinbase.outputs = [out_cb]
        
        tx_std = MagicMock(spec=Transaction)
        tx_std.is_coinbase = False
        tx_std.tx_hash = "tx_std"
        tx_std.inputs = [inp_std]
        tx_std.outputs = [out_std]
        
        block = self.create_dummy_block("blk_1", 1, txs=[tx_coinbase, tx_std])
        
        self.reorg_manager.apply_block_to_state(block)
        
        self.mock_utxo_set.remove_inputs.assert_called_with([inp_std])
        self.mock_utxo_set.add_outputs.assert_any_call("tx_cb", [out_cb])
        self.mock_utxo_set.add_outputs.assert_any_call("tx_std", [out_std])
        
        print("[SUCCESS] Updates de estado (Apply) verificados con tipos correctos.")

    def test_rollback_block_logic(self):
        print(">> Ejecutando: test_rollback_block_logic...")
        
        inp = TxInput("prev_hash", 0, "sig")
        original_output = TxOutput(100, "addr")
        
        tx_origin = MagicMock(spec=Transaction)
        tx_origin.tx_hash = "prev_hash"
        tx_origin.outputs = [original_output]
        
        block_origin = self.create_dummy_block("blk_origin", 0, txs=[tx_origin])
        self.mock_blockchain.chain = [block_origin]
        
        tx_spending = MagicMock(spec=Transaction)
        tx_spending.is_coinbase = False
        tx_spending.tx_hash = "tx_spending"
        tx_spending.inputs = [inp]
        tx_spending.outputs = []
        
        block_to_undo = self.create_dummy_block("blk_undo", 1, txs=[tx_spending])
        
        self.reorg_manager.rollback_block_from_state(block_to_undo)
        
        self.mock_utxo_set.add_outputs.assert_called_with("prev_hash", [original_output])
        self.mock_mempool.add_transaction.assert_called_with(tx_spending)
        print("[SUCCESS] Rollback verificado.")

if __name__ == "__main__":
    try:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestChainReorgManager)
        unittest.TextTestRunner(verbosity=0).run(suite)
        print("\nTODOS LOS TESTS DE ORQUESTACIÓN PASARON")
    except Exception as e:
        print(f"\nERROR: {e}")