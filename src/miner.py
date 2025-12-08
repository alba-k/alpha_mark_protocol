import sys
from typing import Dict, Any # <--- Herramientas de Tipado

# Asumimos que utils también tiene tipado (lo veremos si da error, pero por ahora está bien)
from src.utils import validate_address

class Miner:
    # 1. TIPADO: Exigimos un Diccionario de configuración al nacer
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config: Dict[str, Any] = config
        
        # 2. EXTRACCIÓN SEGURA:
        # Usamos str(...) para garantizar que sea texto, aunque en el JSON sea otra cosa.
        # Accedemos a los diccionarios anidados ["payout"]["..."]
        self.payout_address: str = str(config["payout"]["payout_address"])
        self.coinbase_msg: str = str(config["payout"]["coinbase_message"])
        self.rpc_url: str = str(config["connection"]["node_rpc_url"])

    def start(self) -> None:
        print("\n[MINERO] Inicializando motor de minería AKM...")
        
        # 3. VALIDACIÓN DE SEGURIDAD
        if validate_address(self.payout_address):
            print(f"[SEGURIDAD] Dirección de pago VÁLIDA: {self.payout_address}")
        else:
            print(f"[ERROR FATAL] Dirección de pago INVÁLIDA o INSEGURA.")
            print("El minero se detendrá para proteger tus recursos.")
            sys.exit(1) # Esto detiene el script

        print(f"[CONEXIÓN] Conectando al nodo en: {self.rpc_url}")
        print(f"[INFO] Mensaje en bloque: '{self.coinbase_msg}'")
        
        # 4. BUCLE DE MINADO (Ahora con tipado matemático)
        print(">>> MINANDO AHORA (Presiona Ctrl+C para detener) <<<")
        
        # Definimos 'nonce' explícitamente como entero grande
        nonce: int = 0 
        
        try:
            while True:
                # Aquí iría el hash real SHA256
                nonce += 1
                
                # Operación de módulo para el log (cada 500,000 intentos)
                if nonce % 500000 == 0:
                    print(f"Hash rate actual: Calculando nonce {nonce}...")
                
                # Simular velocidad (comentado para máxima velocidad)
                # time.sleep(0.001) 
                
        except KeyboardInterrupt:
            print("\n[FIN] Minero detenido por el usuario.")