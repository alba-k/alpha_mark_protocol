# akm/interface/api/dependencies.py
import logging
from typing import Optional, Dict, Any, Union

# Framework Imports
from fastapi import HTTPException, status

# Imports de Capa Core
from akm.core.nodes.miner_node import MinerNode
from akm.core.nodes.spv_node import SPVNode 
from akm.core.nodes.full_node import FullNode  # <--- 1. AGREGADO

# Import de Configuración Central
from akm.core.config.config_manager import ConfigManager 

# Imports de Infraestructura (Keystore)
from akm.infra.identity.keystore import Keystore

# Imports de Interface
from akm.interface.api.config import settings

logger = logging.getLogger(__name__)

# Definimos el tipo base (Ahora incluye FullNode)
CoreNodeType = Union[FullNode, MinerNode, SPVNode] # <--- 2. ACTUALIZADO

class NodeContainer:
    _instance: Optional[CoreNodeType] = None 
    _keystore: Optional[Keystore] = None
    _active_identity: Optional[Dict[str, Any]] = None

    @classmethod
    def get_instance(cls) -> CoreNodeType:
        if cls._instance is None:
            logger.critical("🚨 ERROR DE ARRANQUE: El nodo no ha sido inicializado. Ejecute set_instance() primero.")
            raise RuntimeError("El nodo no ha sido inicializado. Ejecute set_instance() primero.")
        return cls._instance

    @classmethod
    def set_instance(cls, node_instance: CoreNodeType):
        if cls._instance is not None: 
            logger.debug("Instancia de nodo ya inyectada. Ignorando set_instance.")
            return
            
        cls._instance = node_instance
        node_type = type(node_instance).__name__
        logger.info(f"✅ [API-DI] Instancia de nodo '{node_type}' inyectada correctamente.")

    @classmethod
    def get_keystore(cls) -> Keystore:
        if cls._keystore is None:
            try:
                config = ConfigManager()
                # Acceso seguro a la configuración de persistencia
                if hasattr(config, 'persistence') and hasattr(config.persistence, 'wallet_filename'):
                    wallet_file = config.persistence.wallet_filename
                else:
                    wallet_file = "wallet.dat" # Fallback seguro
                
                # Inicializamos el Keystore con el archivo específico de este nodo
                cls._keystore = Keystore(filepath=wallet_file)
                logger.info(f"🔑 [API] Keystore inicializado: {wallet_file}")
                
            except Exception as e:
                logger.error(f"❌ Error al inicializar Keystore: {e}")
                raise

        return cls._keystore

    @classmethod
    def get_active_identity(cls) -> Optional[Dict[str, Any]]:
        """Devuelve la identidad activa o None si no hay login."""
        return cls._active_identity

    @classmethod
    def set_active_identity(cls, identity: Dict[str, Any]):
        cls._active_identity = identity
        address = identity.get('address', 'N/A')
        logger.info(f"🔓 Identidad activa establecida. Dirección: {address}")
        
        # Reactivar minería si corresponde (Solo si es MinerNode)
        if cls._instance and isinstance(cls._instance, MinerNode):
            # Verificación segura de configuración
            mining_enabled = getattr(settings, 'mining_enabled', False)
            
            if address and mining_enabled:
                logger.info(f"⛏️ [API] ROL: MINERO | Reactivando bucle de minería para: {address[:12]}...")
                cls._instance.stop_mining()
                cls._instance.start_mining_loop(address)
            else:
                logger.warning("⚠️ Minería inactiva por configuración o falta de dirección.")

    @classmethod
    def shutdown(cls):
        if cls._instance:
            logger.info("🛑 [API] Iniciando el proceso de detención del nodo...")
            
            # Detener bucles de minería si existen
            if hasattr(cls._instance, 'stop_mining'):
                cls._instance.stop_mining() # type: ignore
                logger.debug("Minería detenida.")
            
            # Detener bucle principal de red
            if hasattr(cls._instance, 'stop'):
                cls._instance.stop()
                logger.info("Instancia de nodo detenida con éxito.")
                
            cls._instance = None
        else:
            logger.debug("El nodo ya estaba detenido.")

def get_node_dependency() -> CoreNodeType:
    return NodeContainer.get_instance()

def get_keystore_dependency() -> Keystore:
    return NodeContainer.get_keystore()

def get_identity_dependency() -> Dict[str, Any]:
    """
    Inyector de dependencia para endpoints que requieren autenticación.
    Si la billetera está bloqueada, devuelve un error HTTP 401 controlado
    en lugar de crashear el servidor.
    """
    identity = NodeContainer.get_active_identity()
    
    if identity is None:
        logger.warning("🚫 Acceso denegado: Intento de operación sin identidad cargada.")
        # [FIX] Lanzamos HTTPException en lugar de RuntimeError para no tumbar Uvicorn
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Billetera bloqueada. Por favor, desbloquea tu billetera primero (/wallet/load)."
        )
        
    return identity