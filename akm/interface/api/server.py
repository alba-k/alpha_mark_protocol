# akm/interface/api/server.py

import sys
import os
import logging
from typing import Dict, Any

# --- Configuración de Path ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path: sys.path.insert(0, project_root)

# --- Framework Imports ---
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# --- Project Imports ---
from akm.interface.api import schemas
from akm.interface.api.dependencies import (
    NodeContainer, get_node_dependency, get_identity_dependency
)
from akm.interface.api.config import settings
from akm.core.utils.monetary import Monetary 
from akm.core.nodes.spv_node import SPVNode
from akm.core.managers.wallet_manager import WalletManager
from akm.infra.crypto.software_signer import SoftwareSigner
from akm.core.factories.node_factory import NodeFactory

logger = logging.getLogger(__name__)

# ==============================================================================
# 🏗️ SERVICE LAYER (POO / SRP)
# ==============================================================================

class WalletService:
    def __init__(self, node: SPVNode):
        self.node = node

    def get_status(self) -> schemas.NodeStatusResponse:
        peers_count = 0
        if hasattr(self.node, 'p2p') and self.node.p2p:
            peers_count = len(self.node.p2p.get_connected_peers())

        return schemas.NodeStatusResponse(
            node_id="API-SPV-MOBILE",
            height=self.node.header_chain.height,
            peers_count=peers_count,
            is_syncing=False,
            environment="SPV_CLIENT"
        )

    def get_balance(self, address: str) -> schemas.BalanceResponse:
        self.node.request_balance_update(address)
        return schemas.BalanceResponse(
            address=address,
            balance=self.node.get_cached_balance(),
            utxo_count=self.node.get_cached_utxo_count()
        )

    def process_transaction(self, req: schemas.TransactionRequest, identity: Dict[str, Any]) -> schemas.TransactionResponse:
        try:
            priv_key = identity.get('private_key')
            sender_address = identity.get('address')
            
            if not priv_key or not sender_address:
                raise ValueError("Identidad de billetera no cargada correctamente.")

            # 1. Preparar valores
            signer = SoftwareSigner(priv_key)
            wallet_manager = WalletManager(signer)
            amount_alba = Monetary.to_albas(req.amount)
            fee_alba = Monetary.to_albas(req.fee)
            required_total = amount_alba + fee_alba

            # 2. Obtener UTXOs (Adapter de Memoria)
            utxo_source = self.node.get_memory_utxo_set()
            
            # --- CORRECCIÓN CRÍTICA DE SINCRONIZACIÓN [SOLUCIONADO] ---
            # Usamos el método del adaptador en lugar de intentar iterarlo directamente.
            # El adaptador sabe cómo sumar los diccionarios internos.
            available_in_utxos = utxo_source.get_balance_for_address(sender_address)
            
            # Si lo que tenemos en UTXOs cargados es menor a lo necesario,
            # no podemos construir la TX.
            if available_in_utxos < required_total:
                logger.warning(f"UTXOs insuficientes en memoria ({available_in_utxos}) para enviar ({required_total}). Solicitando sync...")
                
                # Disparar actualización a la red
                self.node.request_balance_update(sender_address)
                
                # Rechazar amablemente para que el cliente reintente
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                    detail="Sincronizando fondos con la red. Por favor intente en 5 segundos."
                )
            # ----------------------------------------------------------

            # 3. Crear Transacción (Ahora seguro porque sabemos que hay UTXOs)
            tx = wallet_manager.create_transaction(
                recipient_address=req.recipient_address,
                amount_alba=amount_alba,
                fee=fee_alba,
                utxo_set=utxo_source
            )

            # 4. Propagar
            if self.node.broadcast_transaction(tx):
                return schemas.TransactionResponse(
                    tx_hash=tx.tx_hash, 
                    status="broadcasted"
                )
            else:
                raise ValueError("Fallo en la propagación P2P.")

        except HTTPException:
            raise 
        except ValueError as e:
            logger.warning(f"Error de transacción: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.exception("Error crítico en transacción")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno procesando transacción.")

# ... (El resto del archivo lifespan, FastAPI setup, etc. se mantiene igual) ...

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("📱 [BOOT] Iniciando API Wallet (SPV Mode)...")
    try:
        spv_node = NodeFactory.create_node("SPV_NODE")
        if hasattr(spv_node, 'start'):
            spv_node.start()
            logger.info("✅ Nodo SPV conectado a la red.")
        NodeContainer.set_instance(spv_node)
        yield
    except Exception as e:
        logger.critical(f"❌ Error fatal al iniciar SPV: {e}")
        sys.exit(1)
    finally:
        logger.info("🛑 Apagando nodo SPV...")
        NodeContainer.shutdown()

app = FastAPI(title=settings.title, version=settings.version, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
static_dir = os.path.join(current_dir, "../web")
if os.path.exists(static_dir):
    app.mount("/app", StaticFiles(directory=static_dir, html=True), name="static")

def get_wallet_service(node: Any = Depends(get_node_dependency)) -> WalletService:
    if not isinstance(node, SPVNode):
        raise HTTPException(status_code=500, detail="Configuración incorrecta: La API Wallet requiere un nodo tipo SPV.")
    return WalletService(node)

@app.get("/status", response_model=schemas.NodeStatusResponse, tags=["Sistema"])
def get_status(service: WalletService = Depends(get_wallet_service)):
    return service.get_status()

@app.get("/balance/{address}", response_model=schemas.BalanceResponse, tags=["Wallet"])
def get_balance(address: str, service: WalletService = Depends(get_wallet_service)):
    return service.get_balance(address)

@app.post("/transactions", response_model=schemas.TransactionResponse, tags=["Wallet"])
def send_transaction(req: schemas.TransactionRequest, service: WalletService = Depends(get_wallet_service), identity: Dict[str, Any] = Depends(get_identity_dependency)):
    return service.process_transaction(req, identity)

@app.post("/wallet/create", response_model=schemas.WalletResponse, tags=["Keystore"])
def create_wallet(req: schemas.WalletCreateRequest):
    try:
        ks = NodeContainer.get_keystore()
        if ks.wallet_exists(): raise HTTPException(status_code=400, detail="Ya existe una billetera.")
        identity = ks.create_new_wallet(req.password.get_secret_value())
        NodeContainer.set_active_identity(identity)
        return schemas.WalletResponse(address=identity['address'], public_key=identity['public_key'], status="created", mnemonic=identity['mnemonic'])
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/wallet/load", response_model=schemas.WalletResponse, tags=["Keystore"])
def load_wallet(req: schemas.WalletLoadRequest):
    try:
        ks = NodeContainer.get_keystore()
        identity = ks.load_wallet(req.get_password_value())
        NodeContainer.set_active_identity(identity)
        return schemas.WalletResponse(address=identity['address'], public_key=identity['public_key'], status="unlocked", mnemonic=None)
    except ValueError: raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    except FileNotFoundError: raise HTTPException(status_code=404, detail="No existe billetera.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)