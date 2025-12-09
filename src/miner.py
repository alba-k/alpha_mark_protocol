import sys
import time


from akm.core.config.config_manager import ConfigManager
from akm.core.factories.node_factory import NodeFactory
from src.utils import validate_address

class Miner:
    def __init__(self) -> None:
        self.config_manager = ConfigManager()
        self.payout_address = self.config_manager.mining.default_miner_address
        
        if not validate_address(self.payout_address):
            print(f"[ERROR] Dirección de pago inválida: {self.payout_address}")
            sys.exit(1)

        print("[INIT] 🏭 Ensamblando Miner Node Real...")
        self.core_node = NodeFactory.create_miner_node()

    def start(self) -> None:
        print("\n[MINERO] Inicializando motor de consenso AKM...")
        print(f"[CONFIG] Payout Address: {self.payout_address}")
        print(f"[RED] Escuchando en puerto: {self.config_manager.network.port}")
        
        # 1. Arrancar servicios de Red
        self.core_node.start() 
        
        # 🔥 CORRECCIÓN CLAVE: PAUSA DE SINCRONIZACIÓN
        # Esperamos 5 segundos para asegurar el Handshake con el Full Node
        print("⏳ [SYNC] Esperando conexión con la red (5s)...")
        time.sleep(5) 
        
        # 2. Ahora sí, arrancamos el minado
        print(">>> ⛏️ INICIANDO MINERÍA REAL (POW) <<<")
        self.core_node.start_mining_loop(miner_address=self.payout_address)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[FIN] Deteniendo minería y nodo...")
            self.core_node.stop_mining()
            self.core_node.stop()