# akm/core/scripting/engine.py

import logging
from typing import List, Callable, Dict, Any, Optional

from akm.core.scripting.opcodes import Opcodes
from akm.core.utils.crypto_utility import CryptoUtility

logger = logging.getLogger(__name__)

class ScriptError(Exception):
    """Excepción para errores controlados de lógica de script."""
    pass

SignatureVerifier = Callable[[bytes, bytes, Any, int], bool]

class ScriptEngine:
    def __init__(self, signature_verifier: Optional[SignatureVerifier] = None) -> None:
        try:
            self.stack: List[bytes] = []
            self._operations: Dict[int, Callable[[], None]] = {
                Opcodes.OP_DUP: self._op_dup,
                Opcodes.OP_HASH160: self._op_hash160,
                Opcodes.OP_EQUALVERIFY: self._op_equalverify,
                Opcodes.OP_CHECKSIG: self._op_checksig,
                Opcodes.OP_DROP: self._op_drop,
                Opcodes.OP_TRUE: self._op_true,
            }
            self._signature_verifier = signature_verifier
            self._current_tx = None
            self._current_input_index = 0
            
            logger.info("Motor de scripts (VM) listo.")
        except Exception:
            logger.exception("Error al inicializar ScriptEngine")

    def execute(self, script_sig: bytes, script_pubkey: bytes, transaction: Any, tx_input_index: int) -> bool:
        self.stack.clear()
        self._current_tx = transaction
        self._current_input_index = tx_input_index
        
        # El script completo es la unión del permiso (sig) y el candado (pubkey)
        full_script = script_sig + script_pubkey
        
        try:
            pointer = 0
            while pointer < len(full_script):
                opcode = full_script[pointer]

                # --- CASO A: PUSHDATA (0x01 a 0x4b) ---
                if 0x01 <= opcode <= 0x4b:
                    n_bytes = opcode
                    if pointer + 1 + n_bytes > len(full_script):
                        raise ScriptError("PUSHDATA fuera de límites.")
                    
                    data = full_script[pointer + 1 : pointer + 1 + n_bytes]
                    self._push(data)
                    pointer += 1 + n_bytes
                    continue

                # --- CASO B: OPCODES ---
                pointer += 1
                if opcode in self._operations:
                    self._operations[opcode]()
                else:
                    logger.info(f"Script fallido: Opcode {hex(opcode)} desconocido.")
                    return False

            # --- VALIDACIÓN FINAL ---
            if not self.stack:
                return False
            
            # El tope de la pila debe ser distinto de cero para ser válido
            top = self.stack[-1]
            success = (top == b'\x01') or (len(top) > 0 and any(b != 0 for b in top))
            
            if success:
                logger.info(f"Script verificado para input {tx_input_index}.")
            else:
                logger.info(f"Script fallido (Tope de pila falso) en input {tx_input_index}.")
                
            return success

        except ScriptError as e:
            logger.info(f"Script inválido: {e}")
            return False
        except Exception:
            logger.exception("Error crítico en la ejecución del script")
            return False
        finally:
            self._current_tx = None

    # --- MANIPULACIÓN DE PILA ---
    def _push(self, data: bytes):
        self.stack.append(data)

    def _pop(self) -> bytes:
        if not self.stack:
            raise ScriptError("Stack Underflow (Intento de pop en pila vacía).")
        return self.stack.pop()

    # --- IMPLEMENTACIÓN DE OPCODES ---
    def _op_true(self): self._push(b'\x01')
    def _op_drop(self): self._pop()
    def _op_dup(self):
        val = self._pop()
        self._push(val)
        self._push(val)

    def _op_equalverify(self):
        elem1 = self._pop()
        elem2 = self._pop()
        if elem1 != elem2:
            raise ScriptError("OP_EQUALVERIFY: Elementos no coinciden.")

    def _op_hash160(self):
        element = self._pop()
        # CryptoUtility maneja str o bytes, pero normalizamos aquí para seguridad
        hashed_hex = CryptoUtility.hash160(element)
        self._push(bytes.fromhex(hashed_hex))

    def _op_checksig(self):
        if self._signature_verifier is None:
            raise ScriptError("Falta verificador de firmas inyectado.")

        pub_key_bytes = self._pop()
        signature_bytes = self._pop()
        
        # Delegamos la verificación criptográfica pesada al servicio externo
        is_valid = self._signature_verifier(
            signature_bytes, 
            pub_key_bytes, 
            self._current_tx, 
            self._current_input_index
        )

        if not is_valid:
            raise ScriptError("OP_CHECKSIG: Firma criptográfica inválida.")
        
        self._push(b'\x01')