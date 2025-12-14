# akm/tests/unit/test_p2p_service.py
import sys
import os
import unittest
import json
from unittest.mock import MagicMock, patch, ANY
from typing import cast

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from akm.infra.network.p2p_service import P2PService
from akm.core.config.config_manager import ConfigManager

class TestP2PService(unittest.TestCase):

    def setUp(self):
        # 1. Resetear Singleton de Configuración Real (Por limpieza)
        setattr(ConfigManager, "_instance", None)

        # 2. MOCKEAR DONDE SE USA (CRÍTICO)
        # En lugar de parchear 'akm.core.config...', parcheamos la referencia
        # que tiene el archivo p2p_service.py.
        # Esto evita romper la clase real y el error de super().
        self.mock_config_patcher = patch('akm.infra.network.p2p_service.ConfigManager')
        self.MockConfigManager = self.mock_config_patcher.start()
        
        # Valores dummy para el mock
        # ConfigManager().network.host -> "127.0.0.1"
        self.MockConfigManager.return_value.network.host = "127.0.0.1"
        self.MockConfigManager.return_value.network.port = 5000
        self.MockConfigManager.return_value.network.seeds = []

        # 3. Mockear ConnectionManager (Infraestructura)
        # Parcheamos también donde se usa: dentro de p2p_service
        self.conn_patcher = patch('akm.infra.network.p2p_service.ConnectionManager')
        self.MockConnectionManagerCls = self.conn_patcher.start()
        
        # Instancia del Mock que usará el servicio
        self.mock_connection_instance = MagicMock()
        self.MockConnectionManagerCls.return_value = self.mock_connection_instance

        # 4. Instanciar el servicio bajo prueba
        self.p2p = P2PService()

    def tearDown(self):
        self.mock_config_patcher.stop()
        self.conn_patcher.stop()
        setattr(ConfigManager, "_instance", None)

    def test_broadcast_serializes_json_correctly(self):
        print("\n>> Ejecutando: test_broadcast_serializes_json_correctly...")
        
        message = {"type": "TEST", "payload": "Hola Mundo"}
        
        self.p2p.broadcast(message)
        
        # Casting para ayudar al linter
        connection_mock = cast(MagicMock, self.p2p.connection)
        
        # Verificar llamada
        connection_mock.send_to_all.assert_called_once_with(ANY, None)
        
        # Verificar contenido
        args, _ = connection_mock.send_to_all.call_args
        bytes_sent = args[0]
        
        decoded_msg = json.loads(bytes_sent.decode('utf-8'))
        
        self.assertEqual(decoded_msg["type"], "TEST")
        self.assertEqual(decoded_msg["payload"], "Hola Mundo")
        self.assertIn("_net_t", decoded_msg)
        
        print("[SUCCESS] Serialización JSON correcta.")

    def test_receive_valid_json_triggers_handler(self):
        print(">> Ejecutando: test_receive_valid_json_triggers_handler...")
        
        mock_handler = MagicMock()
        self.p2p.register_handler(mock_handler)
        
        incoming_json = json.dumps({"type": "BLOCK", "data": 123}).encode('utf-8')
        peer_id = "192.168.1.50:8333"
        
        # Simulamos recepción interna
        self.p2p._on_bytes_received(incoming_json, peer_id) # type: ignore
        
        mock_handler.assert_called_once()
        args, _ = mock_handler.call_args
        data_received = args[0]
        sender_id = args[1]
        
        self.assertEqual(data_received["type"], "BLOCK")
        self.assertEqual(data_received["data"], 123)
        self.assertEqual(sender_id, peer_id)
        print("[SUCCESS] Recepción correcta.")

    def test_broadcast_with_exclude_peer(self):
        print(">> Ejecutando: test_broadcast_with_exclude_peer...")
        
        msg = {"type": "GOSSIP"}
        peer_to_skip = "10.0.0.5:5000"
        
        self.p2p.broadcast(msg, exclude_peer=peer_to_skip)
        
        connection_mock = cast(MagicMock, self.p2p.connection)
        connection_mock.send_to_all.assert_called_with(ANY, peer_to_skip)
        
        print("[SUCCESS] Exclusión correcta.")

if __name__ == "__main__":
    unittest.main()