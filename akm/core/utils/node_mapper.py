# akm/core/utils/node_mapper.py
from typing import Dict, Any, List, cast
from akm.core.models.block import Block
from akm.core.models.transaction import Transaction
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput

class NodeMapper:
    """
    [SRP] Especialista en convertir datos crudos de red (JSON/Dict)
    a objetos de dominio ricos (Block, Transaction).
    """

    @staticmethod
    def reconstruct_transaction(data: Dict[str, Any]) -> Transaction:
        """Reconstruye una Transacción completa desde un diccionario."""
        inputs = [
            TxInput(str(i['previous_tx_hash']), int(i['output_index']), str(i['script_sig']))
            for i in data['inputs']
        ]
        
        outputs = [
            TxOutput(int(o['value_alba']), str(o['script_pubkey']))
            for o in data['outputs']
        ]
        
        # Uso seguro de .get() para fee
        fee_val = int(data.get('fee', 0))

        tx = Transaction(
            tx_hash=str(data['tx_hash']),
            timestamp=int(data['timestamp']),
            inputs=inputs,
            outputs=outputs,
            fee=fee_val
        )
        
        # Aseguramos la integridad del hash original
        if hasattr(tx, 'set_final_hash'):
            tx.set_final_hash(str(data['tx_hash']))
            
        return tx

    @staticmethod
    def reconstruct_block(data: Dict[str, Any]) -> Block:
        """Reconstruye un Bloque completo y sus transacciones."""
        raw_txs = cast(List[Dict[str, Any]], data['transactions'])
        
        # Reconstrucción recursiva
        txs = [NodeMapper.reconstruct_transaction(tx_data) for tx_data in raw_txs]
        
        return Block(
            index=int(data['index']),
            timestamp=int(data['timestamp']),
            previous_hash=str(data['previous_hash']),
            bits=str(data['bits']),
            merkle_root=str(data['merkle_root']),
            nonce=int(data['nonce']),
            block_hash=str(data['hash']),
            transactions=txs
        )