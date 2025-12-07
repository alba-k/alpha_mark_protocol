# akm/core/managers/gossip_manager.py
import logging
import threading
from typing import Dict, Any, Optional
from collections import deque

# Interfaces
from akm.core.interfaces.i_network import INetworkService

logger = logging.getLogger(__name__)

class _DedupCache:
    """
    Clase auxiliar privada para deduplicación Thread-Safe.
    """
    def __init__(self, max_size: int = 10000):
        # [FIX Línea 16] Tipado explícito para el contenedor genérico
        self._cache: deque[str] = deque(maxlen=max_size)
        self._set: set[str] = set()
        self._lock = threading.Lock()
        
        # [FIX Línea 27] Guardamos el límite como int puro para evitar errores de Optional[int]
        self._limit = max_size

    def is_known(self, item_hash: str) -> bool:
        if not item_hash: return True
        
        with self._lock:
            if item_hash in self._set: return True
            
            self._set.add(item_hash)
            self._cache.append(item_hash)
            
            # [FIX Línea 27] Usamos self._limit (int) en lugar de self._cache.maxlen (Optional[int])
            if len(self._set) > (self._limit * 2):
                 self._set = set(self._cache)
            
            return False

class GossipManager:
    """
    Gestor de Propagación.
    Depende de la abstracción INetworkService.
    """

    def __init__(self, network_service: INetworkService):
        self.network = network_service
        self._dedup_cache = _DedupCache(max_size=10000)

    def propagate_block(self, block_data: Dict[str, Any], origin_peer: Optional[str] = None):
        self._propagate_entity(block_data, "BLOCK", "hash", origin_peer)

    def propagate_transaction(self, tx_data: Dict[str, Any], origin_peer: Optional[str] = None):
        self._propagate_entity(tx_data, "TX", "tx_hash", origin_peer)

    def mark_as_seen(self, item_hash: str):
        self._dedup_cache.is_known(item_hash)

    def _propagate_entity(self, entity_data: Dict[str, Any], msg_type: str, hash_key: str, origin_peer: Optional[str]):
        payload, item_hash = self._normalize_input(entity_data, hash_key)

        if not item_hash or self._dedup_cache.is_known(item_hash):
            return

        message: Dict[str, Any] = {
            "type": msg_type,
            "payload": payload
        }
        
        logger.info(f"📢 Propagando {msg_type} {item_hash[:8]}...")
        self.network.broadcast(message, exclude_peer=origin_peer)

    def _normalize_input(self, data: Dict[str, Any], hash_key: str) -> tuple[Dict[str, Any], Optional[str]]:
        if "payload" in data and hash_key not in data:
            inner = data["payload"]
            return inner, str(inner.get(hash_key, ""))
        return data, str(data.get(hash_key, ""))