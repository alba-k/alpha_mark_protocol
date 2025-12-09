# akm/core/nodes/miner_node.py
import logging
import threading
import time
from typing import Optional, Dict, Any

# Herencia
from akm.core.nodes.full_node import FullNode

# Dependencias
from akm.core.managers.mining_manager import MiningManager
from akm.infra.network.p2p_service import P2PService
from akm.core.managers.gossip_manager import GossipManager
from akm.core.models.blockchain import Blockchain
from akm.core.managers.utxo_set import UTXOSet
from akm.core.services.mempool import Mempool
from akm.core.managers.consensus_orchestrator import ConsensusOrchestrator
from akm.core.managers.chain_reorg_manager import ChainReorgManager
from akm.core.config.config_manager import ConfigManager
from akm.core.config.protocol_constants import ProtocolConstants

logging.basicConfig(level=logging.INFO, format='[MinerNode] %(message)s')

class MinerNode(FullNode):
    """
    [LSP] Nodo Minero.
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
        mining_manager: MiningManager
    ):
        # Inicializar el Padre (FullNode) explícitamente
        super().__init__(
            p2p_service, gossip_manager, blockchain, utxo_set, mempool, consensus, reorg_manager
        )
        
        self.miner = mining_manager
        
        # Cargar configuración
        config = ConfigManager()
        self._miner_address: Optional[str] = config.mining.default_miner_address
        self._mining_active = False
        
        # ⚡ NUEVO: Evento para cancelar minería si llega un bloque externo
        self._interrupt_mining = threading.Event()

    def start_mining_loop(self, miner_address: Optional[str] = None):
        """
        Inicia el proceso de minería.
        Si se pasa una dirección, se usa esa. Si no, usa la de la configuración.
        """
        # Prioridad: Argumento > Configuración
        address_to_use = miner_address if miner_address else self._miner_address
        
        if not address_to_use:
            logging.error("❌ No se puede iniciar minería: Falta dirección de pago.")
            return

        self._miner_address = address_to_use
        self._mining_active = True
        self._interrupt_mining.clear()
        
        mining_thread = threading.Thread(target=self._mining_worker, daemon=True)
        mining_thread.start()
        logging.info(f"⛏️ Minería ACTIVA -> {self._miner_address[:10]}...")

    def stop_mining(self):
        self._mining_active = False
        self._interrupt_mining.set() # Forzar salida inmediata
        logging.info("🛑 Minería detenida.")

    def _process_payload(self, msg_type: str, payload: Dict[str, Any], peer_id: str):
        """
        Override: Intercepta bloques entrantes para reiniciar la minería.
        """
        # 1. Procesamiento normal del Nodo Completo (Validación, Consenso, Mempool)
        super()._process_payload(msg_type, payload, peer_id)
        
        # 2. Lógica Reactiva del Minero
        if msg_type == ProtocolConstants.MSG_BLOCK:
            # Si alguien más encontró un bloque, detenemos nuestro trabajo actual
            # para empezar a minar sobre el nuevo padre inmediatamente.
            if self._mining_active:
                logging.info("⚡ [Miner] Bloque detectado en la red. Reiniciando trabajo...")
                self._interrupt_mining.set()

    def mine_one_block(self, miner_address: Optional[str] = None) -> bool:
        """Intenta minar un solo bloque."""
        
        # Determinar qué dirección usar (Argumento > Interna > Error)
        target_address = miner_address if miner_address else self._miner_address

        if not target_address:
            logging.error("Falta dirección de minero.")
            return False

        # Actualizamos la interna por consistencia si no estaba seteadas
        if not self._miner_address:
            self._miner_address = target_address

        # Resetear bandera de interrupción antes de empezar
        self._interrupt_mining.clear()

        logging.info("🔨 Trabajando en bloque...")
        try:
            # ⚡ CORRECCIÓN: Pasamos el evento de interrupción al Manager
            # Nota: MiningManager.mine_block debe ser actualizado para aceptar este argumento opcional
            new_block = self.miner.mine_block(target_address, interrupt_event=self._interrupt_mining)
            
            # Si mine_block retorna None, significa que fue interrumpido
            if new_block is None:
                logging.info("⚠️ Minería interrumpida (Stale Block evitado).")
                return False

            if self.consensus.add_block(new_block):
                logging.info(f"💎 ¡BLOQUE ENCONTRADO! Hash: {new_block.hash[:8]}")
                self.gossip.propagate_block(new_block.to_dict())
                return True
            else:
                logging.warning("Bloque rechazado (Stale).")
                return False
                
        except Exception as e:
            logging.error(f"Error minería: {e}")
            return False

    def _mining_worker(self):
        while self._mining_active:
            # El worker intenta minar. Si es interrumpido (return False),
            # el bucle while vuelve a empezar inmediatamente (con el nuevo estado de la cadena).
            self.mine_one_block()
            
            # Pequeña pausa para no saturar si hay errores continuos
            if self._mining_active:
                time.sleep(0.1)