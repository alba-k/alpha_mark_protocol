# akm/interface/api/dependencies.py
from typing import Optional, Dict, Any, Union

# Imports de Capa Core
from akm.core.nodes.miner_node import MinerNode
from akm.core.nodes.spv_node import SPVNode 
# Import de Configuración Central
from akm.core.config.config_manager import ConfigManager # <--- NECESARIO

# Imports de Infraestructura (Keystore)
from akm.infra.identity.keystore import Keystore

# Imports de Interface
from akm.interface.api.config import settings

# Definimos el tipo base
CoreNodeType = Union[MinerNode, SPVNode] 

class NodeContainer:
    """
    Service Container (Singleton).
    Gestiona el ciclo de vida del nodo activo y sus dependencias de identidad.
    """
    _instance: Optional[CoreNodeType] = None 
    _keystore: Optional[Keystore] = None
    _active_identity: Optional[Dict[str, Any]] = None

    @classmethod
    def get_instance(cls) -> CoreNodeType:
        if cls._instance is None:
            raise RuntimeError("El nodo no ha sido inicializado. Ejecute set_instance() primero.")
        return cls._instance

    @classmethod
    def set_instance(cls, node_instance: CoreNodeType):
        if cls._instance is not None: return
        cls._instance = node_instance
        print("✅ [API-DI] Instancia de nodo inyectada correctamente.")

    @classmethod
    def get_keystore(cls) -> Keystore:
        """
        Obtiene el Keystore configurado para este nodo específico.
        """
        if cls._keystore is None:
            # 🔥 MEJORA: Leer configuración dinámica en lugar de hardcode
            config = ConfigManager()
            wallet_file = config.persistence.wallet_filename
            
            # Inicializamos el Keystore con el archivo específico de este nodo
            cls._keystore = Keystore(filepath=wallet_file)
            print(f"🔑 [API] Keystore inicializado: {wallet_file}")
            
        return cls._keystore

    @classmethod
    def get_active_identity(cls) -> Dict[str, Any]:
        if cls._active_identity is None:
            raise RuntimeError("⚠️ Billetera BLOQUEADA. Carga una identidad primero.")
        return cls._active_identity

    @classmethod
    def set_active_identity(cls, identity: Dict[str, Any]):
        cls._active_identity = identity
        
        # Reactivar minería si corresponde
        if cls._instance and isinstance(cls._instance, MinerNode):
            address = identity.get('address')
            if address and settings.mining_enabled:
                print(f"⛏️ [API] ROL: MINERO | Reactivando para: {address}")
                cls._instance.stop_mining()
                cls._instance.start_mining_loop(address)

    @classmethod
    def shutdown(cls):
        if cls._instance:
            print("🛑 [API] Deteniendo nodo...")
            if hasattr(cls._instance, 'stop_mining'):
                cls._instance.stop_mining() # type: ignore
            
            if hasattr(cls._instance, 'stop'):
                cls._instance.stop()
                
            cls._instance = None

# --- INYECCIÓN ---

def get_node_dependency() -> CoreNodeType:
    return NodeContainer.get_instance()

def get_keystore_dependency() -> Keystore:
    return NodeContainer.get_keystore()

def get_identity_dependency() -> Dict[str, Any]:
    return NodeContainer.get_active_identity()