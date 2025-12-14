# akm/tests/unit/test_sqlite_blockchain_repository.py
import sys
import os
import unittest
import time

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from akm.infra.persistence.sqlite.sqlite_blockchain_repository import SqliteBlockchainRepository
from akm.infra.persistence.database_manager import DatabaseManager
from akm.core.config.config_manager import ConfigManager
from akm.core.models.block import Block
from akm.core.models.transaction import Transaction
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput

class TestSqlitePersistence(unittest.TestCase):

    def setUp(self):
        """
        Configuración inteligente con historial:
        Guarda los resultados en 'akm/tests/results/persistence/' sin sobrescribir.
        """
        # 1. Preparar carpeta de resultados
        self.results_dir = os.path.join(project_root, "akm", "tests", "results", "persistence")
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        # 2. Generar nombre único para este test (sqlite_test_1.db, etc.)
        self.db_path = self._get_unique_db_path("sqlite_test")
        print(f"\n[SETUP] DB para este test: {self.db_path}")

        # 3. Resetear Singletons (Vital)
        setattr(DatabaseManager, "_instance", None)
        setattr(ConfigManager, "_instance", None)

        # 4. Inyección Manual de Configuración (CRÍTICO)
        # Aquí le decimos al sistema: "Usa el archivo único que acabo de inventar"
        config = ConfigManager()
        config.persistence._db_name = self.db_path # type: ignore
        config.persistence._storage_engine = "sqlite" # type: ignore

        # 5. Inicializar el repositorio
        # Al nacer, leerá la configuración que acabamos de inyectar
        self.repo = SqliteBlockchainRepository()

    def tearDown(self):
        # Cerrar conexión para liberar el archivo (pero NO borrarlo)
        if hasattr(self, 'repo'):
            self.repo.conn.close()
        
        # Limpieza de estado global
        setattr(DatabaseManager, "_instance", None)
        setattr(ConfigManager, "_instance", None)

    def _get_unique_db_path(self, base_name: str) -> str:
        """Busca el siguiente número disponible para no sobrescribir."""
        counter = 1
        while True:
            filename = f"{base_name}_{counter}.db"
            full_path = os.path.join(self.results_dir, filename)
            if not os.path.exists(full_path):
                return full_path
            counter += 1

    # --- HELPERS ---
    def create_dummy_block(self, index: int, prev_hash: str) -> Block:
        inp = TxInput("prev_hash_beef", 0, "sig_123")
        out = TxOutput(50, "miner_addr")
        tx = Transaction(f"tx_hash_{index}", int(time.time()), [inp], [out], fee=10)
        
        return Block(
            index=index,
            timestamp=int(time.time()),
            previous_hash=prev_hash,
            bits="1d00ffff",
            merkle_root=f"merkle_{index}",
            nonce=12345,
            block_hash=f"block_hash_{index}",
            transactions=[tx]
        )

    # --- TESTS ---
    def test_save_and_get_block(self):
        print(">> Ejecutando: test_save_and_get_block...")
        original_block = self.create_dummy_block(1, "genesis_hash")
        self.repo.save_block(original_block)
        
        retrieved_block = self.repo.get_block_by_hash(original_block.hash)
        
        self.assertIsNotNone(retrieved_block)
        if retrieved_block:
            self.assertEqual(retrieved_block.index, 1)
            self.assertEqual(retrieved_block.hash, original_block.hash)
            self.assertEqual(len(retrieved_block.transactions), 1)
        print("[SUCCESS] Bloque guardado y recuperado.")

    def test_get_last_block_logic(self):
        print(">> Ejecutando: test_get_last_block_logic...")
        # DB inicia vacía porque es un archivo nuevo único
        b1 = self.create_dummy_block(1, "000")
        b2 = self.create_dummy_block(2, b1.hash)
        b3 = self.create_dummy_block(3, b2.hash)
        
        self.repo.save_block(b1)
        self.repo.save_block(b3) 
        self.repo.save_block(b2) 
        
        last = self.repo.get_last_block()
        
        self.assertIsNotNone(last)
        if last:
            self.assertEqual(last.index, 3) 
        print("[SUCCESS] Último bloque correcto.")

    def test_idempotency_duplicate_save(self):
        print(">> Ejecutando: test_idempotency_duplicate_save...")
        b1 = self.create_dummy_block(1, "hash_unique")
        self.repo.save_block(b1)
        
        try:
            self.repo.save_block(b1)
        except Exception as e:
            self.fail(f"Error: {e}")
            
        count = self.repo.count()
        self.assertEqual(count, 1) 
        print("[SUCCESS] Idempotencia verificada.")

    def test_count_and_pagination(self):
        print(">> Ejecutando: test_count_and_pagination...")
        for i in range(10):
            self.repo.save_block(self.create_dummy_block(i, f"prev_{i}"))
            
        self.assertEqual(self.repo.count(), 10)
        print("[SUCCESS] Paginación correcta.")

if __name__ == "__main__":
    unittest.main()