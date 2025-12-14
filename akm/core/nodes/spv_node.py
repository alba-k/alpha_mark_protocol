# akm/core/nodes/spv_node.py
import logging
import time
from typing import Dict, Any, List, cast

from akm.core.nodes.base_node import BaseNode
from akm.core.models.header_chain import HeaderChain
from akm.core.models.block_header import BlockHeader
from akm.core.models.transaction import Transaction
from akm.core.managers.gossip_manager import GossipManager
from akm.infra.network.p2p_service import P2PService
from akm.core.config.protocol_constants import ProtocolConstants
from akm.core.services.merkle_tree_builder import MerkleTreeBuilder
from akm.core.utils.monetary import Monetary

logger = logging.getLogger(__name__)

class SPVNode(BaseNode):
    """
    [Cliente Ligero - Billetera]
    No tiene Base de Datos. Usa memoria volátil.
    Pide UTXOs a Full Nodes para construir transacciones.
    """

    class MemoryUTXOAdapter:
        """
        Adapter que cumple con la interfaz implícita de UTXOSet.
        """
        def __init__(self, utxo_list: List[Dict[str, Any]]):
            self.utxos = utxo_list

        def get_utxos_for_address(self, address: str) -> List[Dict[str, Any]]:
            return self.utxos
        
        def get_balance_for_address(self, address: str) -> int:
            return sum(int(u.get('amount', 0)) for u in self.utxos)

    def __init__(self, p2p_service: P2PService, gossip_manager: GossipManager):
        super().__init__(p2p_service, gossip_manager)
        
        # [TIPADO] Definición explícita para habilitar .broadcast()
        self.p2p: P2PService = p2p_service

        self.header_chain = HeaderChain()
        
        # ESTADO VOLÁTIL (Caché de Billetera)
        self.wallet_cache: Dict[str, Any] = {
            "address": None,
            "utxos": [],
            "balance_alba": 0,
            "last_update": 0.0
        }

    def request_balance_update(self, address: str) -> None:
        """
        Lanza una petición a la red: '¿Alguien tiene los UTXOs de esta dirección?'
        """
        logger.info(f"📡 Solicitando actualización de saldo para: {address[:8]}...")
        msg: Dict[str, Any] = {
            "type": ProtocolConstants.MSG_GET_UTXOS,
            "payload": {"address": address}
        }
        self.p2p.broadcast(msg)

    def get_memory_utxo_set(self) -> Any:
        return self.MemoryUTXOAdapter(self.wallet_cache["utxos"])

    def get_cached_balance(self) -> float:
        """Retorna el saldo en caché formateado como AKM (float)."""
        return float(Monetary.to_akm(self.wallet_cache["balance_alba"]))
    
    def get_cached_utxo_count(self) -> int:
        return len(self.wallet_cache["utxos"])

    def broadcast_transaction(self, tx: Transaction) -> bool:
        """
        El SPV no valida completamente ni tiene mempool.
        Solo firma y propaga la TX cruda a la red.
        """
        logger.info(f"🚀 [SPV] Transmitiendo transacción firmada: {tx.tx_hash[:8]}")
        msg: Dict[str, Any] = {
            "type": ProtocolConstants.MSG_TX,
            "payload": tx.to_dict()
        }
        self.p2p.broadcast(msg)
        return True

    def _process_payload(self, msg_type: str, payload: Dict[str, Any], peer_id: str) -> None:
        """Manejo de mensajes del Nodo Ligero."""
        
        # 1. RESPUESTA DE LA RED: DATOS DE BILLETERA
        if msg_type == ProtocolConstants.MSG_UTXO_SET:
            addr = str(payload.get("address", ""))
            utxos = cast(List[Dict[str, Any]], payload.get("utxos", []))
            
            # Cálculo seguro del balance
            total_alba = sum(int(u.get('amount', 0)) for u in utxos)
            
            # Actualizamos caché
            self.wallet_cache = {
                "address": addr,
                "utxos": utxos,
                "balance_alba": total_alba,
                "last_update": time.time()
            }
            
            logger.info(f"💰 Balance Recibido: {Monetary.to_akm(total_alba)} AKM ({len(utxos)} UTXOs)")

        # 2. SINCRONIZACIÓN DE CABECERAS (HEADERS)
        elif msg_type == ProtocolConstants.MSG_HANDSHAKE:
            peer_height = int(payload.get("height", 0))
            if peer_height > self.header_chain.height:
                self.sync_headers()

        elif msg_type == ProtocolConstants.MSG_HEADERS:
            raw_headers: list[Dict[str, Any]]= payload if isinstance(payload, list) else []
            self._handle_headers(raw_headers)
            
        elif msg_type == ProtocolConstants.MSG_MERKLE_PROOF:
            self._handle_proof(payload)
            
        elif msg_type == ProtocolConstants.MSG_BLOCK:
            # Ignoramos bloques completos para ahorrar datos
            pass

    # --- Métodos Privados de Ayuda ---

    def sync_headers(self) -> None:
        start_hash = self.header_chain.tip.hash if self.header_chain.tip else ""
        self.p2p.broadcast({
            "type": ProtocolConstants.MSG_GET_HEADERS, 
            "payload": {"start_hash": start_hash, "limit": 500}
        })

    def _handle_headers(self, raw_headers: List[Dict[str, Any]]) -> None:
        """Procesa una lista de headers con instanciación tipada y segura."""
        count = 0
        for h in raw_headers:
            try:
                # INSTANCIACIÓN SEGURA Y TIPADA
                header = BlockHeader(
                    index=int(h.get('index', 0)),
                    timestamp=int(h.get('timestamp', 0)),
                    previous_hash=str(h.get('previous_hash') or h.get('prev_hash', '')),
                    bits=str(h.get('bits', '')),
                    merkle_root=str(h.get('merkle_root', '')),
                    nonce=int(h.get('nonce', 0)),
                    block_hash=str(h.get('hash', ''))
                )
                
                if self.header_chain.add_header(header):
                    count += 1
                else:
                    break
            except Exception as e:
                logger.error(f"Error procesando header: {e}")
                break
                
        if count > 0:
            logger.info(f"✅ Headers sincronizados: +{count} (Altura: {self.header_chain.height})")

    def _handle_proof(self, data: Dict[str, Any]) -> None:
        """Verificación Merkle."""
        tx_hash = str(data.get("tx_hash", ""))
        block_hash = str(data.get("block_hash", ""))
        merkle_root = str(data.get("merkle_root", ""))
        proof = cast(List[str], data.get("proof", []))
        
        local_header = self.header_chain.get_header_by_hash(block_hash)
        
        if not local_header:
            logger.warning(f"⚠️ Header desconocido para prueba Merkle: {block_hash[:8]}")
            return

        if local_header.merkle_root != merkle_root:
            logger.error("❌ Raíz Merkle no coincide con header local.")
            return

        if MerkleTreeBuilder.verify_proof(tx_hash, merkle_root, proof):
            logger.info(f"✅ PAGO VERIFICADO: {tx_hash[:8]} en bloque #{local_header.index}")
        else:
            logger.error(f"❌ Prueba Merkle fallida para {tx_hash[:8]}")