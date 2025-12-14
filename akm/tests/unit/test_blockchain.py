# akm/tests/unit/test_blockchain.py
'''
Test Suite para el Modelo Blockchain (Integración Real).
    Verifica que la clase Blockchain funcione correctamente conectada
    a un repositorio SQLite real, guardando y recuperando bloques del disco.
'''

import sys
import os
import unittest
import time

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importaciones
from akm.core.models.blockchain import Blockchain
from akm.core.models.block import Block
from akm.core.models.transaction import Transaction
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput
from akm.infra.persistence.sqlite.sqlite_blockchain_repository import SqliteBlockchainRepository
from akm.core.config.config_manager import ConfigManager
from akm.infra.persistence.database_manager import DatabaseManager

class TestBlockchainIntegration(unittest.TestCase):

    def setUp(self):
        """
        Configuración de Integración:
        1. Prepara carpeta de resultados.
        2. Configura una DB SQLite real única para este test.
        3. Instancia la Blockchain conectada a esa DB.
        """
        # 1. Carpeta de resultados
        self.results_dir = os.path.join(project_root, "akm", "tests", "results", "blockchain_model")
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        # 2. Nombre único de DB
        self.db_path = self._get_unique_db_path("chain_test")
        print(f"\n[SETUP] DB de integración: {self.db_path}")

        # 3. Resetear Singletons
        setattr(ConfigManager, "_instance", None)
        setattr(DatabaseManager, "_instance", None)

        # 4. Inyectar configuración (Sin tocar atributos privados directamente si es posible,
        # pero como tu ConfigManager es manual, esta es la forma de hacerlo en tests)
        config = ConfigManager()
        config.persistence._db_name = self.db_path # type: ignore
        config.persistence._storage_engine = "sqlite" # type: ignore

        # 5. Crear Repositorio Real
        self.repository = SqliteBlockchainRepository()
        
        # 6. Crear Blockchain Real
        self.blockchain = Blockchain(repository=self.repository)

    def tearDown(self):
        if hasattr(self, 'repository'):
            self.repository.conn.close()
        
        setattr(ConfigManager, "_instance", None)
        setattr(DatabaseManager, "_instance", None)

    def _get_unique_db_path(self, base_name: str) -> str:
        counter = 1
        while True:
            filename = f"{base_name}_{counter}.db"
            full_path = os.path.join(self.results_dir, filename)
            if not os.path.exists(full_path):
                return full_path
            counter += 1

    def create_real_block(self, index: int, prev_hash: str) -> Block:
        """Crea un bloque con estructura válida."""
        inp = TxInput("0000" * 16, 0, "sig_real")
        out = TxOutput(50, "miner_address_real")
        tx = Transaction(f"tx_hash_{index}", int(time.time()), [inp], [out], fee=0)
        
        return Block(
            index=index,
            timestamp=int(time.time()),
            previous_hash=prev_hash,
            bits="1d00ffff",
            merkle_root=f"merkle_root_{index}",
            nonce=12345,
            block_hash=f"block_hash_{index}",
            transactions=[tx]
        )

    def test_add_and_retrieve_block_real(self):
        print(">> Ejecutando: test_add_and_retrieve_block_real...")
        
        # 1. Crear Génesis
        genesis = self.create_real_block(0, "0" * 64)
        self.blockchain.add_block(genesis)
        
        # 2. Verificar que 'last_block' lo recupera del disco
        last = self.blockchain.last_block
        self.assertIsNotNone(last)
        if last:
            self.assertEqual(last.index, 0)
            self.assertEqual(last.hash, genesis.hash)
            
        print("[SUCCESS] Bloque añadido y recuperado desde SQLite.")

    def test_chain_persistence_integrity(self):
        print(">> Ejecutando: test_chain_persistence_integrity...")
        
        # Añadir 3 bloques
        b0 = self.create_real_block(0, "000")
        self.blockchain.add_block(b0)
        
        b1 = self.create_real_block(1, b0.hash)
        self.blockchain.add_block(b1)
        
        b2 = self.create_real_block(2, b1.hash)
        self.blockchain.add_block(b2)
        
        # 1. Verificar Altura
        self.assertEqual(len(self.blockchain), 3)
        
        # 2. Verificar búsqueda por Hash
        retrieved_b1 = self.blockchain.get_block_by_hash(b1.hash)
        self.assertIsNotNone(retrieved_b1)
        if retrieved_b1:
            self.assertEqual(retrieved_b1.index, 1)
            self.assertEqual(retrieved_b1.previous_hash, b0.hash)
            
        # 3. Verificar búsqueda por Índice
        retrieved_b2 = self.blockchain.get_block_by_index(2)
        self.assertIsNotNone(retrieved_b2)
        if retrieved_b2:
            self.assertEqual(retrieved_b2.hash, b2.hash)
            
        print("[SUCCESS] Integridad de la cadena en disco verificada.")

    def test_replace_chain_real(self):
        print(">> Ejecutando: test_replace_chain_real...")
        
        # Cadena original (Corta)
        b0 = self.create_real_block(0, "gen")
        self.blockchain.add_block(b0)
        
        # Nueva cadena (Más larga, reorg)
        new_b1 = self.create_real_block(1, b0.hash)
        new_b2 = self.create_real_block(2, new_b1.hash)
        new_chain = [b0, new_b1, new_b2]
        
        # Ejecutar Reemplazo
        self.blockchain.replace_chain(new_chain)
        
        # Verificar que la DB tiene ahora 3 bloques (o los actualizados)
        # Nota: En tu implementación simple de replace_chain, sobrescribe/añade.
        self.assertEqual(len(self.blockchain), 3)
        self.assertEqual(self.blockchain.last_block.hash, new_b2.hash) # type: ignore
        
        print("[SUCCESS] Reemplazo de cadena en disco exitoso.")

if __name__ == "__main__":
    unittest.main()