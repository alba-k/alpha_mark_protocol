# akm/core/managers/gossip_manager.py
import logging
from typing import Dict, Any, Optional, TYPE_CHECKING

from akm.core.config.protocol_constants import ProtocolConstants
from akm.infra.network.p2p_service import P2PService
from akm.core.services.merkle_tree_builder import MerkleTreeBuilder

if TYPE_CHECKING:
    from akm.core.models.blockchain import Blockchain

logging.basicConfig(level=logging.INFO, format='[Gossip] %(message)s')

class GossipManager:
    """
    Gestor de Difusión. Enruta mensajes entre la Red P2P y la Blockchain.
    """

    def __init__(self, p2p_service: P2PService, blockchain: Optional['Blockchain'] = None):
        self.p2p = p2p_service
        self.blockchain: Optional['Blockchain'] = blockchain
        self.p2p.register_handler(self._handle_network_message)

    def set_blockchain(self, blockchain: 'Blockchain'):
        self.blockchain = blockchain

    def propagate_block(self, block_payload: Dict[str, Any], origin_peer: Optional[str] = None):
        msg: Dict[str, Any] = {"type": ProtocolConstants.MSG_BLOCK, "payload": block_payload}
        self.p2p.broadcast(msg, exclude_peer=origin_peer)

    def propagate_transaction(self, tx_payload: Dict[str, Any], origin_peer: Optional[str] = None):
        msg: Dict[str, Any] = {"type": ProtocolConstants.MSG_TX, "payload": tx_payload}
        self.p2p.broadcast(msg, exclude_peer=origin_peer)

    # --- MÉTODOS PÚBLICOS DE SERVICIO SPV (SOLUCIÓN ENCAPSULAMIENTO) ---

    def process_get_headers(self, payload: Any, peer_id: str):
        """[Server] Responde con headers ligeros."""
        if not self.blockchain: return

        locator_hash = payload.get("start_hash", "")
        limit = min(payload.get("limit", 2000), 2000)
        
        logging.info(f"📲 [SPV] Cliente {peer_id[:8]} pide headers desde {locator_hash[:8] or 'Genesis'}")
        
        headers = self.blockchain.get_headers(locator_hash, limit)
        
        if headers:
            response: Dict[str, Any] = {"type": ProtocolConstants.MSG_HEADERS, "payload": headers}
            self.p2p.broadcast(response)
            logging.info(f"📤 [SPV] Enviados {len(headers)} headers.")

    def process_get_proof(self, payload: Any, peer_id: str):
        """[Server] Genera prueba de Merkle para una TX."""
        if not self.blockchain: return
        
        tx_hash = payload.get("tx_hash")
        logging.info(f"🔎 [SPV] Buscando prueba para TX: {tx_hash[:8]}")
        
        target_block = None
        for block in self.blockchain.get_history_iterator(0): 
            for tx in block.transactions:
                if tx.tx_hash == tx_hash:
                    target_block = block
                    break
            if target_block: break
            
        if target_block:
            all_hashes = [tx.tx_hash for tx in target_block.transactions]
            proof = MerkleTreeBuilder.get_proof(all_hashes, tx_hash)
            
            if proof:
                response: Dict[str, Any] = {
                    "type": ProtocolConstants.MSG_MERKLE_PROOF,
                    "payload": {
                        "tx_hash": tx_hash,
                        "block_hash": target_block.hash,
                        "merkle_root": target_block.merkle_root,
                        "proof": proof
                    }
                }
                self.p2p.broadcast(response)
                logging.info(f"✅ [SPV] Prueba generada y enviada.")
        else:
            logging.warning("TX no encontrada para prueba Merkle.")

    # --- PRIVADO: Enrutador Interno ---
    def _handle_network_message(self, data: Dict[str, Any], peer_id: str):
        msg_type = data.get("type")
        payload = data.get("payload")

        # Ahora usamos los métodos públicos también internamente
        if msg_type == ProtocolConstants.MSG_GET_HEADERS:
            self.process_get_headers(payload, peer_id)
            
        elif msg_type == ProtocolConstants.MSG_GET_MERKLE_PROOF:
            self.process_get_proof(payload, peer_id)