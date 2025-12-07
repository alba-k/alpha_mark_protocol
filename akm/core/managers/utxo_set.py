# akm/core/managers/utxo_set.py
'''
class UTXOSet:
    Fuente de verdad para calcular saldos y validar que una moneda existe 
    antes de gastarla. Su única responsabilidad es mantener el estado UNSPENT.

    Methods::
        add_outputs, remove_inputs, get_utxo_by_reference, get_balance_for_address, 
        get_total_circulating_supply, clear.
        get_utxos_for_address: Retorna lista detallada para construcción de TXs.
'''

import logging
from typing import Dict, List, Optional, Any

from akm.core.models.tx_output import TxOutput
from akm.core.models.tx_input import TxInput

logging.basicConfig(level=logging.INFO, format='[UTXOSet] %(message)s')

class UTXOSet:

    def __init__(self):
        # Key format: "tx_hash:output_index"
        self._utxos: Dict[str, TxOutput] = {}

    def add_outputs(self, tx_hash: str, outputs: List[TxOutput]) -> None:
        if not tx_hash:
            raise ValueError("UTXOSet: Se requiere un hash de transacción válido.")

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

    def get_utxos_for_address(self, address: str) -> List[Dict[str, Any]]:
        """
        Retorna la lista detallada de UTXOs propiedad de una dirección.
        Esencial para que la Wallet construya transaccionexs.
        """
        user_utxos: List[Dict[str, Any]] = []
        
        for key, output in self._utxos.items():
            if output.script_pubkey == address:
                tx_hash, index_str = key.split(':')
                
                user_utxos.append({
                    "tx_hash": tx_hash,
                    "output_index": int(index_str),
                    "amount": output.value_alba,
                    "output_object": output
                })
        return user_utxos

    def get_total_circulating_supply(self) -> int:
        return sum(utxo.value_alba for utxo in self._utxos.values())

    def clear(self) -> None:
        """
        Vacia completamente el conjunto de UTXOs.
        Este método es crítico para la estrategia de reconstrucción de estado (Chain Reorg).
        """
        self._utxos.clear()
        logging.info("UTXO Set vaciado completamente.")