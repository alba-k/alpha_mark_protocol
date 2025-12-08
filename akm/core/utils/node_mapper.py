# akm/core/utils/node_mapper.py
from typing import Dict, Any, List
from akm.core.models.block import Block
from akm.core.models.transaction import Transaction
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput

class NodeMapper:
    """
    Utility para convertir Diccionarios (JSON) <-> Objetos de Dominio.
    Asegura que los tipos (str vs bytes) se manejen correctamente al deserializar.
    """

    @staticmethod
    def reconstruct_block(data: Dict[str, Any]) -> Block:
        transactions = [
            NodeMapper.reconstruct_transaction(tx_data) 
            for tx_data in data.get("transactions", [])
        ]
        
        return Block(
            index=int(data["index"]),
            timestamp=int(data["timestamp"]),
            previous_hash=str(data["previous_hash"]),
            bits=str(data["bits"]),
            merkle_root=str(data["merkle_root"]),
            nonce=int(data["nonce"]),
            block_hash=str(data["hash"]),
            transactions=transactions
        )

    @staticmethod
    def reconstruct_transaction(data: Dict[str, Any]) -> Transaction:
        inputs: List[TxInput] = []
        for inp in data.get("inputs", []):
            # ⚡ CORRECCIÓN: Convertir script_sig de STR (JSON) a BYTES (Modelo)
            sig_val = inp.get("script_sig", "")
            if isinstance(sig_val, str):
                sig_val = sig_val.encode('utf-8')
                
            inputs.append(TxInput(
                previous_tx_hash=str(inp["previous_tx_hash"]),
                output_index=int(inp["output_index"]),
                script_sig=sig_val
            ))

        outputs: List[TxOutput] = []
        for out in data.get("outputs", []):
            # ⚡ CORRECCIÓN: Convertir script_pubkey de STR (JSON) a BYTES (Modelo)
            pub_val = out.get("script_pubkey", "")
            if isinstance(pub_val, str):
                pub_val = pub_val.encode('utf-8')
                
            # value_alba viene como string en el JSON para precisión, convertir a int
            outputs.append(TxOutput(
                value_alba=int(out["value_alba"]),
                script_pubkey=pub_val
            ))

        tx = Transaction(
            tx_hash=str(data["tx_hash"]),
            timestamp=int(data["timestamp"]),
            inputs=inputs,
            outputs=outputs,
            fee=int(data.get("fee", 0))
        )
        return tx