# akm/core/nodes/spm_node.py
import logging
from typing import List, Optional, Dict, Any

# Ajusta las rutas de importación según tu estructura real si han cambiado
from akm.core.nodes.base_node import BaseNode
from akm.core.config.network_config import NetworkConfig
from akm.infra.network.p2p_service import P2PService
from akm.core.managers.gossip_manager import GossipManager

logger = logging.getLogger(__name__)

class SPMNode(BaseNode):
    """
    Standard Peer Node (SPM).
    Nodo completo, validación fuerte, identidad SPM.
    """
    
    def __init__(self, host: str, port: int, seeds: Optional[List[str]] = None):
        # 1. Configuración SPM (Alto rendimiento)
        config = NetworkConfig()
        update_data: Dict[str, Any] = {
            "p2p_port": port,
            "max_peers": 50,  
            "seed_nodes": seeds or []
        }
        config.update_from_dict(update_data)

        if host:
            config._host = host # type: ignore

        # 2. Identidad: "AlphaMark/SPM"
        # Creamos el servicio de red primero
        network_service = P2PService(
            config=config, 
            agent_name="AlphaMark/SPM:1.0.0" 
        )
        
        # 3. Componentes internos
        # CORRECCIÓN: Pasamos 'network_service' al GossipManager como requiere su __init__
        gossip_manager = GossipManager(p2p_service=network_service) 
        
        # 4. Inicializar Padre (BaseNode)
        super().__init__(
            network_service=network_service, 
            gossip_manager=gossip_manager
        )
        
        logger.info(f"🚀 NODO SPM INICIALIZADO | ID: AlphaMark/SPM | Listen: {config.host}:{config.port}")

    def _process_payload(self, msg_type: str, payload: Dict[str, Any], peer_id: str) -> None:
        """
        Lógica específica del SPM (Sobreescribe BaseNode).
        """
        try:
            if msg_type == "BLOCK":
                logger.debug(f"SPM: Recibido BLOQUE de {peer_id}. Iniciando validación completa...")
                # self.blockchain.validate_and_add(payload)
                
            elif msg_type == "TX":
                logger.debug(f"SPM: Recibida TX de {peer_id}. Verificando en Mempool...")
                # self.mempool.add_transaction(payload)
                
            elif msg_type == "GET_HEADERS":
                logger.debug(f"SPM: Nodo {peer_id} solicita cabeceras. Sirviendo datos...")
                # self._handle_get_headers(payload, peer_id)
                
            else:
                logger.debug(f"SPM: Mensaje {msg_type} recibido (sin manejador específico).")

        except Exception as e:
            logger.error(f"Error en SPM procesando {msg_type}: {e}")