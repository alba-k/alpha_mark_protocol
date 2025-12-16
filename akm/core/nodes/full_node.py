# akm/core/nodes/full_node.py

import logging
from typing import Dict, Any, cast, List

# Herencia y Utilería
from akm.core.nodes.base_node import BaseNode
from akm.core.utils.node_mapper import NodeMapper

# Infraestructura e Interfaces
from akm.infra.network.p2p_service import P2PService 
from akm.core.managers.gossip_manager import GossipManager
from akm.core.config.protocol_constants import ProtocolConstants

# Core Managers y Modelos
from akm.core.models.blockchain import Blockchain
from akm.core.models.transaction import Transaction 
from akm.core.managers.utxo_set import UTXOSet
from akm.core.services.mempool import Mempool
from akm.core.managers.consensus_orchestrator import ConsensusOrchestrator
from akm.core.managers.chain_reorg_manager import ChainReorgManager
from akm.core.factories.genesis_block_factory import GenesisBlockFactory

# Validadores
from akm.core.validators.transaction_rules_validator import TransactionRulesValidator

logger = logging.getLogger(__name__)

class FullNode(BaseNode):
    """
    Nodo Completo (Full Node).
    Mantiene la Blockchain, valida transacciones y evita el doble gasto.
    """

    def __init__(
        self, 
        p2p_service: P2PService, 
        gossip_manager: GossipManager,
        blockchain: Blockchain,
        utxo_set: UTXOSet,
        mempool: Mempool,
        consensus: ConsensusOrchestrator,
        reorg_manager: ChainReorgManager
    ):
        super().__init__(network_service=p2p_service, gossip_manager=gossip_manager)
        
        self.p2p_service: P2PService = p2p_service
        self.blockchain = blockchain
        self.utxo_set = utxo_set
        self.mempool = mempool
        self.consensus = consensus
        self.reorg_manager = reorg_manager
        
        self.p2p_service.set_height_provider(lambda: self.blockchain.height)
        
        self._hydrate_and_check_genesis()
        logger.info("🟢 FullNode inicializado y listo para la red.")

    def _hydrate_and_check_genesis(self) -> None:
        chain_height = len(self.blockchain)
        
        if chain_height > 0:
            logger.info(f"📚 Hidratando UTXO Set desde {chain_height} bloques...")
            self.utxo_set.clear()
            for block in self.blockchain.get_history_iterator():
                self.reorg_manager.apply_block_to_state(block)
        else:
            logger.warning("⚠️ Blockchain vacía. Creando Génesis...")
            genesis = GenesisBlockFactory.create_genesis_block()
            if self.consensus.add_block(genesis):
                logger.info(f"🌍 GÉNESIS CREADO: {genesis.hash[:16]}...")
        
        if self.blockchain.last_block:
             logger.info(f"✅ Nodo Sincronizado. Altura actual: {self.blockchain.last_block.index}")

    def _process_payload(self, msg_type: str, payload: Dict[str, Any], peer_id: str) -> None:
        
        if msg_type == ProtocolConstants.MSG_GET_UTXOS:
            address_query = str(payload.get("address", ""))
            if address_query:
                utxos_found = self.utxo_set.get_utxos_for_address(address_query)
                self._network.send_message(peer_id, {
                    "type": ProtocolConstants.MSG_UTXO_SET,
                    "payload": {"address": address_query, "utxos": utxos_found}
                })

        elif msg_type == ProtocolConstants.MSG_HANDSHAKE:
            peer_height = int(payload.get("height", 0))
            if peer_height > self.blockchain.height:
                logger.info(f"📉 Peer avanzado ({peer_height}). Solicitando Sync...")
                self._trigger_sync(peer_id)

        elif msg_type == ProtocolConstants.MSG_SYNC_REQUEST:
            start_index = int(payload.get("start_index", 1))
            blocks = self.blockchain.get_blocks_range(start_index, limit=500)
            if blocks:
                self._network.send_message(peer_id, {
                    "type": ProtocolConstants.MSG_SYNC_BATCH,
                    "payload": {"blocks": [b.to_dict() for b in blocks]}
                })

        elif msg_type == ProtocolConstants.MSG_SYNC_BATCH:
            # [FIX TYPE] Cast explícito para que el linter sepa que es una lista de dicts
            raw_blocks = cast(List[Dict[str, Any]], payload.get("blocks", []))
            
            if not raw_blocks: return

            # [FIX LOGIC] Ahora 'x' se reconoce correctamente como Dict[str, Any]
            raw_blocks.sort(key=lambda x: int(x.get('index', 0)))

            logger.info(f"📥 Procesando lote de {len(raw_blocks)} bloques...")
            imported = 0
            
            for b_data in raw_blocks:
                try:
                    block = NodeMapper.reconstruct_block(b_data)
                    if self.consensus.add_block(block): 
                        imported += 1
                    else:
                        if block.index > self.blockchain.height + 1:
                            pass
                except Exception as e: 
                    logger.error(f"Error importando bloque de lote: {e}")
                    break
            
            logger.info(f"✅ Lote finalizado. +{imported} bloques. Altura: {self.blockchain.height}")
            
            if imported >= 1 and len(raw_blocks) >= 500:
                self._trigger_sync(peer_id)

        elif msg_type == ProtocolConstants.MSG_BLOCK:
            try:
                block = NodeMapper.reconstruct_block(payload)
                if self.consensus.add_block(block):
                    logger.info(f"📢 Bloque #{block.index} aceptado y propagado.")
                    self._gossip.propagate_block(block.to_dict(), origin_peer=peer_id)
                else:
                    if block.index > self.blockchain.height + 1:
                        logger.info(f"🔗 Bloque futuro detectado. Sync rápido con {peer_id[:8]}...")
                        self._trigger_sync(peer_id, offset_back=5)
            except Exception as e:
                logger.error(f"Error procesando bloque Gossip: {e}")

        elif msg_type == ProtocolConstants.MSG_TX:
            try:
                tx = NodeMapper.reconstruct_transaction(payload)
                rules_validator = TransactionRulesValidator(self.utxo_set)
                
                if rules_validator.validate(tx):
                    if self.mempool.add_transaction(tx):
                        logger.info(f"🤑 TX {tx.tx_hash[:8]} válida en Mempool. Propagando.")
                        self._gossip.propagate_transaction(tx.to_dict(), origin_peer=peer_id)
            except Exception:
                pass

        elif msg_type in [ProtocolConstants.MSG_GET_HEADERS, ProtocolConstants.MSG_GET_MERKLE_PROOF]:
            if msg_type == ProtocolConstants.MSG_GET_HEADERS:
                self._gossip.process_get_headers(payload, peer_id)
            else:
                self._gossip.process_get_proof(payload, peer_id)

    def _trigger_sync(self, peer_id: str, offset_back: int = 0) -> None:
        start = max(1, self.blockchain.height + 1 - offset_back)
        self._network.send_message(peer_id, {
            "type": ProtocolConstants.MSG_SYNC_REQUEST,
            "payload": {"start_index": start}
        })

    def submit_transaction(self, tx: Transaction) -> bool:
        rules_validator = TransactionRulesValidator(self.utxo_set)
        if not rules_validator.validate(tx):
             logger.warning(f"⚠️ TX Propia rechazada: {tx.tx_hash[:8]}")
             return False
        if self.mempool.add_transaction(tx):
            logger.info(f"🚀 TX Propia enviada: {tx.tx_hash[:8]}")
            self._gossip.propagate_transaction(tx.to_dict()) 
            return True
        return False

    def get_balance(self, address: str) -> int:
        return self.utxo_set.get_balance_for_address(address)