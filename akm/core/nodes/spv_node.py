# akm/core/nodes/spv_node.py
import logging
from typing import Dict, Any, List, cast

from akm.core.nodes.base_node import BaseNode
from akm.core.models.header_chain import HeaderChain
from akm.core.models.block_header import BlockHeader
from akm.core.managers.gossip_manager import GossipManager
from akm.infra.network.p2p_service import P2PService
from akm.core.config.protocol_constants import ProtocolConstants
from akm.core.services.merkle_tree_builder import MerkleTreeBuilder

logging.basicConfig(level=logging.INFO, format='[SPV-Mobile] %(message)s')

class SPVNode(BaseNode):
    """
    [Cliente Ligero]
    Maneja HeaderChain en memoria y valida pagos usando Merkle Proofs.
    """

    def __init__(self, p2p_service: P2PService, gossip_manager: GossipManager):
        super().__init__(p2p_service, gossip_manager)
        self.header_chain = HeaderChain()
        
    def sync(self) -> None:
        """Inicia descarga de headers."""
        start_hash = ""
        if self.header_chain.tip:
            start_hash = self.header_chain.tip.hash
            
        msg: Dict[str, Any] = {
            "type": ProtocolConstants.MSG_GET_HEADERS,
            "payload": {"start_hash": start_hash, "limit": 500}
        }
        logging.info(f"🔄 [Sync] Solicitando headers...")
        self.p2p.broadcast(msg)

    def verify_payment(self, tx_hash: str) -> None:
        """Solicita a la red probar que una TX existe."""
        logging.info(f"🕵️ [SPV] Verificando pago: {tx_hash[:8]}...")
        msg: Dict[str, Any] = {
            "type": ProtocolConstants.MSG_GET_MERKLE_PROOF,
            "payload": {"tx_hash": tx_hash}
        }
        self.p2p.broadcast(msg)

    def _process_payload(self, msg_type: str, payload: Dict[str, Any], peer_id: str) -> None:
        if msg_type == ProtocolConstants.MSG_HEADERS:
            if isinstance(payload, list):
                self._handle_headers_received(cast(List[Dict[str, Any]], payload))
                
        elif msg_type == ProtocolConstants.MSG_MERKLE_PROOF:
            self._handle_proof_received(payload)
            
        elif msg_type == ProtocolConstants.MSG_BLOCK:
            logging.debug("Ignorando bloque completo (Soy SPV).")

    def _handle_headers_received(self, headers_data: List[Dict[str, Any]]) -> None:
        logging.info(f"📥 Recibidos {len(headers_data)} headers.")
        count = 0
        for h_dict in headers_data:
            try:
                header = BlockHeader(
                    index=int(h_dict['index']),
                    timestamp=int(h_dict['timestamp']),
                    previous_hash=str(h_dict.get('prev_hash') or h_dict.get('previous_hash')),
                    bits=str(h_dict['bits']),
                    merkle_root=str(h_dict['merkle_root']),
                    nonce=int(h_dict['nonce']),
                    block_hash=str(h_dict['hash'])
                )
                if self.header_chain.add_header(header):
                    count += 1
                else:
                    logging.error(f"❌ Header inválido #{header.index}.")
                    break
            except Exception as e:
                logging.error(f"Error parseando header: {e}")
                break

        if count > 0:
            logging.info(f"✅ Sincronizados {count} headers. Altura: {self.header_chain.height}")

    def _handle_proof_received(self, proof_data: Dict[str, Any]):
        """Valida matemáticamente la prueba de inclusión."""
        tx_hash = proof_data.get("tx_hash", "")
        block_hash = proof_data.get("block_hash", "")
        merkle_root = proof_data.get("merkle_root", "")
        proof = proof_data.get("proof", [])
        
        # 1. ¿Tengo ese bloque validado?
        # Usamos el método público del HeaderChain
        local_header = self.header_chain.get_header_by_hash(block_hash)
        
        if not local_header:
            logging.warning(f"⚠️ [SPV] Prueba recibida para bloque desconocido {block_hash[:8]}. (¿Necesitas sincronizar?)")
            return

        # 2. Verificar que la raíz coincida con mi cadena honesta
        if local_header.merkle_root != merkle_root:
            logging.error("❌ [SPV] ALERTA: Merkle Root de la prueba no coincide con Header local.")
            return

        # 3. Verificar Criptografía (Ruta de Merkle)
        if MerkleTreeBuilder.verify_proof(tx_hash, merkle_root, proof):
            logging.info(f"✅ [SPV] PAGO CONFIRMADO: {tx_hash[:8]} está matemáticamente probado en el bloque #{local_header.index}.")
        else:
            logging.error(f"❌ [SPV] PRUEBA FALLIDA: La TX no genera la raíz del bloque.")