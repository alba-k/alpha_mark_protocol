# akm/core/models/transaction.py
from typing import List, Dict, Any, Optional
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput
from akm.core.utils.monetary import Monetary 

# Importación diferida para tipado estático (evita ciclos en runtime)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # Esto solo lo ve el linter, no Python en ejecución
    pass

class Transaction:
    """
    Representa una transacción en la red Alpha Mark.
    Soporta Scripting (bytes) y cálculo de Hash para firmas (SIGHASH).
    
    INVARIANTE DE CLASE:
    - Todos los campos están estrictamente tipados.
    - Los montos son enteros (Albas).
    """

    def __init__(
        self,
        tx_hash: str, 
        timestamp: int,
        inputs: Optional[List[TxInput]] = None,
        outputs: Optional[List[TxOutput]] = None,
        fee: int = 0 
    ):
        # --- 1. VALIDACIÓN ESTRICTA DE TIPOS (Runtime) ---
        if not isinstance(tx_hash, str): # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"Transaction: 'tx_hash' debe ser str. Recibido: {type(tx_hash).__name__}")
        
        if not isinstance(timestamp, int): # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"Transaction: 'timestamp' debe ser int. Recibido: {type(timestamp).__name__}")
        
        if not isinstance(fee, int): # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"Transaction: 'fee' debe ser int (Albas). Recibido: {type(fee).__name__}")
        
        # Validar listas (si no son None)
        if inputs is not None and not isinstance(inputs, list): # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"Transaction: 'inputs' debe ser una lista. Recibido: {type(inputs).__name__}")
            
        if outputs is not None and not isinstance(outputs, list): # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"Transaction: 'outputs' debe ser una lista. Recibido: {type(outputs).__name__}")

        # --- 2. VALIDACIONES DE LÓGICA DE NEGOCIO ---
        if fee < 0:
            raise ValueError("Transaction: El fee no puede ser negativo.")

        # --- 3. ASIGNACIÓN ---
        self._inputs: List[TxInput] = inputs if inputs is not None else []
        self._outputs: List[TxOutput] = outputs if outputs is not None else []
        
        self._tx_hash: str = tx_hash
        self._timestamp: int = timestamp
        self._fee: int = fee

    # --- PROPIEDADES (Getters) ---
    @property
    def tx_hash(self) -> str: return self._tx_hash
    @property
    def inputs(self) -> List[TxInput]: return self._inputs[:] # Copia defensiva
    @property
    def outputs(self) -> List[TxOutput]: return self._outputs[:] # Copia defensiva
    @property
    def timestamp(self) -> int: return self._timestamp
    @property
    def fee(self) -> int: return self._fee

    @property
    def fee_akm_display(self) -> str:
        """Formatea el fee para visualización humana."""
        val = Monetary.to_akm(self._fee)
        return f"{val:.8f}"

    @property
    def total_output_albas(self) -> int:
        """Suma total de valor transferido (sin fee)."""
        return sum(out.value_alba for out in self._outputs)

    @property
    def is_coinbase(self) -> bool:
        """Detecta si es una transacción de recompensa de minería."""
        if len(self._inputs) != 1: return False
        inp = self._inputs[0]
        # Validación Coinbase estándar: Hash nulo y índice máximo
        return inp.previous_tx_hash == "0" * 64 and inp.output_index == 0xFFFFFFFF

    def set_final_hash(self, new_hash: str) -> None:
        """Permite establecer el hash después de calcularlo."""
        if not isinstance(new_hash, str): # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("El hash debe ser un string.")
        self._tx_hash = new_hash

    def get_hash_for_signature(self, input_index: int, connected_script: Optional[bytes] = None) -> bytes:
        """
        🔥 CRÍTICO PARA SCRIPTING:
        Calcula el hash de la transacción 'recortada' para firmar (SIGHASH_ALL).
        """
        # Importación local para evitar ciclos (Transaction <-> Hasher)
        from akm.core.services.transaction_hasher import TransactionHasher

        # 🔥 CORRECCIÓN: Tipado explícito de la lista para evitar "partially unknown"
        temp_inputs: List[TxInput] = []
        
        for i, inp in enumerate(self._inputs):
            # Por defecto, script vacío (bytes)
            script_to_use: bytes = b''
            
            # Si estamos firmando ESTE input, inyectamos el script del output conectado (pubkey)
            if i == input_index and connected_script:
                script_to_use = connected_script
            
            # Clonamos el input con el script temporal
            temp_inputs.append(TxInput(
                previous_tx_hash=inp.previous_tx_hash,
                output_index=inp.output_index,
                script_sig=script_to_use # TxInput ya valida que esto sea bytes
            ))

        # 2. Crear Transacción Temporal para hashear
        temp_tx = Transaction(
            tx_hash="", # Irrelevante para el cálculo del hash de firma
            timestamp=self._timestamp,
            inputs=temp_inputs,
            outputs=self._outputs, # Los outputs se mantienen
            fee=self._fee
        )

        # 3. Calcular Hash
        # TransactionHasher devuelve str (hex), convertimos a bytes
        tx_hash_hex: str = TransactionHasher.calculate(temp_tx)
        return bytes.fromhex(tx_hash_hex)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa la transacción para la red P2P.
        Convierte tipos complejos (bytes) a formatos transmisibles (hex/str).
        """
        return {
            "tx_hash": self._tx_hash,
            "inputs": [inp.to_dict() for inp in self._inputs],
            "outputs": [out.to_dict() for out in self._outputs],
            "timestamp": self._timestamp,
            "fee": str(self._fee) # Importante: Int -> Str para evitar problemas de precisión JSON
        }