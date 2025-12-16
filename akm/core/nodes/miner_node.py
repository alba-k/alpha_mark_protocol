# akm/core/nodes/miner_node.py

import logging
import threading
import time
from typing import Optional, Dict, Any

# Herencia
from akm.core.nodes.full_node import FullNode

# Configuración y Constantes
from akm.core.config.mining_config import MiningConfig 
from akm.core.config.protocol_constants import ProtocolConstants

# Interfaces y Managers
from akm.infra.network.p2p_service import P2PService 
from akm.core.managers.mining_manager import MiningManager
from akm.core.managers.gossip_manager import GossipManager
from akm.core.models.blockchain import Blockchain
from akm.core.managers.utxo_set import UTXOSet
from akm.core.services.mempool import Mempool
from akm.core.managers.consensus_orchestrator import ConsensusOrchestrator
from akm.core.managers.chain_reorg_manager import ChainReorgManager

logger = logging.getLogger(__name__)

class MinerNode(FullNode):
    """
    Nodo Minero.
    Hereda de FullNode, por lo que ya sabe validar y sincronizar.
    Solo agrega la capacidad de crear bloques (Proof of Work).
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
        # 1. Inicializar al Padre (FullNode -> BaseNode)
        super().__init__(
            p2p_service, gossip_manager, blockchain, utxo_set, mempool, consensus, reorg_manager
        )
        
        # [FIX TIPO] Explicitamos que self._gossip es del tipo GossipManager
        self._gossip: GossipManager = gossip_manager
        
        # 2. Configuración específica de Minería
        self.miner = mining_manager
        self._miner_address: Optional[str] = mining_config.default_miner_address
        self._mining_active = False
        
        # Evento para detener el minado actual si alguien más gana
        self._interrupt_mining = threading.Event()

    def start(self):
        """Arranca la red (Padre) y luego el Minero."""
        super().start() 
        
        if self._miner_address:
            logger.info(f"🔨 Auto-iniciando minería hacia: {self._miner_address}")
            self._start_mining_thread()
        else:
            logger.warning("⚠️ Minero activo pero SIN dirección de pago configurada.")

    # --- [NUEVO] Métodos requeridos por la API (dependencies.py) ---
    
    def stop_mining(self):
        """
        Detiene el proceso de minería.
        Usado por la API cuando se cambia de identidad o se apaga el nodo.
        """
        if self._mining_active:
            self._mining_active = False
            self._interrupt_mining.set()
            logger.info("🛑 Minería detenida manualmente.")

    def start_mining_loop(self, address: str):
        """
        Inicia (o reinicia) el proceso de minería con una dirección específica.
        Usado por la API cuando el usuario hace Login.
        """
        self._miner_address = address
        
        if not self._mining_active:
            logger.info(f"⛏️ Iniciando motor de minería para: {address}")
            self._start_mining_thread()
        else:
            logger.info(f"⛏️ Dirección de minería actualizada en caliente: {address}")

    # ---------------------------------------------------------------

    def _start_mining_thread(self):
        self._mining_active = True
        self._interrupt_mining.clear()
        threading.Thread(target=self._mining_loop, daemon=True).start()
        logger.info(f"⛏️  Motor de Minería: ENCENDIDO")

    def _process_payload(self, msg_type: str, payload: Dict[str, Any], peer_id: str):
        """
        Intercepta mensajes. Si llega un BLOQUE válido de la red,
        interrumpe el trabajo actual.
        """
        # 1. Dejar que el FullNode procese el mensaje
        super()._process_payload(msg_type, payload, peer_id)
        
        # 2. Reacción del Minero
        if msg_type == ProtocolConstants.MSG_BLOCK:
            # Si llegó un bloque, paramos de minar el actual
            if self._mining_active:
                self._interrupt_mining.set() 

    def _mining_loop(self):
        """Bucle infinito de intento de minado."""
        while self._mining_active:
            self._interrupt_mining.clear()
            
            if not self._miner_address:
                time.sleep(1)
                continue

            try:
                # Intentar minar un bloque
                new_block = self.miner.mine_block(
                    self._miner_address, 
                    interrupt_event=self._interrupt_mining
                )
                
                # Si new_block existe, significa que NO fuimos interrumpidos y ganamos
                if new_block:
                    if self.consensus.add_block(new_block):
                        tx_count = len(new_block.transactions)
                        logger.info(f"💎 ¡BLOQUE #{new_block.index} MINADO! Hash: {new_block.hash[:8]} | TXs: {tx_count}")
                        
                        self._gossip.propagate_block(new_block.to_dict())
                    else:
                        logger.warning("Bloque propio rechazado (Stale/Viejo).")

            except Exception as e:
                logger.error(f"Error en hilo de minería: {e}")
                time.sleep(1)