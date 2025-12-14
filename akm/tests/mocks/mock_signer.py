# akm/tests/mocks/mock_signer.py
'''
class MockSigner:
    Devuelve valores fijos y predecibles para verificar la lógica de negocio sin criptografía real.

    Methods::
        sign(tx_hash) -> str:
            Retorna una firma simulada fija para validar el flujo del Manager.
        get_public_key() -> str:
            Retorna una clave pública simulada constante.
'''

from akm.core.interfaces.i_signer import ISigner

class MockSigner(ISigner):

    # Constantes públicas para validación en tests
    MOCK_SIGNATURE: str = "TEST_MOCKED_SIGNATURE_AKM_0123456789ABCDEF"
    MOCK_PUBLIC_KEY: str = "MOCK_PUB_KEY_02ABCDEF"

    def sign(self, tx_hash: str) -> str:
        return self.MOCK_SIGNATURE

    def get_public_key(self) -> str:
        return self.MOCK_PUBLIC_KEY