# scripts/generate_keys.py
import sys
import os
import json
import secrets
from typing import Any

# Ajuste de rutas para importar módulos hermanos
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.insert(0, root_dir)

from akm.infra.crypto.software_signer import SoftwareSigner
from akm.infra.identity.address_factory import AddressFactory

def generate_identity(output_file: str = "wallet_identity.json"):
    print("🔑 Generando nueva identidad criptográfica...")
    
    # 1. Generar Clave Privada (32 bytes hex)
    private_key_hex = secrets.token_hex(32)
    
    # 2. Derivar Clave Pública y Dirección
    signer = SoftwareSigner(private_key_hex)
    public_key_hex = signer.get_public_key()
    
    # ⚡ CORRECCIÓN DE TYPO: create_from_public_key
    address = AddressFactory.create_from_public_key(public_key_hex)
    
    identity_data: dict[str, Any] = {
        "private_key": private_key_hex,
        "public_key": public_key_hex,
        "address": address
    }
    
    # 3. Guardar
    with open(output_file, 'w') as f:
        json.dump(identity_data, f, indent=4)
        
    print(f"✅ Identidad guardada en: {output_file}")
    print(f"   Address: {address}")
    print(f"   Pub Key: {public_key_hex[:16]}...")
    print("⚠️  ADVERTENCIA: Guarda este archivo en un lugar seguro.")

if __name__ == "__main__":
    # Permite pasar el nombre del archivo como argumento
    filename = sys.argv[1] if len(sys.argv) > 1 else "wallet_identity.json"
    generate_identity(filename)