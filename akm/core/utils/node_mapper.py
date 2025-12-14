# akm/core/utils/node_mapper.py

import logging
from typing import Dict, Any, List

# Modelos
from akm.core.models.block import Block
from akm.core.models.transaction import Transaction
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput

logger = logging.getLogger(__name__)

class NodeMapper:

    @staticmethod
    def reconstruct_block(data: Dict[str, Any]) -> Block:
        try:
            # 1. DETECCIÓN DE ESTRUCTURA
            # Si existe la clave "header", los datos metadatos están ahí dentro.
            # Si no, asumimos que están en la raíz (compatibilidad legacy).
            if "header" in data:
                header_data = data["header"]
                txs_data = data.get("transactions", [])
            else:
                header_data = data
                txs_data = data.get("transactions", [])

            # 2. Reconstruir Transacciones
            transactions = [
                NodeMapper.reconstruct_transaction(tx_data) 
                for tx_data in txs_data
            ]
            
            # 3. Normalización de campos clave
            # Hash: puede venir como 'hash' o 'block_hash'
            b_hash = header_data.get("hash") or header_data.get("block_hash") or ""
            
            # Bits/Dificultad: puede venir como 'bits' o 'difficulty'
            bits_val = str(header_data.get("bits") or header_data.get("difficulty") or "")

            # 4. Crear el Objeto Block
            block = Block(
                index=int(header_data["index"]),
                timestamp=int(header_data["timestamp"]),
                previous_hash=str(header_data["previous_hash"]),
                bits=bits_val,
                merkle_root=str(header_data["merkle_root"]),
                nonce=int(header_data["nonce"]),
                block_hash=str(b_hash),
                transactions=transactions
            )

            # logger.debug(f"Datos: Bloque #{block.index} reconstruido correctamente.")
            return block

        except KeyError as e:
            logger.error(f"❌ Falta campo obligatorio en el JSON del bloque: {e}")
            raise
        except Exception as e:
            logger.exception(f"❌ Fallo al reconstruir Block desde el payload: {e}")
            raise

    @staticmethod
    def reconstruct_transaction(data: Dict[str, Any]) -> Transaction:
        try:
            # Procesamiento de Inputs
            inputs: List[TxInput] = []
            for inp in data.get("inputs", []):
                # Decodificación crítica de HEX a Bytes
                script_sig = NodeMapper._hex_to_bytes(inp.get("script_sig", ""))
                
                inputs.append(TxInput(
                    previous_tx_hash=str(inp.get("previous_tx_hash") or inp.get("prev_hash") or ""),
                    output_index=int(inp.get("output_index") or inp.get("index") or 0),
                    script_sig=script_sig
                ))

            # Procesamiento de Outputs
            outputs: List[TxOutput] = []
            for out in data.get("outputs", []):
                script_pubkey = NodeMapper._hex_to_bytes(out.get("script_pubkey", ""))
                
                outputs.append(TxOutput(
                    value_alba=int(out.get("value_alba") or out.get("amount") or 0),
                    script_pubkey=script_pubkey
                ))

            return Transaction(
                tx_hash=str(data.get("tx_hash", "")),
                timestamp=int(data.get("timestamp", 0)),
                inputs=inputs,
                outputs=outputs,
                fee=int(data.get("fee", 0))
            )

        except Exception:
            logger.exception("Error mapeando transacción desde datos serializados")
            raise

    @staticmethod
    def _hex_to_bytes(hex_val: Any) -> bytes:
        """Helper para normalizar datos hexadecimales a bytes reales."""
        if not hex_val:
            return b""
        
        if isinstance(hex_val, str):
            try:
                # Intentamos decodificar hex si parece hex limpio
                # (Nota: a veces viene texto plano si lo guardamos como utf-8 antes)
                return hex_val.encode('utf-8') 
            except ValueError:
                return hex_val.encode('utf-8')
        
        return b""