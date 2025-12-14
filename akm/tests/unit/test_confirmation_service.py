# akm/tests/unit/test_confirmation_service.py
'''
Test Suite para ConfirmationService:
    Verifica el cálculo correcto de la profundidad (confirmaciones) de un bloque.

    Functions::
        test_confirmations_middle_block(): Bloque en medio de la cadena.
        test_confirmations_tip_block(): Bloque en la punta (1 confirmación).
        test_confirmations_unknown_block(): Bloque no encontrado (0 confirmaciones).
'''

import sys
import os
import unittest
from unittest.mock import MagicMock

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from akm.core.services.confirmation_service import ConfirmationService
from akm.core.models.block import Block
from akm.core.models.blockchain import Blockchain

class TestConfirmationService(unittest.TestCase):

    def setUp(self):
        # Mock de la Blockchain
        self.mock_blockchain = MagicMock(spec=Blockchain)
        self.service = ConfirmationService(self.mock_blockchain)

    def create_dummy_block(self, block_hash: str, index: int) -> MagicMock:
        block = MagicMock(spec=Block)
        block.hash = block_hash
        block.index = index
        return block

    def test_confirmations_middle_block(self):
        print("\n>> Ejecutando: test_confirmations_middle_block...")
        
        # Escenario: Cadena [A] -> [B] -> [C] -> [D]
        # Queremos saber confirmaciones de [B] (Index 1)
        # Tip es [D] (Index 3)
        
        blk_a = self.create_dummy_block("hash_A", 0)
        blk_b = self.create_dummy_block("hash_B", 1) # Objetivo
        blk_c = self.create_dummy_block("hash_C", 2)
        blk_d = self.create_dummy_block("hash_D", 3) # Tip
        
        # Configuramos el Mock de la cadena
        self.mock_blockchain.chain = [blk_a, blk_b, blk_c, blk_d]
        self.mock_blockchain.last_block = blk_d
        
        # Ejecutar
        confirmations = self.service.get_confirmations("hash_B")
        
        # Verificación: (3 - 1) + 1 = 3 confirmaciones (B, C, D)
        self.assertEqual(confirmations, 3)
        print(f"[SUCCESS] Confirmaciones correctas: {confirmations} (Esperado: 3)")

    def test_confirmations_tip_block(self):
        print(">> Ejecutando: test_confirmations_tip_block...")
        
        blk_a = self.create_dummy_block("hash_A", 0)
        
        self.mock_blockchain.chain = [blk_a]
        self.mock_blockchain.last_block = blk_a
        
        # El último bloque siempre tiene 1 confirmación
        confirmations = self.service.get_confirmations("hash_A")
        
        self.assertEqual(confirmations, 1)
        print(f"[SUCCESS] Confirmaciones en el tip: {confirmations}")

    def test_confirmations_unknown_block(self):
        print(">> Ejecutando: test_confirmations_unknown_block...")
        
        blk_a = self.create_dummy_block("hash_A", 0)
        self.mock_blockchain.chain = [blk_a]
        self.mock_blockchain.last_block = blk_a
        
        # Buscamos un hash que no existe
        confirmations = self.service.get_confirmations("hash_FANTASMA")
        
        self.assertEqual(confirmations, 0)
        print(f"[SUCCESS] Bloque desconocido retorna 0 confirmaciones.")

if __name__ == "__main__":
    try:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestConfirmationService)
        unittest.TextTestRunner(verbosity=0).run(suite)
        print("\nTODOS LOS TESTS DE CONFIRMACIÓN PASARON")
    except Exception as e:
        print(f"\nERROR: {e}")