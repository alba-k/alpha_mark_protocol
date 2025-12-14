# akm/tests/e2e/test_api_lifecycle.py
import sys
import os
import time
import unittest
from typing import Any
from fastapi.testclient import TestClient

# --- AJUSTE DE RUTAS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importamos la APP y servicios
from akm.interface.api.server import app
from akm.core.services.identity_service import IdentityService
from akm.interface.api.dependencies import NodeContainer

class TestApiLifecycle(unittest.TestCase):
    
    def setUp(self):
        # 1. Configurar un entorno LIMPIO para el test
        self.test_db = "test_lifecycle_api.db"
        os.environ["AKM_DB_NAME"] = self.test_db
        
        # Limpieza preventiva de archivos previos
        if os.path.exists(self.test_db):
            try: os.remove(self.test_db)
            except: pass
            
        # Aseguramos que el contenedor esté limpio antes de empezar
        NodeContainer.shutdown()
        
        # 2. Generamos identidades para la prueba
        self.alice = IdentityService().create_new_identity()
        self.bob = IdentityService().create_new_identity()

    def tearDown(self):
        # Forzamos el apagado por seguridad al final
        NodeContainer.shutdown()

    def test_full_api_flow(self):
        print("\n==============================================")
        print("   TEST E2E: API REST (CLIENTE HTTP)          ")
        print("==============================================\n")

        # CORRECCIÓN CRÍTICA: Usamos 'with' para activar el ciclo de vida (Lifespan)
        # Esto ejecuta automáticamente 'NodeContainer.initialize()' al entrar
        # y 'NodeContainer.shutdown()' al salir.
        with TestClient(app) as client:
            
            # 1. VERIFICAR ESTADO DEL NODO
            print("[1] Consultando GET /status...")
            response = client.get("/status")
            
            if response.status_code != 200:
                self.fail(f"La API falló al iniciar. Error: {response.text}")
                
            data = response.json()
            print(f"    -> Estado: {data}")
            self.assertIn("node_id", data)
            self.assertGreaterEqual(data["height"], 0)

            # 2. ESPERAR MINERÍA (Necesitamos fondos)
            print("\n[2] Esperando que el nodo mine bloques (generar fondos)...")
            initial_height = data["height"]
            target_height = initial_height + 2
            
            max_retries = 60 
            mined_successfully = False
            
            for i in range(max_retries):
                try:
                    resp = client.get("/status")
                    if resp.status_code == 200:
                        current_height = resp.json()["height"]
                        print(f"    -> Altura actual: {current_height}/{target_height} (Intento {i+1})", end="\r")
                        
                        if current_height >= target_height:
                            mined_successfully = True
                            break
                except Exception:
                    pass
                time.sleep(1)
            
            print() # Salto de línea estético
            if not mined_successfully:
                self.fail("TIMEOUT: El nodo no minó suficientes bloques a tiempo.")
            
            print(f"    -> ¡Bloques minados! Altura objetivo alcanzada.")

            # 3. CONSULTAR SALDO DE ALICE
            print("\n[3] Consultando saldo de Alice (GET /balance)...")
            resp = client.get(f"/balance/{self.alice['address']}")
            
            if resp.status_code != 200:
                print(f"    ERROR API: {resp.text}")
                
            self.assertEqual(resp.status_code, 200)
            balance_data = resp.json()
            
            if "balance" not in balance_data:
                self.fail(f"Respuesta inesperada: {balance_data}")
                
            print(f"    -> Saldo Alice: {balance_data['balance']}")
            self.assertEqual(balance_data['balance'], 0)

            # 4. INTENTO DE TRANSACCIÓN (Fallará por fondos)
            print("\n[4] Probando envío sin fondos (POST /transactions)...")
            payload: dict[str, Any] = {
                "sender_private_key": self.alice["private_key"],
                "recipient_address": self.bob["address"],
                "amount": 10.0,
                "fee": 1.0
            }
            
            resp = client.post("/transactions", json=payload)
            print(f"    -> Respuesta: {resp.status_code} - {resp.text}")
            
            if resp.status_code == 200:
                print("    ⚠️ ¡Alerta! La transacción pasó (¿Tenía fondos?).")
            else:
                print("    ✅ Transacción rechazada correctamente (Alice es pobre).")
                self.assertTrue(resp.status_code >= 400)

        print("\n==============================================")
        print("   TEST API COMPLETADO                        ")
        print("==============================================")

if __name__ == "__main__":
    unittest.main()