# akm/interface/api/server.py
import sys
import os

# 1. AJUSTE DE RUTAS
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from typing import List, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Imports de Interface (DTOs, DI, Config)
from akm.interface.api import schemas
from akm.interface.api.dependencies import (
    NodeContainer, 
    get_node_dependency, 
    get_keystore_dependency, 
    get_identity_dependency
)
from akm.interface.api.config import settings

# ⚡ IMPORTACIÓN REQUERIDA: Traemos el conversor monetario seguro
from akm.core.utils.monetary import Monetary 
# Imports de Core
from akm.core.nodes.miner_node import MinerNode
from akm.core.managers.wallet_manager import WalletManager
from akm.infra.crypto.software_signer import SoftwareSigner
from akm.infra.identity.keystore import Keystore

# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    NodeContainer.initialize()
    yield
    NodeContainer.shutdown()

# --- APP ---
app = FastAPI(
    title=settings.title,
    version=settings.version,
    lifespan=lifespan,
    debug=settings.debug_mode
)

# --- CONFIGURACIÓN WEB ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(current_dir, "../web")
if not os.path.exists(static_dir):
    try: os.makedirs(static_dir)
    except: pass

if os.path.exists(static_dir):
    app.mount("/app", StaticFiles(directory=static_dir, html=True), name="static")

# --- ENDPOINTS ---

@app.get("/", tags=["Sistema"])
def root() -> Dict[str, Any]:
    return {
        "system": settings.title,
        "status": "online",
        "port": settings.port,
        "coin_scale": settings.coin_scale,
        "web_interface": f"http://localhost:{settings.port}/app/index.html"
    }

@app.get("/status", response_model=schemas.NodeStatusResponse, tags=["Sistema"])
def get_status(node: MinerNode = Depends(get_node_dependency)) -> schemas.NodeStatusResponse:
    tip = node.blockchain.last_block
    height = tip.index if tip else 0
    peers = 0
    p2p_service = getattr(node, 'p2p', None)
    if p2p_service and hasattr(p2p_service, 'connection_manager'):
        peers = len(p2p_service.connection_manager.get_active_peers())
    
    return schemas.NodeStatusResponse(
        node_id="API-Node-01",
        height=height,
        peers_count=peers,
        is_syncing=False,
        environment="prod"
    )

@app.get("/balance/{address}", response_model=schemas.BalanceResponse, tags=["Wallet"])
def get_balance(address: str, node: MinerNode = Depends(get_node_dependency)) -> schemas.BalanceResponse:
    try:
        # El nodo devuelve enteros (ALBAS)
        balance_albas = node.get_balance(address)
        utxos = node.utxo_set.get_utxos_for_address(address)
        
        # ⚡ CORRECCIÓN DE SALIDA: Usar Monetary.to_akm para precisión total
        balance_decimal = Monetary.to_akm(balance_albas)
        # Convertimos a float para satisfacer el Pydantic schema (tipo de salida API)
        balance_human = float(balance_decimal) 

        return schemas.BalanceResponse(
            address=address,
            balance=balance_human, 
            utxo_count=len(utxos)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/blocks", response_model=List[schemas.BlockResponse], tags=["Blockchain"])
def get_blocks(limit: int = 10, node: MinerNode = Depends(get_node_dependency)) -> List[schemas.BlockResponse]:
    blocks: List[schemas.BlockResponse] = []
    current = node.blockchain.last_block
    count = 0
    while current is not None and count < limit:
        blocks.append(schemas.BlockResponse(
            index=current.index,
            hash=current.hash,
            previous_hash=current.previous_hash,
            timestamp=current.timestamp,
            transactions_count=len(current.transactions),
            nonce=current.nonce
        ))
        if current.index == 0: break
        current = node.blockchain.get_block_by_hash(current.previous_hash)
        count += 1
    return blocks

@app.post("/wallet/create", response_model=schemas.WalletResponse, tags=["Wallet Management"])
def create_wallet(req: schemas.WalletCreateRequest, keystore: Keystore = Depends(get_keystore_dependency)) -> schemas.WalletResponse:
    try:
        if keystore.wallet_exists():
            raise HTTPException(status_code=400, detail="Ya existe una billetera. Usa /load.")
        
        password = req.password.get_secret_value()
        identity = keystore.create_new_wallet(password)
        NodeContainer.set_active_identity(identity)
        
        return schemas.WalletResponse(
            address=identity['address'],
            public_key=identity['public_key'],
            status="created_and_loaded",
            mnemonic=identity.get('mnemonic', 'No disponible')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/wallet/load", response_model=schemas.WalletResponse, tags=["Wallet Management"])
def load_wallet(req: schemas.WalletLoadRequest, keystore: Keystore = Depends(get_keystore_dependency)) -> schemas.WalletResponse:
    try:
        password = req.get_password_value()
        identity = keystore.load_wallet(password)
        NodeContainer.set_active_identity(identity)
        
        return schemas.WalletResponse(
            address=identity['address'],
            public_key=identity['public_key'],
            status="unlocked",
            mnemonic=None
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No se encontró wallet.dat")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transactions", response_model=schemas.TransactionResponse, tags=["Wallet"])
def send_transaction(
    req: schemas.TransactionRequest, 
    node: MinerNode = Depends(get_node_dependency),
    identity: Dict[str, Any] = Depends(get_identity_dependency)
) -> schemas.TransactionResponse:
    try:
        priv_key: str = identity['private_key']
        signer = SoftwareSigner(priv_key)
        wallet = WalletManager(signer)
        
        # ⚡ CORRECCIÓN DE ENTRADA: Usar Monetary.to_albas para precisión total
        # Convierte la entrada del usuario (float o string) a un entero seguro (Albas)
        amount_in_albas = Monetary.to_albas(req.amount) 
        fee_in_albas = Monetary.to_albas(req.fee)

        if amount_in_albas <= 0:
            raise HTTPException(status_code=400, detail="Monto demasiado bajo.")

        tx = wallet.create_transaction(
            recipient_address=req.recipient_address,
            amount_alba=amount_in_albas,
            fee=fee_in_albas,
            utxo_set=node.utxo_set
        )
        
        if node.submit_transaction(tx):
            return schemas.TransactionResponse(
                tx_hash=tx.tx_hash,
                status="pending_mempool"
            )
        else:
            raise HTTPException(status_code=400, detail="Transacción rechazada")
            
    except ValueError as e:
        # Capturamos el ValueError si el monto AKM excedió los 8 decimales
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print(f"🌍 Iniciando {settings.title} en puerto {settings.port}")
    print(f"💰 Factor de moneda: {settings.coin_scale}")
    uvicorn.run(app, host=settings.host, port=settings.port)