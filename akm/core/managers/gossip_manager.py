# akm/core/managers/gossip_manager.py

import logging
from typing import Dict, Any, Optional, TYPE_CHECKING

# Configuración e Infraestructura
from akm.core.config.protocol_constants import ProtocolConstants
from akm.core.interfaces.i_network import INetworkService
from akm.core.services.merkle_tree_builder import MerkleTreeBuilder

if TYPE_CHECKING:
    from akm.core.models.blockchain import Blockchain

logger = logging.getLogger(__name__)

class GossipManager:
    """
    Gestor encargado de la propagación de información (Gossip) y 
    respuestas a solicitudes de sincronización ligera (SPV).
    """

    def __init__(self, p2p_service: INetworkService, blockchain: Optional['Blockchain'] = None):
        try:
            self.p2p = p2p_service
            self.blockchain = blockchain
            
            # Registro del callback principal
            self.p2p.register_handler(self._handle_network_message)
            logger.info("✅ Gestor de difusión (Gossip) activo.")
        except Exception:
            logger.exception("Error al inicializar GossipManager")

    def set_blockchain(self, blockchain: 'Blockchain'):
        self.blockchain = blockchain

    # --- DIFUSIÓN PÚBLICA (GOSSIP) ---
    
    def propagate_block(self, block_payload: Dict[str, Any], origin_peer: Optional[str] = None):
        try:
            msg: Dict[str, Any] = {"type": ProtocolConstants.MSG_BLOCK, "payload": block_payload}
            self.p2p.broadcast(msg, exclude_peer=origin_peer)
            
            block_idx = block_payload.get('index', '???')
            logger.info(f"📡 Gossip: Propagando bloque #{block_idx}.")
        except Exception:
            logger.exception("Fallo en propagación de bloque")

    def propagate_transaction(self, tx_payload: Dict[str, Any], origin_peer: Optional[str] = None):
        try:
            msg: Dict[str, Any] = {"type": ProtocolConstants.MSG_TX, "payload": tx_payload}
            self.p2p.broadcast(msg, exclude_peer=origin_peer)
            
            tx_id = tx_payload.get('tx_hash', '????')[:8]
            logger.info(f"📡 Gossip: Propagando TX {tx_id}...")
        except Exception:
            logger.exception("Fallo en propagación de transacción")

    # --- SERVICIOS SPV (RESPUESTAS UNICAST) ---

    def process_get_headers(self, payload: Any, peer_id: str):
        if not self.blockchain: return

        try:
            locator_hash = payload.get("start_hash", "")
            limit = min(payload.get("limit", 2000), 2000)
            
            headers = self.blockchain.get_headers(locator_hash, limit)
            
            if headers:
                response: Dict[str, Any] = {"type": ProtocolConstants.MSG_HEADERS, "payload": headers}
                self.p2p.send_message(peer_id, response)
                logger.info(f"SPV: Enviados {len(headers)} headers a {peer_id[:8]}.")
        except Exception:
            logger.exception(f"Error sirviendo headers a {peer_id[:8]}")

    def process_get_proof(self, payload: Any, peer_id: str):
        if not self.blockchain: return
        
        try:
            tx_hash = payload.get("tx_hash")
            target_block = None
            
            # Búsqueda de la TX en la historia
            # NOTA: Esto puede ser lento si la cadena es larga. Idealmente usar índices.
            for block in self.blockchain.get_history_iterator(): 
                if any(getattr(tx, 'tx_hash', None) == tx_hash for tx in block.transactions):
                    target_block = block
                    break
            
            if target_block:
                all_hashes = [getattr(tx, 'tx_hash', "") for tx in target_block.transactions]
                proof = MerkleTreeBuilder.get_proof(all_hashes, tx_hash)
                
                if proof:
                    response: Dict[str, Any] = {
                        "type": ProtocolConstants.MSG_MERKLE_PROOF,
                        "payload": {
                            "tx_hash": tx_hash,
                            "block_hash": getattr(target_block, 'hash', getattr(target_block, 'block_hash', '')),
                            "merkle_root": target_block.merkle_root,
                            "proof": proof
                        }
                    }
                    self.p2p.send_message(peer_id, response)
                    logger.info(f"SPV: Prueba Merkle enviada para TX {tx_hash[:8]}.")
            else:
                logger.info(f"SPV: TX {tx_hash[:8]} no hallada. Solicitud ignorada.")

        except Exception:
            logger.exception("Error procesando Merkle Proof Request")

    # --- ENRUTADOR DE MENSAJES (ROUTER) ---

    def dispatch_message(self, msg_type: str, payload: Any, peer_id: str) -> None:
        """
        [FIX] Método público para enrutar mensajes específicos delegados
        desde otros nodos (ej. MinerNode) o recibidos directamente.
        """
        if msg_type == ProtocolConstants.MSG_GET_HEADERS:
            self.process_get_headers(payload, peer_id)
            
        elif msg_type == ProtocolConstants.MSG_GET_MERKLE_PROOF:
            self.process_get_proof(payload, peer_id)

    def _handle_network_message(self, data: Dict[str, Any], peer_id: str):
        """
        Callback interno registrado en el servicio P2P.
        Extrae los datos y los delega a dispatch_message.
        """
        try:
            msg_type = data.get("type")
            payload = data.get("payload")
            
            if msg_type:
                self.dispatch_message(msg_type, payload, peer_id)
        except Exception:
            logger.exception(f"Error en router interno de Gossip para {peer_id}")