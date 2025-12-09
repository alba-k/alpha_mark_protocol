# akm/core/nodes/full_node.py
import logging
from typing import Dict, Any

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

logging.basicConfig(level=logging.INFO, format='[FullNode] %(message)s')

class FullNode(BaseNode):
    """
    [LSP] Nodo Completo (Validating Node).
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
        # 1. Inicializar Red (Padre)
        super().__init__(p2p_service, gossip_manager)
        
        # 2. Inicializar Estado (Hijo)
        self.blockchain = blockchain
        self.utxo_set = utxo_set
        self.mempool = mempool
        self.consensus = consensus
        self.reorg_manager = reorg_manager
        
        # 3. Conectar P2P con Blockchain (Para que el handshake sepa la altura)
        # [VERIFICADO] - Conexión de método exitosa
        self.p2p.set_height_provider(lambda: self.blockchain.height)
        
        # 4. Restaurar Estado al nacer
        self._hydrate_and_check_genesis()

    def _hydrate_and_check_genesis(self):
        """Recupera el estado desde el disco (Cold Start)."""
        chain_height = len(self.blockchain)
        
        if chain_height > 0:
            logging.info(f"📚 Hidratando estado desde {chain_height} bloques...")
            self.utxo_set.clear()
            for block in self.blockchain.get_history_iterator():
                self.reorg_manager.apply_block_to_state(block)
        
        if chain_height == 0:
            logging.warning("⚠️ Blockchain vacía. Creando Génesis...")
            genesis = GenesisBlockFactory.create_genesis_block()
            if self.consensus.add_block(genesis):
                logging.info(f"🌍 GÉNESIS CREADO: {genesis.hash[:16]}")
        else:
            tip = self.blockchain.last_block
            if tip:
                logging.info(f"✅ Nodo Sincronizado. Altura: {tip.index}")

    def _process_payload(self, msg_type: str, payload: Dict[str, Any], peer_id: str):
        """
        Reacciona a mensajes validados que llegan de la red.
        Ahora incluye lógica de sincronización (IBD).
        """
        
        # --- 1. LÓGICA DE SINCRONIZACIÓN (IBD) ---
        if msg_type == ProtocolConstants.MSG_HANDSHAKE:
            # Al recibir saludo, comparamos alturas para determinar si pedimos sync
            peer_height = int(payload.get("height", 0))
            my_height = self.blockchain.height
            
            logging.info(f"📊 Estado Peer: {peer_height} | Mi Estado: {my_height}")
            
            if peer_height > my_height:
                logging.warning(f"📉 Detectado peer más avanzado ({peer_height} > {my_height}). Solicitando descarga...")
                sync_req:dict[str, Any] = {
                    "type": ProtocolConstants.MSG_SYNC_REQUEST,
                    "payload": {"start_index": my_height + 1}
                }
                # [VERIFICADO] Usamos el método send_message para unicast.
                self.p2p.send_message(peer_id, sync_req)

        elif msg_type == ProtocolConstants.MSG_SYNC_REQUEST:
            # Alguien nos pide bloques viejos (Servidor de historial)
            start_index = int(payload.get("start_index", 1))
            logging.info(f"📚 {peer_id} solicita sincronización desde #{start_index}")
            
            # [VERIFICADO] get_blocks_range es un método existente en Blockchain.
            blocks = self.blockchain.get_blocks_range(start_index, limit=500)
            
            if blocks:
                logging.info(f"📤 Enviando lote de {len(blocks)} bloques a {peer_id}...")
                batch_msg: dict[str, Any] = {
                    "type": ProtocolConstants.MSG_SYNC_BATCH,
                    "payload": {"blocks": [b.to_dict() for b in blocks]}
                }
                self.p2p.send_message(peer_id, batch_msg)

        elif msg_type == ProtocolConstants.MSG_SYNC_BATCH:
            # Recibimos el lote de bloques históricos
            raw_blocks = payload.get("blocks", [])
            logging.info(f"📥 Procesando lote de sincronización ({len(raw_blocks)} bloques)...")
            
            imported_count = 0
            for b_data in raw_blocks:
                try:
                    block = NodeMapper.reconstruct_block(b_data)
                    if self.consensus.add_block(block):
                        imported_count += 1
                except Exception as e:
                    logging.error(f"Error importando bloque histórico: {e}")
                    break
            
            logging.info(f"✅ Sincronización completada: +{imported_count} bloques añadidos.")

            # Si el lote no estaba lleno, significa que terminamos.
            # Si el lote estaba lleno (limit=500), pedimos el siguiente lote.
            if imported_count > 0 and imported_count == 500:
                 logging.warning("El lote estaba lleno. Solicitando siguiente lote...")
                 # Pedimos la continuación inmediatamente
                 next_sync_req: dict[str, Any] = {
                    "type": ProtocolConstants.MSG_SYNC_REQUEST,
                    "payload": {"start_index": self.blockchain.height + 1}
                 }
                 self.p2p.send_message(peer_id, next_sync_req)


        # --- 2. MENSAJES DE CONSENSO EN TIEMPO REAL (Gossip) ---
        elif msg_type == ProtocolConstants.MSG_BLOCK:
            logging.info(f"📨 [Consenso] Bloque recibido de {peer_id[:8]}...")
            try:
                block = NodeMapper.reconstruct_block(payload)
                if self.consensus.add_block(block):
                    logging.info(f"✅ Bloque #{block.index} ACEPTADO.")
                    self.gossip.propagate_block(block.to_dict(), origin_peer=peer_id)
                else:
                    logging.info("🗑️ Bloque rechazado.")
            except Exception as e:
                logging.error(f"Error procesando bloque: {e}")

        elif msg_type == ProtocolConstants.MSG_TX:
            logging.debug(f"📨 [Consenso] TX recibida de {peer_id[:8]}...")
            try:
                tx = NodeMapper.reconstruct_transaction(payload)
                if self.mempool.add_transaction(tx):
                    logging.info(f"✅ TX {tx.tx_hash[:8]} en Mempool.")
                    self.gossip.propagate_transaction(tx.to_dict(), origin_peer=peer_id)
            except Exception as e:
                logging.error(f"Error procesando TX: {e}")

        # --- 3. MENSAJES DE SERVICIO SPV ---
        elif msg_type == ProtocolConstants.MSG_GET_HEADERS:
            self.gossip.process_get_headers(payload, peer_id)

        elif msg_type == ProtocolConstants.MSG_GET_MERKLE_PROOF:
            self.gossip.process_get_proof(payload, peer_id)
    
    def submit_transaction(self, tx: Transaction) -> bool:
        if self.mempool.add_transaction(tx):
            logging.info(f"🚀 Transacción aceptada localmente: {tx.tx_hash[:8]}")
            self.gossip.propagate_transaction(tx.to_dict()) 
            return True
        logging.warning("TX rechazada por Mempool local.")
        return False
        
    def get_balance(self, address: str) -> int:
        return self.utxo_set.get_balance_for_address(address)