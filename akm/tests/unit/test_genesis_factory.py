# akm/tests/unit/test_genesis_factory.py
'''
Test Suite para GenesisBlockFactory:
    Verifica que el Bloque Génesis se construya fielmente a los parámetros
    de configuración histórica y reglas del protocolo.

    Functions::
        test_genesis_block_structure(): Verifica altura, hash previo y timestamp.
        test_genesis_coinbase_content(): Verifica el mensaje, reward y dirección.
        test_genesis_integrity(): Verifica que los hashes no estén vacíos.
'''

import sys
import os
import unittest

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from akm.core.factories.genesis_block_factory import GenesisBlockFactory
from akm.core.config.config_manager import ConfigManager
from akm.core.config.genesis_config import GenesisConfig

class TestGenesisFactory(unittest.TestCase):

    def setUp(self):
        # Instanciamos las configuraciones para comparar contra la verdad
        self.sys_config = ConfigManager()
        self.gen_config = GenesisConfig()
        
        # Creamos el bloque génesis real usando la fábrica
        self.genesis_block = GenesisBlockFactory.create_genesis_block()

    def test_genesis_block_structure(self):
        print("\n>> Ejecutando: test_genesis_block_structure...")
        
        # 1. Verificar Header Básico
        self.assertEqual(self.genesis_block.index, 0, "El índice debe ser 0")
        self.assertEqual(self.genesis_block.previous_hash, "0" * 64, "El hash previo debe ser nulo")
        self.assertEqual(self.genesis_block.nonce, self.gen_config.nonce, "El nonce debe coincidir con la config")
        self.assertEqual(self.genesis_block.timestamp, self.gen_config.timestamp, "El timestamp debe ser el histórico")
        
        # 2. Verificar Dificultad Inicial
        self.assertEqual(self.genesis_block.bits, self.sys_config.initial_difficulty_bits)
        
        print("[SUCCESS] Estructura del bloque Génesis correcta.")

    def test_genesis_coinbase_content(self):
        print(">> Ejecutando: test_genesis_coinbase_content...")
        
        # Debe haber exactamente 1 transacción
        self.assertEqual(len(self.genesis_block.transactions), 1)
        coinbase = self.genesis_block.transactions[0]
        
        # 1. Verificar Input Especial (Coinbase)
        self.assertEqual(len(coinbase.inputs), 1)
        inp = coinbase.inputs[0]
        self.assertEqual(inp.previous_tx_hash, "0" * 64)
        self.assertEqual(inp.output_index, 0xFFFFFFFF)
        
        # VERIFICACIÓN CLAVE: El mensaje histórico
        self.assertEqual(inp.script_sig, self.gen_config.coinbase_message)
        
        # 2. Verificar Output (Pago)
        self.assertEqual(len(coinbase.outputs), 1)
        out = coinbase.outputs[0]
        self.assertEqual(out.value_alba, self.sys_config.initial_subsidy)
        self.assertEqual(out.script_pubkey, self.gen_config.miner_address)
        
        print(f"[SUCCESS] Contenido Coinbase verificado: '{inp.script_sig[:20]}...'")

    def test_genesis_integrity(self):
        print(">> Ejecutando: test_genesis_integrity...")
        
        # Verificar que los hashes fueron calculados y no están vacíos
        self.assertNotEqual(self.genesis_block.hash, "", "El hash del bloque no debe estar vacío")
        self.assertNotEqual(self.genesis_block.transactions[0].tx_hash, "", "El hash de la TX no debe estar vacío")
        self.assertNotEqual(self.genesis_block.merkle_root, "", "La Merkle Root no debe estar vacía")
        
        # Opcional: Verificar que el Merkle Root coincida con el hash de la única tx
        self.assertEqual(self.genesis_block.merkle_root, self.genesis_block.transactions[0].tx_hash)
        
        print(f"[SUCCESS] Integridad criptográfica verificada. Hash Génesis: {self.genesis_block.hash[:16]}...")

if __name__ == "__main__":
    print("==========================================")
    print("   TESTING GENESIS BLOCK FACTORY          ")
    print("==========================================\n")
    try:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestGenesisFactory)
        unittest.TextTestRunner(verbosity=0).run(suite)
        print("\nEL NACIMIENTO DE LA BLOCKCHAIN ES CORRECTO")
    except Exception as e:
        print(f"\nERROR: {e}")