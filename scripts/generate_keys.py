import sys
import os
import json
import datetime

# --- AJUSTE DE RUTAS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, root_dir)

# --- IMPORTACIONES ---
from akm.infra.crypto.software_signer import SoftwareSigner
from akm.infra.identity.address_factory import AddressFactory
from akm.infra.identity.bip39_service import BIP39Service

def generate_identity(folder_name: str = "mis_billeteras"):
    print(f"📂 Preparando directorio: {folder_name}...")
    
    # 1. Crear el directorio si no existe
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"   ✅ Directorio creado: {folder_name}")

    print("🔑 Generando criptografía (BIP-39)...")
    
    # 2. Generar Datos (Mnemonic -> PrivKey -> PubKey -> Address)
    bip39 = BIP39Service()
    mnemonic = bip39.generate_mnemonic(strength=256)
    
    # Derivamos las claves
    private_key_hex = bip39.derive_master_private_key(mnemonic)
    signer = SoftwareSigner(private_key_hex)
    public_key_hex = signer.get_public_key()
    address = AddressFactory.create_from_public_key(public_key_hex)

    # Fecha de creación para registro
    creation_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ---------------------------------------------------------
    # ARCHIVO 1: EL DICCIONARIO (.json) - Para el sistema
    # ---------------------------------------------------------
    wallet_data = {
        "address": address,
        "public_key": public_key_hex,
        "private_key": private_key_hex,
        "mnemonic": mnemonic,
        "created_at": creation_date
    }
    
    # Usamos la dirección como parte del nombre del archivo para no sobreescribir
    short_addr = address[:6] 
    json_filename = os.path.join(folder_name, f"wallet_{short_addr}.json")
    
    with open(json_filename, 'w') as f:
        json.dump(wallet_data, f, indent=4)

    # ---------------------------------------------------------
    # ARCHIVO 2: TODOS LOS DATOS (.txt) - Para imprimir/leer
    # ---------------------------------------------------------
    txt_filename = os.path.join(folder_name, f"SEGURIDAD_{short_addr}.txt")
    
    full_info = f"""
===================================================================
                  🔐 ALPHA MARK PROTOCOL - IDENTITY CARD
===================================================================
FECHA DE CREACIÓN: {creation_date}
DIRECTORIO:        {os.path.abspath(folder_name)}
===================================================================

[1] DIRECCIÓN PÚBLICA (Address)
    Compártela para recibir pagos.
    👉 {address}

[2] FRASE DE RECUPERACIÓN (Mnemonic 24 Palabras)
    ¡MUY IMPORTANTE! Si pierdes esto, pierdes tu dinero.
    No la compartas con nadie.
    
    {mnemonic}

-------------------------------------------------------------------
DATOS TÉCNICOS AVANZADOS (Solo para expertos)
-------------------------------------------------------------------

[3] CLAVE PRIVADA (Private Key - Hex)
    Acceso total a los fondos. Mantener en secreto.
    🔑 {private_key_hex}

[4] CLAVE PÚBLICA (Public Key - Hex)
    Identidad matemática en la red.
    🌍 {public_key_hex}

===================================================================
⚠️  ADVERTENCIA DE SEGURIDAD
    1. Imprime este archivo y guárdalo en un lugar físico seguro.
    2. Borra este archivo de tu computadora si es posible.
    3. Nunca envíes este archivo por internet o chat.
===================================================================
"""
    
    with open(txt_filename, 'w', encoding='utf-8') as f:
        f.write(full_info)

    # --- RESUMEN FINAL ---
    print("\n✅ ¡PROCESO COMPLETADO!")
    print(f"   📂 Tus archivos están en: {folder_name}/")
    print(f"   📄 Diccionario (JSON):    wallet_{short_addr}.json")
    print(f"   📄 Hoja de Seguridad:     SEGURIDAD_{short_addr}.txt")
    print("-" * 50)

if __name__ == "__main__":
    # Puedes pasar el nombre de la carpeta como argumento
    target_folder = sys.argv[1] if len(sys.argv) > 1 else "mis_billeteras"
    generate_identity(target_folder)