# akm/tests/e2e/test_api_spv_lifecycle.py
import sys
import os
import unittest
from fastapi.testclient import TestClient

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from akm.interface.api.server import app
from akm.interface.api.dependencies import NodeContainer

class TestApiSPV(unittest.TestCase):
    
    def setUp(self):
        # 1. Configurar entorno SPV
        os.environ["NODE_TYPE"] = "SPV"
        os.environ["AKM_DB_NAME"] = "test_spv.db" # No se usará, pero por si acaso
        
        # Limpieza
        NodeContainer.shutdown()

    def tearDown(self):
        NodeContainer.shutdown()
        # Restaurar entorno
        if "NODE_TYPE" in os.environ:
            del os.environ["NODE_TYPE"]

    def test_spv_mode_initialization(self):
        print("\n=== TEST API: MODO SPV (MÓVIL) ===")
        
        with TestClient(app) as client:
            
            # 1. Verificar Estado
            print("[1] Verificando /status...")
            resp = client.get("/status")
            self.assertEqual(resp.status_code, 200)
            
            data = resp.json()
            print(f"    -> {data}")
            
            # ASERCIÓN CRÍTICA: ¿Es un SPV?
            self.assertEqual(data["environment"], "SPV_MOBILE")
            self.assertIn("API-SPV_MOBILE", data["node_id"])
            
            # 2. Verificar Comportamiento Diferenciado (Blocks)
            print("[2] Verificando /blocks (Debe estar vacío en SPV)...")
            resp_blocks = client.get("/blocks")
            self.assertEqual(resp_blocks.status_code, 200)
            self.assertEqual(len(resp_blocks.json()), 0)
            print("    -> OK: Lista vacía recibida.")

            # 3. Verificar Balance (Debe ser 0/Mock)
            print("[3] Verificando /balance...")
            resp_bal = client.get("/balance/CUALQUIER_DIRECCION")
            self.assertEqual(resp_bal.status_code, 200)
            self.assertEqual(resp_bal.json()["balance"], 0.0)
            print("    -> OK: Balance 0 (Modo ligero).")

        print("=== TEST SPV COMPLETADO CON ÉXITO ===")

if __name__ == "__main__":
    unittest.main()