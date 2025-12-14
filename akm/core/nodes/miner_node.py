# akm/core/nodes/miner_node.py
import logging
import threading
import time
from typing import Optional, Dict, Any

# Herencia
from akm.core.nodes.full_node import FullNode

# Interfaces e Implementaciones
from akm.infra.network.p2p_service import P2PService 

# Configuración
from akm.core.config.mining_config import MiningConfig 
from akm.core.config.protocol_constants import ProtocolConstants

# Dependencias Managers
from akm.core.managers.mining_manager import MiningManager
from akm.core.managers.gossip_manager import GossipManager
from akm.core.models.blockchain import Blockchain
from akm.core.managers.utxo_set import UTXOSet
from akm.core.services.mempool import Mempool
from akm.core.managers.consensus_orchestrator import ConsensusOrchestrator
from akm.core.managers.chain_reorg_manager import ChainReorgManager

# Logging local
logger = logging.getLogger(__name__)

class MinerNode(FullNode):
    """
    [LSP] Nodo Minero.
    Extiende FullNode con capacidades de minería activa.
    """

    def __init__(
        self, 
        p2p_service: P2PService,  
        gossip_manager: GossipManager, 
        blockchain: Blockchain, 
        utxo_set: UTXOSet, 
        mempool: Mempool, 
        consensus: ConsensusOrchestrator, 
        reorg_manager: ChainReorgManager,
        mining_manager: MiningManager,
        mining_config: MiningConfig 
    ):
        # Inicializar el Padre (FullNode)
        super().__init__(
            p2p_service, gossip_manager, blockchain, utxo_set, mempool, consensus, reorg_manager
        )
        
        self.gossip: GossipManager = gossip_manager
        self.miner = mining_manager
        
        # Cargar configuración desde el objeto inyectado
        self._miner_address: Optional[str] = mining_config.default_miner_address
        
        self._mining_active = False
        
        # Evento para cancelar minería si llega un bloque externo
        self._interrupt_mining = threading.Event()

    # --- [NUEVO] MÉTODO START PARA AUTOMATIZAR EL ARRANQUE ---
    def start(self):
        """
        Sobreescribe el start() del padre.
        1. Arranca la red (P2P).
        2. Arranca la minería automáticamente.
        """
        # 1. Arrancar servicios de red (Lógica del padre - FullNode)
        super().start()
        
        # 2. Arrancar Minería Automática
        if self._miner_address:
            logger.info(f"🔨 Auto-iniciando minería para: {self._miner_address}")
            self.start_mining_loop()
        else:
            logger.warning("⚠️ Minero arrancado pero SIN dirección de billetera configurada. Modo pasivo (No mina).")
    # ---------------------------------------------------------

    def start_mining_loop(self, miner_address: Optional[str] = None):
        """Inicia el proceso de minería en un hilo separado."""
        # Prioridad: Argumento > Configuración inyectada
        address_to_use = miner_address if miner_address else self._miner_address
        
        if not address_to_use:
            logger.error("❌ No se puede iniciar minería: Falta dirección de pago (Wallet Address).")
            return

        self._miner_address = address_to_use
        self._mining_active = True
        self._interrupt_mining.clear()
        
        mining_thread = threading.Thread(target=self._mining_worker, daemon=True)
        mining_thread.start()
        logger.info(f"⛏️ Minería ACTIVA -> {self._miner_address[:10]}...")

    def stop_mining(self):
        self._mining_active = False
        self._interrupt_mining.set() # Forzar salida inmediata del loop de minería
        logger.info("🛑 Minería detenida.")

    def _process_payload(self, msg_type: str, payload: Dict[str, Any], peer_id: str):
        """
        Manejador Central de Mensajes.
        """
        # 1. Delegar mensajes de Sincronización/SPV al GossipManager
        if msg_type in [ProtocolConstants.MSG_GET_HEADERS, ProtocolConstants.MSG_GET_MERKLE_PROOF]:
            if hasattr(self.gossip, 'dispatch_message'):
                self.gossip.dispatch_message(msg_type, payload, peer_id)
            else:
                logger.error(f"GossipManager no tiene dispatch_message para {msg_type}")
            return

        # 2. Procesamiento normal del Nodo Completo (FullNode)
        super()._process_payload(msg_type, payload, peer_id)
        
        # 3. Lógica Reactiva del Minero
        if msg_type == ProtocolConstants.MSG_BLOCK:
            if self._mining_active:
                logger.info("⚡ [Miner] Bloque válido recibido. Reiniciando trabajo...")
                self._interrupt_mining.set()

    def mine_one_block(self, miner_address: Optional[str] = None) -> bool:
        """Intenta minar un solo bloque."""
        target_address = miner_address if miner_address else self._miner_address

        if not target_address:
            logger.error("Falta dirección de minero.")
            return False
        
        if not self._miner_address:
            self._miner_address = target_address

        self._interrupt_mining.clear()

        try:
            # Minar pasando el evento de interrupción
            new_block = self.miner.mine_block(target_address, interrupt_event=self._interrupt_mining)
            
            # Si es None, fuimos interrumpidos
            if new_block is None:
                return False

            # Intentar añadir al consenso local
            if self.consensus.add_block(new_block):
                logger.info(f"💎 ¡BLOQUE ENCONTRADO! Hash: {new_block.hash[:8]}")
                
                # Propagar el bloque a la red
                if hasattr(self.gossip, 'propagate_block'):
                    self.gossip.propagate_block(new_block.to_dict())
                return True
            else:
                logger.warning("Bloque propio rechazado por consenso interno (Stale o Inválido).")
                return False
                
        except Exception as e:
            logger.error(f"Error crítico en ciclo de minería: {e}")
            return False

    def _mining_worker(self):
        """Loop infinito (en hilo) que llama a mine_one_block repetidamente."""
        while self._mining_active:
            self.mine_one_block()
            # Pequeña pausa para no saturar CPU
            if self._mining_active:
                time.sleep(0.01)