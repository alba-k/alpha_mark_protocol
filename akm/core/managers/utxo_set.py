# akm/core/managers/utxo_set.py
'''
class UTXOSet:
    Fuente de verdad para calcular saldos y validar que una moneda existe 
    antes de gastarla. Su única responsabilidad es mantener el estado UNSPENT.

    Attributes::
        _utxos (Dict[str, TxOutput]): Mapa interno { "tx_hash:index" -> TxOutput }.

    Methods::
        add_outputs(tx_hash, outputs) -> None:
            Registra nuevas monedas (UTXOs) al sistema.
        remove_inputs(inputs) -> None:
            Consume monedas existentes (las marca como gastadas).
        get_utxo_by_reference(prev_tx_hash, output_index) -> Optional[TxOutput]:
            Busca una moneda específica.
        get_balance_for_address(address) -> int:
            Calcula el saldo total de una dirección.
        get_total_circulating_supply() -> int:
            Calcula el suministro total de monedas en circulación.
'''

import logging
from typing import Dict, List, Optional

# Importamos las estructuras de valor definidas
from akm.core.models.tx_output import TxOutput
from akm.core.models.tx_input import TxInput

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='[UTXOSet] %(message)s')

class UTXOSet:

    def __init__(self):
        self._utxos: Dict[str, TxOutput] = {}

    def add_outputs(self, tx_hash: str, outputs: List[TxOutput]) -> None:
        if not tx_hash:
            raise ValueError("UTXOSet: Se requiere un hash de transacción válido para añadir outputs.")

        for index, output in enumerate(outputs):
            key = f"{tx_hash}:{index}"
            
            self._utxos[key] = output
            logging.debug(f"UTXO Registrado: {key} -> {output.value_alba} ALBA")

    def remove_inputs(self, inputs: List[TxInput]) -> None:
        for inp in inputs:
            key = f"{inp.previous_tx_hash}:{inp.output_index}"
            
            if key in self._utxos:
                del self._utxos[key]
                logging.debug(f"UTXO Consumido: {key}")
            else:
                logging.warning(f"CRÍTICO: Intento de gastar UTXO no existente o ya gastado: {key}")

    def get_utxo_by_reference(self, prev_tx_hash: str, output_index: int) -> Optional[TxOutput]:
        key = f"{prev_tx_hash}:{output_index}"
        return self._utxos.get(key)

    def get_balance_for_address(self, address: str) -> int:
        balance = 0
        
        for utxo in self._utxos.values():
            if utxo.script_pubkey == address:
                balance += utxo.value_alba
                
        return balance

    def get_total_circulating_supply(self) -> int:
        return sum(utxo.value_alba for utxo in self._utxos.values())