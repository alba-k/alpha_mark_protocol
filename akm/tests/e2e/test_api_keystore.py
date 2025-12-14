# akm/tests/e2e/test_api_keystore.py
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

# Importamos la APP
from akm.interface.api.server import app
from akm.interface.api.dependencies import NodeContainer

class TestApiKeystore(unittest.TestCase):
    
    def setUp(self):
        # 1. Entorno Limpio
        self.test_db = "test_keystore_flow.db"
        self.test_wallet = "test_wallet.dat"
        os.environ["AKM_DB_NAME"] = self.test_db
        
        # Borramos archivos viejos para empezar de cero
        self._clean_files()
        
        # Reiniciamos el contenedor
        NodeContainer.shutdown()
        # Forzamos que el Keystore use el archivo de prueba
        from akm.infra.identity.keystore import Keystore
        NodeContainer._keystore = Keystore(filepath=self.test_wallet) # type: ignore

    def tearDown(self):
        NodeContainer.shutdown()
        self._clean_files()

    def _clean_files(self):
        for f in [self.test_db, self.test_wallet]:
            if os.path.exists(f):
                try: os.remove(f)
                except: pass

    def test_secure_flow(self):
        print("\n==============================================")
        print("   TEST E2E: FLUJO DE BILLETERA SEGURA        ")
        print("==============================================\n")

        with TestClient(app) as client:
            # 1. CREAR BILLETERA (El paso nuevo)
            print("[1] Creando Billetera Segura (POST /wallet/create)...")
            wallet_payload = {"password": "password_super_secreto_123"}
            resp = client.post("/wallet/create", json=wallet_payload)
            
            self.assertEqual(resp.status_code, 200)
            wallet_data = resp.json()
            
            my_address = wallet_data['address']
            mnemonic = wallet_data['mnemonic']
            print(f"    -> Billetera Creada: {my_address}")
            print(f"    -> Semilla (Guardar): {mnemonic[:30]}...")
            
            self.assertIsNotNone(mnemonic)
            self.assertEqual(wallet_data['status'], "created_and_loaded")

            # 2. MINERÍA AUTOMÁTICA (Esperar fondos en la nueva wallet)
            print("\n[2] Esperando fondos (Minería automática)...")
            # Al crear la wallet, el nodo redirigió la minería a 'my_address'
            # Esperamos que el balance suba de 0.
            
            max_retries = 30
            has_funds = False
            
            for i in range(max_retries):
                resp = client.get(f"/balance/{my_address}")
                balance = resp.json()['balance']
                
                # Necesitamos al menos 1 bloque confirmado (50 monedas)
                if balance >= 50:
                    print(f"    -> ¡Fondos recibidos! Balance: {balance}")
                    has_funds = True
                    break
                
                print(f"    -> Minando... Balance actual: {balance} (Intento {i+1})", end="\r")
                time.sleep(1) # Esperamos 1 segundo entre chequeos
            
            if not has_funds:
                self.fail("TIMEOUT: El nodo no generó fondos a tiempo.")

            # 3. ENVÍO SEGURO (Sin clave privada)
            print("\n[3] Enviando dinero (POST /transactions)...")
            # NOTA: Ya no enviamos 'sender_private_key'. ¡Es seguro!
            tx_payload: dict[str, Any] = {
                "recipient_address": "1kbDjMzN3s8g5y2q1", # Dirección cualquiera de destino
                "amount": 10.0,
                "fee": 1.0
            }
            
            resp = client.post("/transactions", json=tx_payload)
            print(f"    -> Respuesta: {resp.status_code} - {resp.json()}")
            
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()['status'], "pending_mempool")
            print("    ✅ ¡ÉXITO! Transacción enviada sin exponer la clave privada.")

        print("\n==============================================")
        print("   TEST COMPLETADO: SISTEMA 100% FUNCIONAL    ")
        print("==============================================")

if __name__ == "__main__":
    unittest.main()