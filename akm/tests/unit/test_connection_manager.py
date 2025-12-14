# akm/tests/unit/test_connection_manager.py
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from akm.infra.network.connection_manager import ConnectionManager

class TestConnectionManager(unittest.TestCase):

    def setUp(self):
        # Callback dummy
        self.mock_callback = MagicMock()
        self.manager = ConnectionManager("0.0.0.0", 5000, self.mock_callback)

    # CORRECCIÓN: Parcheamos threading.Thread para evitar que el hilo de escucha arranque y borre el peer
    @patch('akm.infra.network.connection_manager.threading.Thread') 
    @patch('socket.socket')
    def test_connect_outbound_success(self, mock_socket_cls, mock_thread_cls): # type: ignore
        print("\n>> Ejecutando: test_connect_outbound_success...")
        
        # Configurar el mock del socket
        mock_socket_instance = MagicMock()
        mock_socket_cls.return_value = mock_socket_instance
        
        # Ejecutar conexión
        target_ip = "1.2.3.4"
        target_port = 8333
        result = self.manager.connect_outbound(target_ip, target_port)
        
        # Verificaciones
        self.assertTrue(result)
        mock_socket_instance.connect.assert_called_with((target_ip, target_port))
        
        # Verificar que se agregó a la lista de peers
        peer_id = f"{target_ip}:{target_port}"
        # type: ignore para evitar error de acceso protegido
        self.assertIn(peer_id, self.manager._peers)  # type: ignore
        print("[SUCCESS] Conexión saliente registrada correctamente.")

    def test_send_to_all_logic(self):
        print(">> Ejecutando: test_send_to_all_logic...")
        
        # 1. Simular 3 peers conectados manualmente
        sock1 = MagicMock()
        sock2 = MagicMock()
        sock3 = MagicMock()
        
        # Inyección manual de peers (type: ignore)
        self.manager._peers = {  # type: ignore
            "peer1": sock1,
            "peer2": sock2,
            "peer3": sock3
        } # type: ignore
        
        data = b'{"hola": "mundo"}'
        expected_packet = data + b'\n'
        
        # 2. Enviar a todos
        self.manager.send_to_all(data)
        
        # 3. Verificar que todos recibieron los bytes
        sock1.sendall.assert_called_with(expected_packet)
        sock2.sendall.assert_called_with(expected_packet)
        sock3.sendall.assert_called_with(expected_packet)
        print("[SUCCESS] Broadcast a todos los peers correcto.")

    def test_send_to_all_with_exclusion(self):
        print(">> Ejecutando: test_send_to_all_with_exclusion...")
        
        sock1 = MagicMock()
        sock2 = MagicMock() 
        
        self.manager._peers = {"peer1": sock1, "peer2": sock2} # type: ignore
        
        data = b'ping'
        
        # Enviar excluyendo a peer2
        self.manager.send_to_all(data, exclude_peer="peer2")
        
        # Verificar
        sock1.sendall.assert_called() 
        sock2.sendall.assert_not_called() 
        
        print("[SUCCESS] Lógica de exclusión (Gossip) correcta.")

if __name__ == "__main__":
    unittest.main()