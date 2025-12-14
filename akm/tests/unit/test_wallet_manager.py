# akm/tests/unit/test_wallet_manager.py
'''
Test Suite para WalletManager:
    Verifica la orquestación de la lógica de negocio.
    Incluye pruebas unitarias con Mocks y una prueba de integración con Criptografía Real.

    Functions::
        test_sign_transaction_hash_uses_mock_implementation(): Prueba aislada (Mock).
        test_wallet_manager_identity_retrieval(): Prueba de identidad (Mock).
        test_wallet_manager_real_crypto_integration(): (NUEVO) Prueba con claves reales ECDSA.
'''

import sys
import os
import logging

# --- AJUSTE DE RUTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '../../..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Importaciones de Dominio
from akm.core.managers.wallet_manager import WalletManager

# Importaciones de Mocks e Infraestructura Real
from akm.tests.mocks.mock_signer import MockSigner
from akm.infra.crypto.software_signer import SoftwareSigner

# Desactivar logs para mantener la salida de pruebas limpia
logging.basicConfig(level=logging.CRITICAL)

# --- DATOS DE PRUEBA (MOCK) ---
TEST_HASH = "A3B2C1D4E5F67890"

# --- DATOS REALES (De wallet_identity_1.json) ---
# Usamos estos para probar que la librería criptográfica se integra bien
REAL_PRIVATE_KEY = "629baf943be1b82cc41ec75a21dac0355d88107ed1d2c3b61089eee4843457c8"
REAL_PUBLIC_KEY = "023a5061ad8e3db107ad736e7e02c399dad03fa5d474d4ad62a147a31a6e402bc1"

def test_sign_transaction_hash_uses_mock_implementation():
    """
    [UNITARIO] Verifica que el WalletManager use la implementación inyectada (Mock).
    """
    print(">> Ejecutando: test_sign_transaction_hash_uses_mock_implementation...")
    
    # 1. Arrange
    mock_signer = MockSigner()
    wallet = WalletManager(signer=mock_signer)
    
    # 2. Act
    signature = wallet.sign_transaction_hash(TEST_HASH)
    
    # 3. Assert
    assert signature == MockSigner.MOCK_SIGNATURE
    
    print("[SUCCESS] Firma delegada al Mock correctamente.\n")

def test_wallet_manager_identity_retrieval():
    """
    [UNITARIO] Verifica la obtención de identidad con Mock.
    """
    print(">> Ejecutando: test_wallet_manager_identity_retrieval...")
    
    mock_signer = MockSigner()
    wallet = WalletManager(signer=mock_signer)
    
    public_key = wallet.get_public_key()
    
    assert public_key == MockSigner.MOCK_PUBLIC_KEY
    
    print("[SUCCESS] Identidad Mock recuperada correctamente.\n")

def test_wallet_manager_real_crypto_integration():
    """
    [INTEGRACIÓN] Verifica el funcionamiento con SoftwareSigner y claves reales.
    Aquí probamos que la inyección de dependencias soporte la implementación real.
    """
    print(">> Ejecutando: test_wallet_manager_real_crypto_integration (REAL)...")
    
    # 1. Arrange: Inyectamos el SoftwareSigner real con una clave válida
    real_signer = SoftwareSigner(private_key_hex=REAL_PRIVATE_KEY)
    wallet = WalletManager(signer=real_signer)
    
    # 2. Act & Assert A: Verificar Identidad Pública
    # El WalletManager debe devolver la clave pública derivada matemáticamente de la privada
    derived_public_key = wallet.get_public_key()
    
    assert derived_public_key == REAL_PUBLIC_KEY
    print(f"   -> Clave Pública derivada correctamente: {derived_public_key[:10]}...")

    # 3. Act & Assert B: Firma Real ECDSA
    # Firmamos un hash real (debe ser 64 chars hex)
    # Usamos un hash dummy válido (32 bytes = 64 hex chars)
    tx_hash_real = "c9f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1"
    
    signature = wallet.sign_transaction_hash(tx_hash_real)
    
    # Verificaciones básicas de una firma DER hexadecimal
    assert isinstance(signature, str)
    assert len(signature) > 60 # Las firmas DER suelen ser largas (aprox 140 chars)
    # Verificar que es hexadecimal válido
    int(signature, 16) 
    
    print(f"   -> Firma Real generada exitosamente: {signature[:20]}...")
    print("[SUCCESS] Integración Criptográfica Real verificada.\n")

if __name__ == "__main__":
    print("==========================================")
    print("   TESTING WALLET MANAGER (MOCK & REAL)   ")
    print("==========================================\n")
    
    try:
        test_sign_transaction_hash_uses_mock_implementation()
        test_wallet_manager_identity_retrieval()
        test_wallet_manager_real_crypto_integration()
        
        print("==========================================")
        print("   TODOS LOS TESTS PASARON EXITOSAMENTE   ")
        print("==========================================")
    except AssertionError as e:
        print(f"\nFALLO DE ASERCIÓN: {e}")
    except Exception as e:
        print(f"\nERROR INESPERADO: {e}")