import os
from typing import Dict, Any

class MiningConfig:
    """
    Configuración de Minería.
    """
    def __init__(self):
        self._default_miner_address = os.getenv("AKM_MINER_ADDRESS", "")
        self._mining_threads = int(os.getenv("AKM_MINING_THREADS", 1))
        self._coinbase_message = os.getenv("AKM_COINBASE_MSG", "Mined by AKM")

    @property
    def default_miner_address(self) -> str: return self._default_miner_address
    @property
    def mining_threads(self) -> int: return self._mining_threads
    @property
    def coinbase_message(self) -> str: return self._coinbase_message

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """
        Recibe un diccionario plano con claves de 'payout' o 'performance'.
        """
        if not data: return
        
        if "payout_address" in data: 
            self._default_miner_address = str(data["payout_address"])
            
        if "coinbase_message" in data: 
            self._coinbase_message = str(data["coinbase_message"])
            
        if "threads" in data: 
            self._mining_threads = int(data["threads"])