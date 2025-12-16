import sys
import os
import json
import logging

# Configurar path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports del proyecto
from akm.core.models.transaction import Transaction
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput
from akm.core.services.transaction_hasher import TransactionHasher

# Configurar logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DEBUGGER")

def print_hex_diff(name, val1, val2):
    match = val1 == val2
    icon = "✅" if match else "❌"
    print(f"{icon} {name}:")
    print(f"   ORIG: {val1}")
    print(f"   DEST: {val2}")

def main():
    print("🔬 INICIANDO DIAGNÓSTICO DE INTEGRIDAD DE TRANSACCIÓN\n")

    # 1. Simular Creación en Wallet (Datos Puros / Bytes)
    print("1. Creando Transacción Original (Wallet)...")
    inp = TxInput(
        previous_tx_hash="0" * 64, 
        output_index=0, 
        script_sig=b'\x11\x22\x33' # Bytes reales
    )
    out = TxOutput(
        value_alba=50, 
        script_pubkey=b'\xaa\xbb\xcc' # Bytes reales
    )
    
    tx_orig = Transaction(
        tx_hash="",
        timestamp=123456789,
        inputs=[inp],
        outputs=[out],
        fee=1
    )
    
    # Calcular Hash Original
    hash_orig = TransactionHasher.calculate(tx_orig)
    tx_orig.tx_hash = hash_orig
    print(f"   Hash Original: {hash_orig}")

    # 2. Simular Serialización a JSON (Red)
    print("\n2. Serializando a JSON (Simulando Red)...")
    tx_json_dict = tx_orig.to_dict()
    tx_json_str = json.dumps(tx_json_dict, indent=2)
    print(f"   JSON Payload:\n{tx_json_str}")

    # 3. Simular Recepción en Full Node (Deserialización)
    print("\n3. Reconstruyendo en Full Node...")
    # Simular que leemos el JSON (los bytes se vuelven strings hex)
    received_data = json.loads(tx_json_str)
    tx_reconst = Transaction.from_dict(received_data)

    # 4. Comparar Campos Críticos
    print("\n4. 🔍 COMPARANDO CAMPOS INTERNOS:")
    
    # Inputs
    orig_sig = tx_orig.inputs[0].script_sig
    dest_sig = tx_reconst.inputs[0].script_sig
    print_hex_diff("Input Script Sig (Type & Val)", 
                   f"{type(orig_sig)} {orig_sig.hex() if isinstance(orig_sig, bytes) else orig_sig}", 
                   f"{type(dest_sig)} {dest_sig.hex() if isinstance(dest_sig, bytes) else dest_sig}")

    # Outputs
    orig_pub = tx_orig.outputs[0].script_pubkey
    dest_pub = tx_reconst.outputs[0].script_pubkey
    print_hex_diff("Output Script Pubkey (Type & Val)", 
                   f"{type(orig_pub)} {orig_pub.hex() if isinstance(orig_pub, bytes) else orig_pub}", 
                   f"{type(dest_pub)} {dest_pub.hex() if isinstance(dest_pub, bytes) else dest_pub}")
    
    # Timestamp
    print_hex_diff("Timestamp", tx_orig.timestamp, tx_reconst.timestamp)
    
    # Fee
    print_hex_diff("Fee", tx_orig.fee, tx_reconst.fee)

    # 5. Calcular Hash Reconstruido
    hash_reconst = TransactionHasher.calculate(tx_reconst)
    print(f"\n   Hash Reconstruido: {hash_reconst}")

    if hash_orig == hash_reconst:
        print("\n🎉 ¡ÉXITO! LOS HASHES COINCIDEN. El sistema es consistente.")
    else:
        print("\n💀 FALLO: LOS HASHES SON DIFERENTES. Revisa las diferencias marcadas con ❌.")

if __name__ == "__main__":
    main()