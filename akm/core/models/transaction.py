# akm/core/models/transaction.py

import logging
from typing import List, Dict, Any, Optional

from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput
from akm.core.services.transaction_hasher import TransactionHasher

logger = logging.getLogger(__name__)

class Transaction:

    def __init__(
        self,
        tx_hash: str, 
        timestamp: int,
        inputs: Optional[List[TxInput]] = None,
        outputs: Optional[List[TxOutput]] = None,
        fee: int = 0 
    ) -> None:
        try:
            if fee < 0: 
                raise ValueError("Fee negativo.")

            self._inputs: List[TxInput] = inputs if inputs is not None else []
            self._outputs: List[TxOutput] = outputs if outputs is not None else []
            self._tx_hash: str = tx_hash
            self._timestamp: int = timestamp
            self._fee: int = fee

            if self._tx_hash:
                logger.debug(f"TX {self._tx_hash[:8]}... instanciada.")

        except Exception:
            logger.exception("Error al inicializar Transaction")

    # --- Getters ---
    @property
    def tx_hash(self) -> str: return self._tx_hash
    @property
    def inputs(self) -> List[TxInput]: return self._inputs[:]
    @property
    def outputs(self) -> List[TxOutput]: return self._outputs[:]
    @property
    def timestamp(self) -> int: return self._timestamp
    @property
    def fee(self) -> int: return self._fee
    
    @property
    def total_output_albas(self) -> int: 
        return sum(out.value_alba for out in self._outputs)
    
    @property
    def is_coinbase(self) -> bool:
        if len(self._inputs) != 1: return False
        inp = self._inputs[0]
        # Input nulo estándar: hash ceros y índice máximo
        return inp.previous_tx_hash == "0" * 64 and inp.output_index == 0xFFFFFFFF
    
    @tx_hash.setter
    def tx_hash(self, value: str):
        self._tx_hash = value

    def set_final_hash(self, new_hash: str) -> None:
        self._tx_hash = new_hash

    def get_hash_for_signature(self, input_index: int, connected_script: Optional[bytes] = None) -> bytes:
        """
        [FIX INTEGRIDAD DE PREV_HASH] Calcula el hash de la transacción para ser firmado (SIGHASH_ALL).
        """
        # 1. Creamos inputs temporales (Listado de copias)
        temp_inputs: List[TxInput] = []
        
        for i, inp in enumerate(self._inputs):
            script_to_use: bytes = b''
            
            # Solo copiamos el script si es el input que estamos firmando actualmente
            if i == input_index and connected_script:
                script_to_use = connected_script
            
            # [FIX CRÍTICO AQUÍ] Aseguramos que el previous_tx_hash sea consistente para el hasher.
            # Si es el input nulo de Coinbase, o si es vacío, debe ser 64 ceros.
            prev_hash = inp.previous_tx_hash
            if not prev_hash or prev_hash.lower() == '0' * 64:
                 prev_hash = '0' * 64

            # Creamos una copia del input para modificar el script_sig
            temp_inputs.append(TxInput(
                previous_tx_hash=prev_hash,
                output_index=inp.output_index,
                script_sig=script_to_use 
            ))

        # 2. Creamos la transacción temporal (TxID vacío)
        temp_tx = Transaction(
            tx_hash="",
            timestamp=self._timestamp,
            inputs=temp_inputs,
            outputs=self._outputs, 
            fee=self._fee
        )

        # 3. Calculamos el hash (que será la imagen a firmar)
        tx_hash_hex = TransactionHasher.calculate(temp_tx)
        
        # 4. Devolvemos los bytes del hash para la firma.
        return bytes.fromhex(tx_hash_hex)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la transacción para DB/Red."""
        return {
            "tx_hash": self._tx_hash,
            "inputs": [inp.to_dict() for inp in self._inputs],
            "outputs": [out.to_dict() for out in self._outputs],
            "timestamp": self._timestamp,
            "fee": self._fee 
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Transaction':
        """
        Reconstruye la Transacción desde DB o Red.
        [FIX]: Limpieza de tipos. Convierte Hex Strings a Bytes antes de crear el objeto.
        """
        inputs_list: List[TxInput] = []
        if 'inputs' in data:
            for inp_data in data['inputs']:
                # --- LIMPIEZA DE INPUTS ---
                # Si 'script_sig' viene como string (JSON Hex), lo pasamos a bytes reales
                if 'script_sig' in inp_data and isinstance(inp_data['script_sig'], str):
                    try:
                        # Convertimos en el diccionario antes de pasarlo al constructor
                        inp_data['script_sig'] = bytes.fromhex(inp_data['script_sig'])
                    except ValueError:
                        # Si falla, mantenemos el valor original (el validador lo rechazará luego)
                        logger.warning(f"⚠️ Script Sig inválido en input: {inp_data.get('script_sig', '')[:10]}...")

                inputs_list.append(TxInput.from_dict(inp_data))

        outputs_list: List[TxOutput] = []
        if 'outputs' in data:
            for out_data in data['outputs']:
                # --- LIMPIEZA DE OUTPUTS ---
                # Si 'script_pubkey' viene como string (JSON Hex), lo pasamos a bytes reales
                if 'script_pubkey' in out_data and isinstance(out_data['script_pubkey'], str):
                    try:
                        out_data['script_pubkey'] = bytes.fromhex(out_data['script_pubkey'])
                    except ValueError:
                        logger.warning(f"⚠️ Script Pubkey inválido en output: {out_data.get('script_pubkey', '')[:10]}...")

                outputs_list.append(TxOutput.from_dict(out_data))

        return Transaction(
            tx_hash=data.get('tx_hash', ''),
            timestamp=int(data.get('timestamp', 0)),
            inputs=inputs_list,
            outputs=outputs_list,
            fee=int(data.get('fee', 0))
        )