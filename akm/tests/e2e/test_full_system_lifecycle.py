# akm/tests/e2e/test_full_system_lifecycle.py
import sys
import os
import time
import logging
import pytest 

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Imports del Proyecto
from akm.core.factories.node_factory import NodeFactory
from akm.core.services.identity_service import IdentityService
from akm.core.managers.wallet_manager import WalletManager
from akm.infra.crypto.software_signer import SoftwareSigner
from akm.core.config.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')

def test_full_lifecycle():
    # --- 1. Configuración ---
    print("\n=======================================================")
    print("   TEST E2E: SISTEMA REAL (ALPHA MARK PROTOCOL)        ")
    print("=======================================================\n")

    results_dir = os.path.join(project_root, "akm", "tests", "results", "e2e")
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    db_file = os.path.join(results_dir, "e2e_lifecycle.db")
    
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except PermissionError:
            pytest.fail("⚠️ Cierra DB Browser para poder borrar la base de datos antigua.")

    os.environ["AKM_DB_NAME"] = db_file
    os.environ["AKM_STORAGE_ENGINE"] = "sqlite"
    
    print(f"💾 Base de Datos Real: {db_file}")

    # --- 2. Inicializar Nodo ---
    print("\n[1] Arrancando Nodo Minero...")
    try:
        setattr(ConfigManager, "_instance", None)
        node = NodeFactory.create_miner_node()
    except Exception as e:
        pytest.fail(f"❌ Error fatal al crear el nodo: {e}")

    # --- BLOQUE PRINCIPAL DE PRUEBA ---
    # Usamos try/finally para asegurar que el nodo se apague SIEMPRE,
    # incluso si la prueba falla a la mitad.
    try:
        # --- 3. Identidades ---
        print("\n[2] Generando Identidades...")
        identity_service = IdentityService()
        alice_data = identity_service.create_new_identity()
        bob_data = identity_service.create_new_identity()
        
        print(f"   👤 Alice (Minero): {alice_data['address']}")
        print(f"   👤 Bob (Destino):  {bob_data['address']}")

        # --- 4. Minería ---
        print("\n[3] Iniciando Minería...")
        node.start_mining_loop(alice_data['address'])
        node.start() 

        target_height = 5
        print(f"   ⏳ Minando {target_height} bloques...")
        
        timeout = time.time() + 30 
        while True:
            last = node.blockchain.last_block
            height = last.index if last else 0
            if height >= target_height:
                break
            if time.time() > timeout:
                pytest.fail("⏱️ Timeout esperando bloques.")
            time.sleep(1)
        
        print(f"   ✅ Altura {target_height} alcanzada.")
        
        # --- 5. Transacción ---
        amount = 10
        print(f"\n[4] Enviando {amount} ALBA de Alice a Bob...")
        
        alice_wallet = WalletManager(SoftwareSigner(alice_data['private_key']))
        tx = alice_wallet.create_transaction(bob_data['address'], amount, 1, node.utxo_set)
        
        assert node.submit_transaction(tx) == True, "❌ El nodo rechazó la transacción"
        print("   🚀 TX aceptada en Mempool.")

        # --- 6. Confirmación ---
        print("\n[5] Esperando confirmación...")
        confirmed = False
        for _ in range(30):
            if node.get_balance(bob_data['address']) >= amount:
                confirmed = True
                print(f"   ✅ ¡Confirmado! Bob tiene {node.get_balance(bob_data['address'])} ALBA.")
                break
            time.sleep(1)

        assert confirmed, "⚠️ La transacción nunca se confirmó."

        # --- 7. Verificación Final ---
        balance_bob = node.get_balance(bob_data['address'])
        assert balance_bob == amount, f"Bob debería tener {amount}, pero tiene {balance_bob}."
        
        print("\n🏆 RESULTADO: PASÓ (SUCCESS)")

    finally:
        # --- 8. Limpieza ---
        # Este bloque se ejecuta SIEMPRE, incluso si hay errores arriba.
        print("\n🛑 Apagando nodo...")
        if 'node' in locals():
            node.stop_mining()
            node.stop() # type: ignore

if __name__ == "__main__":
    test_full_lifecycle()