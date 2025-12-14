# akm/tests/unit/test_repository_factory.py
import sys
import os
import unittest
from unittest.mock import patch

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importaciones
from akm.infra.persistence.repository_factory import RepositoryFactory
from akm.infra.persistence.sqlite.sqlite_blockchain_repository import SqliteBlockchainRepository
from akm.infra.persistence.json.json_repository import JsonBlockchainRepository
from akm.core.config.config_manager import ConfigManager
from akm.infra.persistence.database_manager import DatabaseManager

class TestRepositoryFactory(unittest.TestCase):

    def setUp(self):
        """
        Configuración PREVIA:
        1. Prepara carpeta de resultados.
        2. Configura un nombre de archivo único para este test.
        """
        self.results_dir = os.path.join(project_root, "akm", "tests", "results", "factory")
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        self.db_path = self._get_unique_db_path("factory_test")
        
        # --- CORRECCIÓN CLAVE: Limpieza de Singletons ---
        # Garantizamos que no haya instancias sucias de tests anteriores
        setattr(ConfigManager, "_instance", None)
        setattr(DatabaseManager, "_instance", None)

    def tearDown(self):
        """Limpieza y cierre de conexiones."""
        if getattr(DatabaseManager, "_instance", None):
            try:
                DatabaseManager().get_connection().close()
            except Exception:
                pass

        # Resetear Singletons para no afectar otros tests
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

    def test_factory_creates_sqlite(self):
        print(">> Ejecutando: test_factory_creates_sqlite...")
        
        # 1. Configuración Vía Entorno (Limpio y Seguro)
        env_vars = {
            "AKM_STORAGE_ENGINE": "sqlite",
            "AKM_DB_NAME": self.db_path
        }
        
        with patch.dict(os.environ, env_vars):
            # Al instanciar ConfigManager aquí, leerá las variables parchadas
            repo = RepositoryFactory.get_repository()
            
            self.assertIsInstance(repo, SqliteBlockchainRepository)
            
            # Verificamos que realmente usó nuestra ruta
            config = ConfigManager()
            self.assertEqual(config.persistence.db_name, self.db_path)
            
        print("[SUCCESS] Fábrica entregó SQLite correctamente configurado.")

    def test_factory_creates_json(self):
        print(">> Ejecutando: test_factory_creates_json...")
        
        env_vars = {"AKM_STORAGE_ENGINE": "json"}
        
        with patch.dict(os.environ, env_vars):
            # Reiniciamos singleton para que relea la config
            setattr(ConfigManager, "_instance", None)
            
            repo = RepositoryFactory.get_repository()
            self.assertIsInstance(repo, JsonBlockchainRepository)
            
        print("[SUCCESS] Fábrica entregó JSON.")

    def test_factory_rejects_invalid(self):
        print(">> Ejecutando: test_factory_rejects_invalid...")
        
        env_vars = {"AKM_STORAGE_ENGINE": "invalid_db_type"}
        
        with patch.dict(os.environ, env_vars):
            setattr(ConfigManager, "_instance", None)
            
            with self.assertRaises(ValueError):
                RepositoryFactory.get_repository()
            
        print("[SUCCESS] Fábrica rechazó configuración inválida.")

if __name__ == "__main__":
    unittest.main()