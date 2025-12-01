# akm/tests/unit/test_wallet_manager.py
'''
Test Suite para WalletManager:
    Verifica la orquestación de la lógica de negocio aislando la criptografía.

    Functions::
        test_sign_transaction_hash_uses_mock_implementation():
            Prueba de Polimorfismo e Inyección de Dependencias.
        test_wallet_manager_initialization_succeeds():
            Prueba de integridad de inicialización y obtención de identidad.
'''

import logging

# Importaciones de las clases a probar
from akm.core.managers.wallet_manager import WalletManager
from akm.tests.mocks.mock_signer import MockSigner

# Desactivar logs para mantener la salida de pruebas limpia
logging.basicConfig(level=logging.CRITICAL)

# Hash de prueba (str hexadecimal)
TEST_HASH = "A3B2C1D4E5F67890"

def test_sign_transaction_hash_uses_mock_implementation():
    """
    Verifica que el WalletManager use la implementación inyectada (Mock) 
    para firmar, probando el Polimorfismo y la Inversión de Dependencias (DIP).
    """
    # 1. Crear el objeto Mock que implementa la interfaz ISigner
    # Este Mock ya trae la clave pública y la lógica de firma simulada.
    mock_signer = MockSigner()
    
    # 2. Inyección de Dependencias (El Mock sustituye al SoftwareSigner real)
    # WalletManager acepta el Mock porque cumple con el contrato ISigner.
    # NOTA: No pasamos 'public_key' aparte, el manager la extrae del signer.
    wallet = WalletManager(signer=mock_signer)
    
    # 3. Ejecución: WalletManager delega la llamada a mock_signer.sign()
    signature = wallet.sign_transaction_hash(TEST_HASH)
    
    # 4. Verificación: La firma debe ser el valor fijo del Mock.
    # Comprobamos contra la constante definida en el Mock.
    assert signature == MockSigner.MOCK_SIGNATURE
    
    # Doble verificación del valor literal para asegurar integridad del test
    assert signature == "TEST_MOCKED_SIGNATURE_AKM_0123456789ABCDEF"

def test_wallet_manager_identity_retrieval():
    """
    Verifica que el WalletManager pueda obtener correctamente la identidad 
    pública del Signer inyectado.
    """
    # 1. Configuración (Arrange)
    mock_signer = MockSigner()
    wallet = WalletManager(signer=mock_signer)
    
    # 2. Ejecución (Act)
    public_key = wallet.get_public_key()
    
    # 3. Verificación (Assert)
    # Debe coincidir con la clave pública dummy definida en el Mock
    assert public_key == MockSigner.MOCK_PUBLIC_KEY
    assert public_key == "MOCK_PUB_KEY_02ABCDEF"