# akm/interface/api/schemas.py
from pydantic import BaseModel, Field, SecretStr, ConfigDict
from typing import Optional

class ImmutableModel(BaseModel):
    """
    Clase base que fuerza la inmutabilidad (frozen=True).
    Garantiza que el estado del objeto no sea modificado después de crearse.
    """
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        extra='ignore'
    )

# --- GESTIÓN DE BILLETERA (KEYSTORE) ---

class WalletCreateRequest(ImmutableModel):
    password: SecretStr = Field(..., description="Contraseña para encriptar el nuevo archivo")

class WalletLoadRequest(ImmutableModel):
    password: SecretStr = Field(..., description="Contraseña para desbloquear la billetera")

    def get_password_value(self) -> str:
        return self.password.get_secret_value()

class WalletResponse(ImmutableModel):
    address: str
    public_key: str
    status: str
    # CAMPO NUEVO: Muestra la frase semilla solo al crear.
    mnemonic: Optional[str] = Field(None, description="¡IMPORTANTE! 12 palabras de respaldo. Guárdalas.")

# --- TRANSACCIONES ---

class TransactionRequest(ImmutableModel):
    # Ya no pedimos clave privada, la API la tiene en memoria tras el login.
    recipient_address: str = Field(..., description="Dirección Base58 del destinatario")
    amount: float = Field(..., gt=0)
    fee: float = Field(1.0, ge=0)

class TransactionResponse(ImmutableModel):
    tx_hash: str
    status: str

# --- CONSULTAS DE BLOQUE Y ESTADO ---

class BlockResponse(ImmutableModel):
    index: int
    hash: str
    previous_hash: str
    timestamp: int
    transactions_count: int
    nonce: int

class BalanceResponse(ImmutableModel):
    address: str
    balance: float
    utxo_count: int

class NodeStatusResponse(ImmutableModel):
    node_id: str
    height: int
    peers_count: int
    is_syncing: bool
    environment: str