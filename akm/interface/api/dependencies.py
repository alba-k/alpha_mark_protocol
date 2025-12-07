# akm/interface/api/dependencies.py
import os
from typing import Optional, Dict, Any

# Imports de Capa Core
from akm.core.nodes.miner_node import MinerNode
from akm.core.factories.node_factory import NodeFactory

# Imports de Infraestructura (Keystore)
from akm.infra.identity.keystore import Keystore

# Imports de Interface
from akm.interface.api.config import settings

class NodeContainer:
    """
    Service Container (Singleton) para el Nodo Blockchain y Keystore.
    Gestiona la vida del nodo y el estado de la sesión (billetera cargada).
    """
    _instance: Optional[MinerNode] = None
    _keystore: Optional[Keystore] = None
    _active_identity: Optional[Dict[str, Any]] = None

    @classmethod
    def get_instance(cls) -> MinerNode:
        if cls._instance is None:
            raise RuntimeError("El nodo no ha sido inicializado. ¿Olvidaste llamar a initialize()?")
        return cls._instance

    @classmethod
    def get_keystore(cls) -> Keystore:
        if cls._keystore is None:
            # Inicializamos el keystore apuntando al archivo por defecto
            cls._keystore = Keystore(filepath="node_wallet.dat")
        return cls._keystore

    @classmethod
    def get_active_identity(cls) -> Dict[str, Any]:
        """Devuelve la identidad cargada actualmente (Address, Public Key, Private Key)."""
        if cls._active_identity is None:
            raise RuntimeError("⚠️ Billetera BLOQUEADA. Debes cargarla primero con POST /wallet/load o crear una nueva.")
        return cls._active_identity

    @classmethod
    def set_active_identity(cls, identity: Dict[str, Any]):
        """Establece la identidad activa y decide si activar minería según configuración."""
        cls._active_identity = identity
        
        # Si el nodo ya está corriendo, actualizamos el comportamiento
        if cls._instance:
            address = identity.get('address')
            if address:
                
                # --- LÓGICA DE SEPARACIÓN DE ROLES ---
                if settings.mining_enabled:
                    print(f"⛏️ [API] ROL: MINERO | Iniciando trabajo para: {address}")
                    # Reiniciamos el proceso de minería con la nueva dirección
                    cls._instance.stop_mining()
                    cls._instance.start_mining_loop(address)
                else:
                    print(f"🛡️ [API] ROL: WALLET (Pasivo) | Identidad cargada: {address}")
                    print("   -> Este nodo NO minará. Solo enviará transacciones a la red.")
                    # Aseguramos que la minería esté apagada
                    cls._instance.stop_mining()

    @classmethod
    def initialize(cls):
        """Arranca el sistema al iniciar la API."""
        if cls._instance is not None: return

        print(f"🔧 [API] Configurando entorno: {settings.db_name}")
        # Inyectamos la variable de entorno para que el ConfigManager del Core la lea
        os.environ["AKM_DB_NAME"] = settings.db_name
        
        print("🚀 [API] Iniciando motor blockchain...")
        try:
            node = NodeFactory.create_miner_node()
            # Arrancamos componentes de red (P2P). La minería depende de la config y wallet.
            node.start() 
            
            cls._instance = node
            print("✅ [API] Nodo listo (Esperando carga de Wallet).")
        except Exception as e:
            print(f"❌ [API] Error fatal iniciando nodo: {e}")
            raise e

    @classmethod
    def shutdown(cls):
        """Apaga el sistema limpiamente."""
        if cls._instance:
            print("🛑 [API] Deteniendo nodo...")
            cls._instance.stop_mining()
            cls._instance = None

# --- FUNCIONES DE INYECCIÓN (DEPENDENCY INJECTION) ---

def get_node_dependency() -> MinerNode:
    return NodeContainer.get_instance()

def get_keystore_dependency() -> Keystore:
    return NodeContainer.get_keystore()

def get_identity_dependency() -> Dict[str, Any]:
    return NodeContainer.get_active_identity()