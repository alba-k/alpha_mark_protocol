'''
Script Refactorizado: Generador de Identidad (SOLID Compliance)
Se ha eliminado la "God Class" dividiendo las responsabilidades en componentes especializados.

Components::
    IdentityService: Lógica de negocio para creación de claves.
    JsonVaultRepository: Lógica de infraestructura para guardado en disco.
    ConsolePresenter: Lógica de presentación visual (CORREGIDO: Muestra todos los datos).
    IdentityGeneratorApp: Orquestador (Controller).
'''

import sys
import os
import json
import datetime
from typing import Dict

# --- CONFIGURACIÓN DE RUTAS ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

from akm.infra.identity.bip39_service import BIP39Service
from akm.infra.identity.address_factory import AddressFactory
from akm.infra.crypto.software_signer import SoftwareSigner

# ---------------------------------------------------------
# 1. SERVICIO DE DOMINIO (Responsabilidad: CREAR)
# ---------------------------------------------------------
class IdentityService:
    '''
    Encapsula exclusivamente la lógica de negocio para generar una identidad.
    '''
    def create_new_identity(self) -> Dict[str, str]:
        service_bip39 = BIP39Service()
        mnemonico = service_bip39.generate_mnemonic()
        private_key = service_bip39.derive_master_private_key(mnemonico)
        
        signer = SoftwareSigner(private_key)
        public_key = signer.get_public_key()
        address = AddressFactory.create_from_public_key(public_key)

        return {
            "created_at": datetime.datetime.now().isoformat(),
            "mnemonic": mnemonico,
            "private_key": private_key,
            "public_key": public_key,
            "address": address
        }

# ---------------------------------------------------------
# 2. REPOSITORIO DE INFRAESTRUCTURA (Responsabilidad: GUARDAR)
# ---------------------------------------------------------
class JsonVaultRepository:
    '''
    Encapsula exclusivamente la lógica de persistencia en disco (JSON).
    '''
    def __init__(self, vault_folder_name: str = "security_vault"):
        self.vault_path = os.path.join(PROJECT_ROOT, vault_folder_name)

    def save(self, data: Dict[str, str]) -> str:
        self._ensure_directory_exists()
        full_path = self._generate_next_filename()
        
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
        return full_path

    def _ensure_directory_exists(self) -> None:
        if not os.path.exists(self.vault_path):
            os.makedirs(self.vault_path)

    def _generate_next_filename(self) -> str:
        counter = 1
        while True:
            filename = f"wallet_identity_{counter}.json"
            full_path = os.path.join(self.vault_path, filename)
            if not os.path.exists(full_path):
                return full_path
            counter += 1

# ---------------------------------------------------------
# 3. PRESENTADOR (Responsabilidad: MOSTRAR)
# ---------------------------------------------------------
class ConsolePresenter:
    '''
    Encapsula exclusivamente la lógica de salida por pantalla (UI).
    '''
    def show_header(self) -> None:
        print("\n==========================================")
        print("   GENERADOR DE IDENTIDAD (SOLID PRO)     ")
        print("==========================================\n")

    def show_process_start(self) -> None:
        print(">> Iniciando servicios de criptografía...")

    def show_success(self, data: Dict[str, str], filepath: str) -> None:
        # CORRECCIÓN: Ahora imprimimos explícitamente los 4 campos
        print(f"\n[1] FRASE DE RESPALDO (MNEMÓNICO):\n    {data['mnemonic']}")
        print(f"    (IMPORTANTE: Guarda estas palabras fuera de la PC)")
        
        print(f"\n[2] CLAVE PRIVADA (HEX):\n    {data['private_key']}")
        
        print(f"\n[3] DIRECCIÓN PÚBLICA (WALLET):\n    {data['address']}")
        
        # AQUÍ ESTÁ LA LÍNEA QUE FALTABA EN TU EJECUCIÓN ANTERIOR
        print(f"\n[4] CLAVE PÚBLICA (RAW):\n    {data['public_key']}")

        print("\n------------------------------------------")
        print(f"✅ IDENTIDAD GUARDADA CON ÉXITO:")
        print(f"   📂 {filepath}")
        print("------------------------------------------\n")

    def show_error(self, error: Exception) -> None:
        print(f"\n[ERROR CRÍTICO] {error}")

# ---------------------------------------------------------
# 4. APLICACIÓN PRINCIPAL (Responsabilidad: ORQUESTAR)
# ---------------------------------------------------------
class IdentityGeneratorApp:
    '''
    Controlador principal. Une las piezas sueltas.
    '''
    def __init__(self):
        self.service = IdentityService()
        self.repository = JsonVaultRepository()
        self.presenter = ConsolePresenter()

    def run(self) -> None:
        self.presenter.show_header()
        
        try:
            # 1. Crear
            self.presenter.show_process_start()
            identity_data = self.service.create_new_identity()

            # 2. Guardar
            filepath = self.repository.save(identity_data)

            # 3. Mostrar
            self.presenter.show_success(identity_data, filepath)

        except Exception as e:
            self.presenter.show_error(e)

if __name__ == "__main__":
    app = IdentityGeneratorApp()
    app.run()