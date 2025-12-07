# akm/infra/persistence/sqlite/sqlite_blockchain_repository.py
import json
import logging
from typing import Optional, List, Any, Dict, Tuple, cast

# Interfaces y Modelos
from akm.core.interfaces.i_repository import IBlockchainRepository
from akm.core.models.block import Block
from akm.core.models.transaction import Transaction
from akm.core.models.tx_input import TxInput
from akm.core.models.tx_output import TxOutput

# Infra
from akm.infra.persistence.database_manager import DatabaseManager

class SqliteBlockchainRepository(IBlockchainRepository):
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.conn = self.db_manager.get_connection()

    def save_block(self, block: Block) -> None:
        try:
            txs_data = [tx.to_dict() for tx in block.transactions]
            txs_json = json.dumps(txs_data)

            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO blocks 
                (block_index, block_hash, previous_hash, timestamp, bits, nonce, merkle_root, data_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                block.index, 
                block.hash, 
                block.previous_hash, 
                block.timestamp, 
                block.bits, 
                block.nonce, 
                block.merkle_root,
                txs_json
            ))
            
            self.conn.commit()
            logging.info(f"💾 [SQLite] Bloque #{block.index} guardado.")
            
        except Exception as e:
            logging.error(f"Error crítico guardando en SQLite: {e}")
            self.conn.rollback()
            raise e

    def get_last_block(self) -> Optional[Block]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM blocks ORDER BY block_index DESC LIMIT 1')
        row = cursor.fetchone()
        return self._map_row_to_block(row) if row else None

    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM blocks WHERE block_hash = ?', (block_hash,))
        row = cursor.fetchone()
        return self._map_row_to_block(row) if row else None

    def get_blocks_range(self, start_index: int, limit: int) -> List[Block]:
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM blocks WHERE block_index >= ? ORDER BY block_index ASC LIMIT ?', 
            (start_index, limit)
        )
        rows = cursor.fetchall()
        return [self._map_row_to_block(row) for row in rows]

    def count(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM blocks')
        result = cursor.fetchone()
        return result[0] if result else 0

    def _map_row_to_block(self, row: Tuple[Any, ...]) -> Block:
        idx = int(row[0])
        b_hash = str(row[1])
        prev_hash = str(row[2])
        ts = int(row[3])
        bits = str(row[4])
        nonce = int(row[5])
        merkle = str(row[6])
        data_json = str(row[7])
        
        raw_txs = cast(List[Dict[str, Any]], json.loads(data_json))
        transactions: List[Transaction] = []
        
        for tx_dict in raw_txs:
            inputs = [
                TxInput(str(i['previous_tx_hash']), int(i['output_index']), str(i['script_sig'])) 
                for i in tx_dict['inputs']
            ]
            outputs = [
                TxOutput(int(o['value_alba']), str(o['script_pubkey'])) 
                for o in tx_dict['outputs']
            ]
            
            tx = Transaction(
                tx_hash=str(tx_dict['tx_hash']),
                timestamp=int(tx_dict['timestamp']),
                inputs=inputs,
                outputs=outputs,
                fee=int(tx_dict.get('fee', 0))
            )
            if hasattr(tx, 'set_final_hash'):
                tx.set_final_hash(str(tx_dict['tx_hash']))
                
            transactions.append(tx)

        return Block(
            index=idx,
            timestamp=ts,
            previous_hash=prev_hash,
            bits=bits,
            merkle_root=merkle,
            nonce=nonce,
            block_hash=b_hash,
            transactions=transactions
        )