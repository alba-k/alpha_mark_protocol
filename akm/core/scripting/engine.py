# core/scripting/engine.py
import logging
from typing import List, Callable, Dict, Any

from akm.core.scripting.opcodes import Opcodes
from akm.core.utils.crypto_utility import CryptoUtility

# Configurar logs
logger = logging.getLogger(__name__)

class ScriptError(Exception):
    """Excepción personalizada para fallos en la ejecución del script."""
    pass

class ScriptEngine:
    """
    Motor de ejecución de scripts basado en pila (Stack Machine).
    Implementa un subconjunto del lenguaje de scripting de Bitcoin.
    """

    def __init__(self):
        self.stack: List[bytes] = []
        # Mapeo de Opcodes a métodos (Patrón Dispatcher)
        self._operations: Dict[int, Callable[[], None]] = {
            Opcodes.OP_DUP: self._op_dup,
            Opcodes.OP_HASH160: self._op_hash160,
            Opcodes.OP_EQUALVERIFY: self._op_equalverify,
            Opcodes.OP_CHECKSIG: self._op_checksig,
            Opcodes.OP_DROP: self._op_drop,
            Opcodes.OP_TRUE: self._op_true,
            # Aquí puedes registrar nuevos opcodes fácilmente
        }
        
        # Contexto de ejecución actual (se reinicia en cada execute)
        self._current_tx = None
        self._current_input_index = 0

    def execute(self, script_sig: bytes, script_pubkey: bytes, transaction: Any, tx_input_index: int) -> bool:
        """
        Ejecuta la combinación de ScriptSig + ScriptPubKey.
        Retorna True si la ejecución es exitosa y el stack termina con True.
        """
        # 1. Reiniciar estado
        self.stack.clear()
        self._current_tx = transaction
        self._current_input_index = tx_input_index

        # 2. Combinar scripts
        full_script = script_sig + script_pubkey
        
        try:
            pointer = 0
            while pointer < len(full_script):
                opcode = full_script[pointer]

                # --- CASO A: PUSHDATA (Datos puros) ---
                # Si es un byte entre 0x01 y 0x4b, empujamos bytes al stack
                if 0x01 <= opcode <= 0x4b:
                    n_bytes = opcode
                    # Validación de límites
                    if pointer + 1 + n_bytes > len(full_script):
                        raise ScriptError("PUSHDATA fuera de límites")
                        
                    data = full_script[pointer + 1 : pointer + 1 + n_bytes]
                    self._push(data)
                    pointer += 1 + n_bytes
                    continue

                # --- CASO B: EJECUCIÓN DE OPCODES ---
                pointer += 1  # Avanzar puntero antes de ejecutar

                if opcode in self._operations:
                    operation = self._operations[opcode]
                    operation()  # Ejecutar lógica encapsulada
                else:
                    # Opcodes desconocidos o no implementados fallan inmediatamente
                    logger.error(f"Opcode desconocido: {opcode} ({Opcodes.get_name(opcode)})")
                    return False

            # --- VALIDACIÓN FINAL ---
            if len(self.stack) == 0:
                return False
            
            # El elemento superior debe ser True (o no cero/vacío)
            top = self.stack[-1]
            if top == b'\x01' or top == b'\x00\x01' or (len(top) > 0 and any(top)): # Lógica booleana laxa
                return True
            return False

        except ScriptError as e:
            logger.warning(f"Script falló controladamente: {e}")
            return False
        except Exception as e:
            logger.error(f"Error crítico en ScriptEngine: {e}", exc_info=True)
            return False
        finally:
            # Limpiar referencias para evitar fugas de memoria
            self._current_tx = None

    # --- MÉTODOS DE MANIPULACIÓN DE STACK (Helpers) ---

    def _push(self, data: bytes):
        self.stack.append(data)

    def _pop(self) -> bytes:
        if not self.stack:
            raise ScriptError("Stack Underflow (Intento de leer pila vacía)")
        return self.stack.pop()

    # --- IMPLEMENTACIÓN DE OPCODES (Lógica pura) ---

    def _op_true(self):
        self._push(b'\x01')

    def _op_drop(self):
        self._pop()

    def _op_dup(self):
        val = self._pop()
        self._push(val)
        self._push(val)

    def _op_hash160(self):
        element = self._pop()
        hashed = CryptoUtility.hash160(element)
        self._push(hashed)

    def _op_equalverify(self):
        elem1 = self._pop()
        elem2 = self._pop()
        if elem1 != elem2:
            raise ScriptError("OP_EQUALVERIFY falló: Elementos no coinciden")

    def _op_checksig(self):
        pub_key_bytes = self._pop()
        signature_bytes = self._pop()
        
        # Lógica de verificación delegada
        if self._verify_signature_logic(signature_bytes, pub_key_bytes):
            self._push(b'\x01')  # Éxito
        else:
            # En Bitcoin, CheckSig fallido no siempre detiene el script, 
            # pero suele pushear False. Aquí somos estrictos para simplificar.
            # self._push(b'') # Descomentar para comportamiento permisivo
            raise ScriptError("OP_CHECKSIG falló: Firma inválida")

    def _verify_signature_logic(self, signature: bytes, pub_key: bytes) -> bool:
        """Lógica interna de verificación criptográfica"""
        try:
            # Requerimos que la Transacción tenga el método get_hash_for_signature
            # Esto es vital para saber QUÉ estamos firmando
            tx_hash_for_sig = self._current_tx.get_hash_for_signature(self._current_input_index)
            
            return CryptoUtility.verify_signature(
                public_key_bytes=pub_key,
                signature_bytes=signature,
                message_bytes=tx_hash_for_sig
            )
        except AttributeError:
            logger.critical("La transacción no tiene método 'get_hash_for_signature'")
            return False
        except Exception as e:
            logger.debug(f"Fallo criptográfico interno: {e}")
            return False