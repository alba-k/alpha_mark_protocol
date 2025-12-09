# akm/interface/api/dependencies.py
from typing import Optional, Dict, Any, Union

# Imports de Capa Core
from akm.core.nodes.miner_node import MinerNode
from akm.core.nodes.spv_node import SPVNode 

# Imports de Infraestructura (Keystore)
from akm.infra.identity.keystore import Keystore

# Imports de Interface
from akm.interface.api.config import settings

# Definimos el tipo base para facilitar la lectura
CoreNodeType = Union[MinerNode, SPVNode] 

class NodeContainer:
    """
    Service Container (Singleton).
    Gestiona el ciclo de vida del nodo activo (Inyección de Dependencias).
    """
    _instance: Optional[CoreNodeType] = None # Soporte Polimórfico
    _keystore: Optional[Keystore] = None
    _active_identity: Optional[Dict[str, Any]] = None

    @classmethod
    def get_instance(cls) -> CoreNodeType:
        """Acceso a la instancia del nodo activo."""
        if cls._instance is None:
            raise RuntimeError("El nodo no ha sido inicializado. Ejecute set_instance() primero.")
        return cls._instance

    @classmethod
    def set_instance(cls, node_instance: CoreNodeType):
        """
        🔥 NUEVA FUNCIÓN: Inyección de Dependencia (Setter).
        Permite a src/node.py (el lanzador) inyectar el CoreNode ya creado.
        """
        if cls._instance is not None: return
        cls._instance = node_instance
        print("✅ [API-DI] Instancia de nodo inyectada correctamente.")

    # [El resto de métodos get_keystore, get_active_identity, set_active_identity, y shutdown se mantienen]
    
    @classmethod
    def get_keystore(cls) -> Keystore:
        if cls._keystore is None:
            cls._keystore = Keystore(filepath="node_wallet.dat")
        return cls._keystore

    @classmethod
    def get_active_identity(cls) -> Dict[str, Any]:
        if cls._active_identity is None:
            raise RuntimeError("⚠️ Billetera BLOQUEADA. Carga una identidad primero.")
        return cls._active_identity

    @classmethod
    def set_active_identity(cls, identity: Dict[str, Any]):
        cls._active_identity = identity
        
        # Solo reaccionamos si es un Minero (SPV no mina)
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