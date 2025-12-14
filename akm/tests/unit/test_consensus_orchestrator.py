# akm/tests/unit/test_consensus_orchestrator.py
'''
Test Suite para ConsensusOrchestrator:
    Verifica la lógica de decisión para aceptar o rechazar bloques.
    Prueba los caminos de éxito (Extensión) y fallo (Validación, Fork).
'''

import sys
import os
import unittest
from unittest.mock import MagicMock
# IMPORTANTE: cast para el dummy block y Any para flexibilidad
from typing import cast, Optional

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from akm.core.managers.consensus_orchestrator import ConsensusOrchestrator
from akm.core.models.block import Block

class TestConsensusOrchestrator(unittest.TestCase):

    def setUp(self):
        # Mocks de todas las dependencias
        self.mock_blockchain = MagicMock()
        self.mock_utxo_set = MagicMock()
        self.mock_mempool = MagicMock()
        self.mock_reorg_manager = MagicMock()
        self.mock_validator = MagicMock() # BlockRulesValidator
        
        self.orchestrator = ConsensusOrchestrator(
            self.mock_blockchain,
            self.mock_utxo_set,
            self.mock_mempool,
            self.mock_reorg_manager,
            self.mock_validator
        )

    # CORRECCIÓN: Tipado explícito para evitar errores de linter
    def create_dummy_block(self, block_hash: str, prev_hash: str, index: int) -> Block:
        block = MagicMock(spec=Block)
        block.hash = block_hash
        block.previous_hash = prev_hash
        block.index = index
        return cast(Block, block)

    def test_add_block_extension_success(self):
        print("\n>> Ejecutando: test_add_block_extension_success...")
        
        # 1. Configurar Estado Actual (Tip en altura 100)
        tip_block = self.create_dummy_block("hash_100", "hash_99", 100)
        self.mock_blockchain.last_block = tip_block
        
        # 2. Configurar Nuevo Bloque Válido (Altura 101, apunta a 100)
        new_block = self.create_dummy_block("hash_101", "hash_100", 101)
        
        # 3. Configurar Validador (Dice que SI es válido)
        self.mock_validator.validate.return_value = True
        
        # Ejecutar
        result = self.orchestrator.add_block(new_block)
        
        # Verificaciones
        assert result is True
        
        # Debe llamar al ReorgManager para actualizar estado (apply)
        self.mock_reorg_manager.apply_block_to_state.assert_called_with(new_block)
        
        # Debe añadir a la blockchain
        self.mock_blockchain.add_block.assert_called_with(new_block)
        
        print("[SUCCESS] Extensión de cadena válida aceptada.")

    def test_add_block_invalid_rules(self):
        print(">> Ejecutando: test_add_block_invalid_rules...")
        
        new_block = self.create_dummy_block("hash_bad", "hash_prev", 101)
        
        # El validador dice que NO (por PoW, estructura, etc.)
        self.mock_validator.validate.return_value = False
        
        result = self.orchestrator.add_block(new_block)
        
        assert result is False
        self.mock_blockchain.add_block.assert_not_called()
        print("[SUCCESS] Bloque inválido rechazado correctamente.")

    def test_add_block_fork_detected(self):
        print(">> Ejecutando: test_add_block_fork_detected...")
        
        # Estado Actual: Tip en 100 (hash_100)
        tip_block = self.create_dummy_block("hash_100", "hash_99", 100)
        self.mock_blockchain.last_block = tip_block
        
        # Nuevo Bloque (Fork): Altura 101, pero apunta a otro padre ("hash_fork_root")
        fork_block = self.create_dummy_block("hash_fork_101", "hash_fork_root", 101)
        
        # Simulamos que la blockchain CONOCE al padre del fork ("hash_fork_root").
        fork_parent = self.create_dummy_block("hash_fork_root", "hash_prev", 100)
        
        # CORRECCIÓN: Agregar tipo al parámetro 'h' para eliminar el error "unknown type"
        def get_block_side_effect(h: str) -> Optional[Block]:
            if h == "hash_fork_root":
                return fork_parent
            return None
            
        self.mock_blockchain.get_block_by_hash.side_effect = get_block_side_effect
        
        self.mock_validator.validate.return_value = True
        
        result = self.orchestrator.add_block(fork_block)
        
        # Debe retornar False (no se puede extender directamente, requiere reorg)
        assert result is False
        
        # No debe modificar el estado local (eso requiere reorg completo)
        self.mock_blockchain.add_block.assert_not_called()
        self.mock_reorg_manager.apply_block_to_state.assert_not_called()
        
        print("[SUCCESS] Fork detectado y manejado (rechazo de extensión directa).")

if __name__ == "__main__":
    try:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestConsensusOrchestrator)
        unittest.TextTestRunner(verbosity=0).run(suite)
        print("\nTODOS LOS TESTS DE CONSENSO PASARON")
    except Exception as e:
        print(f"\nERROR: {e}")