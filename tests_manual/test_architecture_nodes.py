# tests_manual/test_architecture_nodes.py
import sys
import os
import time

# Ajuste de rutas
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, root_dir)

from akm.core.factories.node_factory import NodeFactory
from akm.infra.persistence.database_manager import DatabaseManager
from akm.core.config.protocol_constants import ProtocolConstants

def test_architecture():
    print("--- TEST DE ARQUITECTURA: MINER NODE vs SPV NODE ---")
    
    # 1. Preparar Servidor (Miner Node) - Tiene DB y Minero
    DatabaseManager.reset()
    server = NodeFactory.create_miner_node()
    
    # Minar historia (Génesis + 2 bloques)
    print("\n[SERVIDOR] Generando Blockchain...")
    server.mine_one_block("ADDR_TEST_SRV")
    time.sleep(0.1)
    server.mine_one_block("ADDR_TEST_SRV")
    
    # +1 por el Génesis automático
    print(f"✅ Servidor Altura (Bloques Completos): {len(server.blockchain)}")

    # 2. Preparar Cliente (SPV Node - Móvil) - Tiene RAM y Headers
    client = NodeFactory.create_spv_node()
    print("\n[CLIENTE] Nodo Móvil iniciado (Memoria vacía).")
    print(f"📱 Cliente Altura Inicial: {client.header_chain.height}")

    # 3. BRIDGE DE RED VIRTUAL (Simulación P2P)
    print("\n[RED] Conectando nodos virtualmente...")
    
    # Bridge: Cliente -> Servidor (Solicitud)
    def bridge_client_to_server(msg, peer_id=None):
        if msg['type'] == ProtocolConstants.MSG_GET_HEADERS:
            print("   >>> [Red] GET_HEADERS viaja al Servidor")
            # El servidor procesa la petición
            server.gossip._handle_network_message(msg, "Mobile_Client_01")
            
    # Bridge: Servidor -> Cliente (Respuesta)
    def bridge_server_to_client(msg, peer_id=None):
        if msg['type'] == ProtocolConstants.MSG_HEADERS:
            print("   <<< [Red] HEADERS viajan al Cliente")
            # El cliente procesa la respuesta
            client._process_payload(msg['type'], msg['payload'], "Server_Node_01")

    # Interceptamos la red
    client.p2p.broadcast = bridge_client_to_server
    server.p2p.broadcast = bridge_server_to_client

    # 4. EJECUCIÓN
    print("\n[ACCIÓN] Cliente pulsa 'Sincronizar'...")
    client.sync()
    
    # Esperamos un momento a que el procesamiento termine
    time.sleep(1)
    
    # 5. VERIFICACIÓN
    print("\n[RESULTADO]")
    server_height = len(server.blockchain)
    client_height = client.header_chain.height
    
    print(f"✅ Servidor Altura: {server_height}")
    print(f"📱 Cliente Altura:  {client_height}")
    
    if client_height == server_height:
        print("\n✅ ÉXITO TOTAL: El celular tiene la copia ligera de la cadena.")
        print("   Arquitectura Modular Validada.")
    elif client_height > 0:
        print(f"\n⚠️  PARCIAL: El cliente sincronizó {client_height} de {server_height} headers.")
    else:
        print("\n❌ FALLO: Desincronizados.")

    DatabaseManager().close()

if __name__ == "__main__":
    test_architecture()