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

# 🛡️ IMPORTACIONES AÑADIDAS PARA SEGURIDAD
from akm.core.validators.transaction_rules_validator import TransactionRulesValidator
# ------------------------------------------

logger = logging.getLogger(__name__)

class FullNode(BaseNode):
    """
    Nodo Completo (Full Node).
    Responsabilidades:
    1. Mantener la Blockchain completa y el UTXO Set.
    2. Validar autónomamente cada bloque y transacción.
    3. Servir datos a nodos SPV (Wallet Server).
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
        super().__init__(p2p_service, gossip_manager)
        
        self.blockchain = blockchain
        self.utxo_set = utxo_set
        self.mempool = mempool
        self.consensus = consensus
        self.reorg_manager = reorg_manager
        
        # Inyectamos el proveedor de altura al servicio P2P para el Handshake
        if hasattr(p2p_service, 'set_height_provider'):
            p2p_service.set_height_provider(lambda: self.blockchain.height)
        
        # Inicialización del Estado
        self._hydrate_and_check_genesis()
        logger.info("🟢 FullNode inicializado y listo para la red.")

    def _hydrate_and_check_genesis(self) -> None:
        """
        Carga inicial del estado (Hidratación) y creación de Génesis si es necesario.
        """
        chain_height = len(self.blockchain)
        
        if chain_height > 0:
            logger.info(f"📚 Hidratando UTXO Set desde {chain_height} bloques existentes...")
            self.utxo_set.clear()
            for block in self.blockchain.get_history_iterator():
                # Aplicamos cada bloque para reconstruir el saldo de todos
                self.reorg_manager.apply_block_to_state(block)
        else:
            logger.warning("⚠️ Blockchain vacía. Creando Génesis...")
            genesis = GenesisBlockFactory.create_genesis_block()
            if self.consensus.add_block(genesis):
                logger.info(f"🌍 GÉNESIS CREADO: {genesis.hash[:16]}...")
        
        if self.blockchain.last_block:
             logger.info(f"✅ Nodo Sincronizado. Altura actual: {self.blockchain.last_block.index}")

    def _process_payload(self, msg_type: str, payload: Dict[str, Any], peer_id: str) -> None:
        """
        Lógica central de procesamiento de mensajes entrantes del P2P.
        """
        
        # --- 1. SOPORTE A NODOS LIGEROS (Wallet Server) ---
        if msg_type == ProtocolConstants.MSG_GET_UTXOS:
            address_query = str(payload.get("address", ""))
            if address_query:
                logger.debug(f"🔍 [SPV Service] Consultando fondos para: {address_query[:8]}... (Peer: {peer_id[:8]})")
                utxos_found = self.utxo_set.get_utxos_for_address(address_query)
                
                response: Dict[str, Any] = {
                    "type": ProtocolConstants.MSG_UTXO_SET,
                    "payload": {"address": address_query, "utxos": utxos_found}
                }
                self._network.send_message(peer_id, response)

        # --- 2. SINCRONIZACIÓN DE BLOQUES (IBD) ---
        elif msg_type == ProtocolConstants.MSG_HANDSHAKE:
            peer_height = int(payload.get("height", 0))
            if peer_height > self.blockchain.height:
                logger.info(f"📉 Peer avanzado al conectar ({peer_height} vs {self.blockchain.height}). Solicitando Sync...")
                self._trigger_sync(peer_id)

        elif msg_type == ProtocolConstants.MSG_SYNC_REQUEST:
            start_index = int(payload.get("start_index", 1))
            logger.debug(f"📡 Recibida solicitud de bloques desde index {start_index}.")
            blocks = self.blockchain.get_blocks_range(start_index, limit=500)
            if blocks:
                self._network.send_message(peer_id, {
                    "type": ProtocolConstants.MSG_SYNC_BATCH,
                    "payload": {"blocks": [b.to_dict() for b in blocks]}
                })

        elif msg_type == ProtocolConstants.MSG_SYNC_BATCH:
            raw_blocks = payload.get("blocks", [])
            logger.info(f"📥 Importando lote de {len(raw_blocks)} bloques. Altura local: {self.blockchain.height}")
            imported = 0
            
            for b_data in raw_blocks:
                try:
                    block = NodeMapper.reconstruct_block(b_data)
                    if self.consensus.add_block(block): 
                        imported += 1
                except Exception as e: 
                    logger.warning(f"Error o interrupción al importar el bloque: {e}")
                    break
            
            logger.info(f"✅ Lote importado. {imported} bloques añadidos. Nueva Altura: {self.blockchain.height}")
            
            if imported >= 500:
                self._trigger_sync(peer_id)

        # --- 3. GOSSIP (Tiempo Real: Bloques) ---
        elif msg_type == ProtocolConstants.MSG_BLOCK:
            try:
                block = NodeMapper.reconstruct_block(payload)
                current_height = self.blockchain.height
                
                if block.index > current_height + 1:
                    logger.warning(f"🐢 GAP DETECTADO: Local={current_height}, Recibido={block.index}. Iniciando recuperación...")
                    self._trigger_sync(peer_id)
                    return 
                
                if self.consensus.add_block(block):
                    logger.info(f"📢 Nuevo Bloque #{block.index} aceptado y propagado.")
                    self._gossip.propagate_block(block.to_dict(), origin_peer=peer_id)
                else:
                    if block.index > 0 and not self.blockchain.get_block_by_hash(block.previous_hash):
                        logger.info(f"🔗 Huérfano detectado (Padre desconocido: {block.previous_hash[:8]}...). Solicitando contexto a {peer_id[:8]}...")
                        self._trigger_sync(peer_id, offset_back=5)
                    else:
                        logger.debug(f"Bloque {block.index} rechazado por consenso (ej. duplicado/inválido).")

            except Exception as e:
                logger.error(f"❌ Error procesando bloque entrante: {e}", exc_info=True)

        # 🚀 [CAMBIO CRÍTICO DE SEGURIDAD] - MANEJO SEGURO DE TRANSACCIONES
        elif msg_type == ProtocolConstants.MSG_TX:
            try:
                tx = NodeMapper.reconstruct_transaction(payload)
                
                # [🛡️] 1. INICIALIZAR VALIDADOR DE REGLAS (Utiliza el UTXOSet para chequear fondos y existencia de UTXOs)
                rules_validator = TransactionRulesValidator(self.utxo_set)
                
                # [🛡️] 2. VALIDACIÓN ESTRICTA (Chequea UTXOs, Balance y Firmas)
                if not rules_validator.validate(tx):
                    # El validador ya logueó la razón del rechazo (ej. "Fondos insuficientes")
                    logger.warning(f"⛔ TX Rechazada (Reglas/Firma Inválida): {tx.tx_hash[:8]}")
                    return

                # 3. Si pasa la validación, la TX entra al Mempool
                if self.mempool.add_transaction(tx):
                    logger.info(f"🤑 Nueva TX VÁLIDA en Mempool: {tx.tx_hash[:8]}... aceptada y propagada.")
                    self._gossip.propagate_transaction(tx.to_dict(), origin_peer=peer_id)
                else:
                    logger.debug(f"TX {tx.tx_hash[:8]} ya existe o Mempool lleno.")

            except Exception as e:
                logger.error(f"❌ Error procesando TX entrante: {e}", exc_info=True)

        # --- 4. Delegación SPV (Proofs & Headers) ---
        elif msg_type == ProtocolConstants.MSG_GET_HEADERS:
            logger.debug(f"Delegando petición GET_HEADERS a GossipManager.")
            self._gossip.process_get_headers(payload, peer_id)
            
        elif msg_type == ProtocolConstants.MSG_GET_MERKLE_PROOF:
            logger.debug(f"Delegando petición GET_MERKLE_PROOF a GossipManager.")
            self._gossip.process_get_proof(payload, peer_id)

    # --- Métodos Auxiliares Privados ---

    def _trigger_sync(self, peer_id: str, offset_back: int = 0) -> None:
        start = max(1, self.blockchain.height + 1 - offset_back)
        logger.info(f"⬇️  Solicitando bloques a {peer_id[:8]}... a partir del index {start}.")
        self._network.send_message(peer_id, {
            "type": ProtocolConstants.MSG_SYNC_REQUEST,
            "payload": {"start_index": start}
        })

    # --- Métodos Públicos (Usados por MinerNode o Scripts) ---

    def submit_transaction(self, tx: Transaction) -> bool:
        """
        Permite inyectar una transacción localmente (ej. desde el Minero o CLI).
        """
        # Debe usar el mismo chequeo que la red:
        rules_validator = TransactionRulesValidator(self.utxo_set)
        if not rules_validator.validate(tx):
             logger.warning(f"⚠️ Fallo al enviar TX propia: {tx.tx_hash[:8]}... rechazada por validación interna.")
             return False
             
        if self.mempool.add_transaction(tx):
            logger.info(f"🚀 TX Propia aceptada y difundida: {tx.tx_hash[:8]}...")
            self._gossip.propagate_transaction(tx.to_dict()) 
            return True
        logger.warning(f"⚠️ Fallo al enviar TX propia: {tx.tx_hash[:8]}... rechazada por Mempool.")
        return False

    def get_balance(self, address: str) -> int:
        """Consulta el saldo confirmado en el UTXO Set."""
        return self.utxo_set.get_balance_for_address(address)