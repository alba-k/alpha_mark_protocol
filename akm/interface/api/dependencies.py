# akm/interface/api/dependencies.py
import os
from typing import Optional, Dict, Any, Union

# Imports de Capa Core
from akm.core.nodes.miner_node import MinerNode
from akm.core.nodes.spv_node import SPVNode  # [NUEVO]
from akm.core.factories.node_factory import NodeFactory

# Imports de Infraestructura (Keystore)
from akm.infra.identity.keystore import Keystore

# Imports de Interface
from akm.interface.api.config import settings

class NodeContainer:
    """
    Service Container (Singleton).
    Gestiona el ciclo de vida del nodo activo (Miner o SPV).
    """
    _instance: Optional[Union[MinerNode, SPVNode]] = None # Soporte Polimórfico
    _keystore: Optional[Keystore] = None
    _active_identity: Optional[Dict[str, Any]] = None

    @classmethod
    def get_instance(cls) -> Union[MinerNode, SPVNode]:
        if cls._instance is None:
            raise RuntimeError("El nodo no ha sido inicializado.")
        return cls._instance

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
    def initialize(cls):
        """Arranca el sistema leyendo la configuración de Docker."""
        if cls._instance is not None: return

        # 1. LEER TIPO DE NODO
        node_type = os.getenv("NODE_TYPE", "FULL").upper()
        
        print(f"🔧 [API] Configurando entorno: {settings.db_name}")
        os.environ["AKM_DB_NAME"] = settings.db_name
        
        print(f"🚀 [API] Iniciando motor blockchain en modo: {node_type}...")
        
        try:
            if node_type == "SPV":
                # --- MODO CLIENTE LIGERO ---
                print("📱 Creando Nodo SPV (Mobile)...")
                node = NodeFactory.create_spv_node()
                node.start()
                # Auto-sync opcional al inicio
                node.sync()
            else:
                # --- MODO MINERO / FULL ---
                print("🏭 Creando Nodo Completo (Miner)...")
                node = NodeFactory.create_miner_node()
                node.start() 
            
            cls._instance = node
            print("✅ [API] Nodo listo.")
            
        except Exception as e:
            print(f"❌ [API] Error fatal iniciando nodo: {e}")
            raise e

    @classmethod
    def shutdown(cls):
        if cls._instance:
            print("🛑 [API] Deteniendo nodo...")
            # Si tiene método stop_mining (MinerNode), lo llamamos
            if hasattr(cls._instance, 'stop_mining'):
                cls._instance.stop_mining() # type: ignore
            
            # Detener red base
            if hasattr(cls._instance, 'stop'):
                cls._instance.stop()
                
            cls._instance = None

# --- INYECCIÓN ---

def get_node_dependency() -> Union[MinerNode, SPVNode]:
    return NodeContainer.get_instance()

def get_keystore_dependency() -> Keystore:
    return NodeContainer.get_keystore()

def get_identity_dependency() -> Dict[str, Any]:
    return NodeContainer.get_active_identity()