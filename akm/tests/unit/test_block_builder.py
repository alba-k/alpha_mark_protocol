# akm/tests/unit/test_block_builder.py
'''
Test Suite para BlockBuilder (Minería):
    Simula el proceso de minado (PoW) usando la configuración REAL del proyecto.
    
    CORRECCIÓN:
    - Se elimina el mocking (@patch).
    - Se lee la dificultad (bits) directamente del ConfigManager.
    - Al usar la configuración por defecto ("207fffff"), la minería es real pero instantánea.
'''

import sys
import os
import time
import unittest

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from akm.core.builders.block_builder import BlockBuilder
from akm.core.factories.transaction_factory import TransactionFactory
from akm.core.utils.difficulty_utils import DifficultyUtils
from akm.core.config.config_manager import ConfigManager

class TestBlockBuilder(unittest.TestCase):

    def setUp(self):
        # 1. Reseteamos el Singleton para asegurar que cargamos la configuración limpia
        setattr(ConfigManager, "_instance", None)

    def test_mining_valid_block(self):
        print("\n>> Ejecutando: test_mining_valid_block (Configuración Real)...")
        
        # 2. Instanciamos la Configuración Real del Proyecto
        # Esto cargará los valores por defecto definidos en ConsensusConfig
        # (Por defecto: AKM_INIT_BITS = "207fffff", que es dificultad mínima)
        config = ConfigManager()
        
        # 3. Obtenemos los bits oficiales del sistema
        # No inventamos "1d00ffff", usamos lo que el sistema tiene configurado.
        real_bits = config.consensus.initial_difficulty_bits
        
        print(f"   -> Usando Dificultad del Proyecto: {real_bits}")
        
        # 4. Preparar Datos
        coinbase = TransactionFactory.create_coinbase("MINER_ADDR", 1, 50)
        transactions = [coinbase]
        prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        
        start_time = time.time()
        
        # 5. EJECUTAR MINERÍA REAL
        # El BlockBuilder usará la dificultad que le pasamos.
        # Al ser "207fffff" (Regtest), encontrará el nonce muy rápido.
        block = BlockBuilder.build(transactions, prev_hash, bits=real_bits, index=1)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 6. Verificaciones
        print(f"   -> ¡ÉXITO! Bloque Minado.")
        print(f"   -> Hash: {block.hash}")
        print(f"   -> Nonce: {block.nonce}")
        print(f"   -> Tiempo: {duration:.4f} segundos")
        
        # Validamos matemáticamente contra el target real de la configuración
        target = DifficultyUtils.bits_to_target(real_bits)
        block_hash_int = int(block.hash, 16)
        
        self.assertLessEqual(block_hash_int, target, "El hash debe cumplir con el target de la configuración")
        self.assertGreaterEqual(block.nonce, 0)
        
        print("[SUCCESS] Minería completada usando configuración nativa.")

if __name__ == "__main__":
    unittest.main()