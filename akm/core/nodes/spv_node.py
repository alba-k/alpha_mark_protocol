# akm/core/nodes/spv_node.py

import logging
import time
from typing import Dict, Any, List, cast, Set

# Importaciones de configuración e infraestructura
from akm.core.nodes.base_node import BaseNode
from akm.infra.network.p2p_service import P2PService
from akm.core.managers.gossip_manager import GossipManager

# Modelos y Lógica
from akm.core.models.header_chain import HeaderChain
from akm.core.models.block_header import BlockHeader
from akm.core.models.transaction import Transaction
from akm.core.config.protocol_constants import ProtocolConstants
from akm.core.utils.monetary import Monetary

logger = logging.getLogger(__name__)

class SPVNode(BaseNode):
    """
    [Cliente Ligero - Billetera]
    Mantiene solo los headers y los UTXOs propios del usuario.
    """

    class MemoryUTXOAdapter:
        """
        Adaptador interno para que el WalletManager pueda consumir
        los UTXOs que tenemos en memoria (cache) como si fuera una base de datos.
        """
        def __init__(self, utxo_list: List[Dict[str, Any]]):
            self.utxos = utxo_list

        def get_utxos_for_address(self, address: str) -> List[Dict[str, Any]]:
            # En SPV solo tenemos nuestros propios UTXOs, devolvemos todo lo filtrado previamente.
            return self.utxos
        
        def get_balance_for_address(self, address: str) -> int:
            # Suma robusta manejando posibles claves
            return sum(int(u.get('amount') or u.get('value_alba', 0)) for u in self.utxos)

    def __init__(self, p2p_service: P2PService, gossip_manager: GossipManager):
        
        # 1. Inicializar Padre (BaseNode) con los servicios inyectados
        super().__init__(
            network_service=p2p_service, 
            gossip_manager=gossip_manager
        )
        
        self.p2p = p2p_service 

        # 2. Componentes exclusivos del SPV
        self.header_chain = HeaderChain()
        
        # Estado Volátil (Caché de Billetera)
        self.wallet_cache: Dict[str, Any] = {
            "address": None,
            "utxos": [],
            "balance_alba": 0,
            "last_update": 0.0
        }
        
        # Logs de inicio
        if hasattr(self.p2p, 'config'):
            host = self.p2p.config.host
            port = self.p2p.config.port
            logger.info(f"📱 NODO SPV (BILLETERA) INICIALIZADO | Listen: {host}:{port}")

    def request_balance_update(self, address: str) -> None:
        logger.info(f"📡 Solicitando actualización de saldo para: {address[:8]}...")
        msg: Dict[str, Any] = {
            "type": ProtocolConstants.MSG_GET_UTXOS,
            "payload": {"address": address}
        }
        self.p2p.broadcast(msg)

    def get_memory_utxo_set(self) -> Any:
        return self.MemoryUTXOAdapter(self.wallet_cache["utxos"])

    def get_cached_balance(self) -> float:
        return float(Monetary.to_akm(self.wallet_cache["balance_alba"]))
    
    def get_cached_utxo_count(self) -> int:
        return len(self.wallet_cache["utxos"])

    def broadcast_transaction(self, tx: Transaction) -> bool:
        logger.info(f"🚀 [SPV] Transmitiendo transacción firmada: {tx.tx_hash[:8]}")
        msg: Dict[str, Any] = {
            "type": ProtocolConstants.MSG_TX,
            "payload": tx.to_dict()
        }
        self.p2p.broadcast(msg)
        self._remove_spent_utxos_from_cache(tx)
        return True

    def _remove_spent_utxos_from_cache(self, tx: Transaction) -> None:
        try:
            current_utxos = self.wallet_cache["utxos"]
            if not current_utxos: return

            spent_ids: Set[str] = set()
            for inp in tx.inputs:
                spent_id = f"{inp.previous_tx_hash}:{inp.output_index}"
                spent_ids.add(spent_id)

            remaining_utxos: List[Dict[str, Any]] = []
            for u in current_utxos:
                # Normalización de claves para evitar errores
                u_tx_hash = u.get('tx_hash') or u.get('hash')
                u_index = u.get('index') if 'index' in u else u.get('output_index')
                
                u_id = f"{u_tx_hash}:{u_index}"
                if u_id not in spent_ids:
                    remaining_utxos.append(u)
            
            new_balance = sum(int(u.get('amount') or u.get('value_alba', 0)) for u in remaining_utxos)
            self.wallet_cache["utxos"] = remaining_utxos
            self.wallet_cache["balance_alba"] = new_balance
            logger.info(f"📉 [WALLET] Saldo actualizado localmente. Nuevo Saldo: {Monetary.to_akm(new_balance)}")

        except Exception as e:
            logger.error(f"Error actualizando caché local tras gasto: {e}")

    def _process_payload(self, msg_type: str, payload: Dict[str, Any], peer_id: str) -> None:
        if msg_type == ProtocolConstants.MSG_UTXO_SET:
            addr = str(payload.get("address", ""))
            utxos = cast(List[Dict[str, Any]], payload.get("utxos", []))
            
            # Cálculo de balance usando 'amount' (estándar de red)
            total_alba = sum(int(u.get('amount', 0)) for u in utxos)
            
            self.wallet_cache = {
                "address": addr,
                "utxos": utxos,
                "balance_alba": total_alba,
                "last_update": time.time()
            }
            logger.info(f"💰 Balance Recibido: {Monetary.to_akm(total_alba)} AKM ({len(utxos)} UTXOs)")

        elif msg_type == ProtocolConstants.MSG_HANDSHAKE:
            peer_height = int(payload.get("height", 0))
            if peer_height > self.header_chain.height:
                self.sync_headers()

        elif msg_type == ProtocolConstants.MSG_HEADERS:
            raw_headers: List[Dict[str, Any]] = payload if isinstance(payload, list) else []
            self._handle_headers(raw_headers)
            
        elif msg_type == ProtocolConstants.MSG_MERKLE_PROOF:
            self._handle_proof(payload)

    def sync_headers(self) -> None:
        start_hash = self.header_chain.tip.hash if self.header_chain.tip else ""
        self.p2p.broadcast({
            "type": ProtocolConstants.MSG_GET_HEADERS, 
            "payload": {"start_hash": start_hash, "limit": 500}
        })

    def _handle_headers(self, raw_headers: List[Dict[str, Any]]) -> None:
        count = 0
        for h in raw_headers:
            try:
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
                else: break
            except Exception: break
        if count > 0:
            logger.info(f"✅ Headers sincronizados: +{count} (Altura: {self.header_chain.height})")

    def _handle_proof(self, data: Dict[str, Any]) -> None:
        # Lógica simplificada de validación Merkle
        pass