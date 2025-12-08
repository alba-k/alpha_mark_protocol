# tests_manual/test_persistence_flow.py
import sys
import os
import time

# Hack para rutas
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, root_dir)

from akm.core.factories.node_factory import NodeFactory
from akm.infra.persistence.database_manager import DatabaseManager

def clean_environment():
    """Borra la DB anterior para empezar de cero."""
    db_path = os.path.join(root_dir, "blockchain_oficial.db")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("🧹 DB eliminada.")
        except:
            pass
    
    if os.path.exists("blockchain_oficial.db"):
        try:
            os.remove("blockchain_oficial.db")
        except:
            pass

def run_test():
    print("--- INICIANDO TEST DE PERSISTENCIA ---")
    clean_environment()

    # FASE 1: Nacer y Minar
    print("\n[FASE 1] Iniciando nodo por primera vez...")
    
    # 1. Usamos método público para asegurar estado limpio
    DatabaseManager.reset()
    
    node1 = NodeFactory.create_miner_node()
    
    print(f"Altura inicial: {len(node1.blockchain)}")
    
    miner_address = "AKM_TEST_MINER_ADDR"
    print(f"⛏️  Minando 2 bloques para {miner_address}...")
    
    # ⚡ CORRECCIÓN: Pasamos la dirección explícitamente
    if node1.mine_one_block(miner_address): 
        print("✅ Bloque 1 minado y aceptado.")
    else:
        print("❌ Falló minado Bloque 1")
    time.sleep(0.5) 
    
    if node1.mine_one_block(miner_address):
        print("✅ Bloque 2 minado y aceptado.")
    else:
        print("❌ Falló minado Bloque 2")
    
    balance_fase_1 = node1.get_balance(miner_address)
    height_fase_1 = len(node1.blockchain)
    
    print(f"💰 Balance Fase 1: {balance_fase_1} Albas")
    print(f"📏 Altura Fase 1: {height_fase_1}")

    # Simular Apagado
    print("\n🔌 SIMULANDO APAGADO DEL NODO...")
    
    # 2. Cierre limpio
    DatabaseManager().close()
    del node1
    
    # 3. Reset
    DatabaseManager.reset()

    # FASE 2: Renacer
    print("\n[FASE 2] Reiniciando nodo (Leyendo disco)...")
    node2 = NodeFactory.create_miner_node()
    
    height_fase_2 = len(node2.blockchain)
    balance_fase_2 = node2.get_balance(miner_address)
    
    print(f"📏 Altura Fase 2: {height_fase_2}")
    print(f"💰 Balance Fase 2: {balance_fase_2} Albas")
    
    # VERIFICACIÓN
    if height_fase_1 == height_fase_2 and balance_fase_1 == balance_fase_2:
        if height_fase_1 > 1:
            print("\n✅ ÉXITO TOTAL: El nodo recordó todo después de apagarse.")
            print("   - Blockchain persistente: OK")
            print("   - UTXO Set persistente: OK")
        else:
            print("\n⚠️  PARCIAL: El nodo persistió, pero no se minaron bloques nuevos.")
    else:
        print("\n❌ FALLO: Datos inconsistentes.")
        print(f"   Diferencia Altura: {height_fase_1} vs {height_fase_2}")
        print(f"   Diferencia Saldo: {balance_fase_1} vs {balance_fase_2}")

if __name__ == "__main__":
    run_test()