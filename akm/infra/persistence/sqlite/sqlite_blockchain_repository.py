# akm/infra/persistence/sqlite/sqlite_blockchain_repository.py
import json
import logging
from typing import Optional, List, Any, Dict, Tuple

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
            self._insert_block_cursor(self.conn.cursor(), block)
            self.conn.commit()
            logging.debug(f"💾 [SQLite] Bloque #{block.index} guardado.")
        except Exception as e:
            logging.error(f"Error crítico guardando bloque en SQLite: {e}")
            self.conn.rollback()
            raise e

    def save_blocks_atomic(self, blocks: List[Block]) -> None:
        if not blocks: return
        cursor = self.conn.cursor()
        try:
            for block in blocks:
                self._insert_block_cursor(cursor, block)
            self.conn.commit()
            logging.info(f"💾 [SQLite] Batch Save: {len(blocks)} bloques.")
        except Exception as e:
            logging.error(f"❌ Error en Batch Save: {e}")
            self.conn.rollback()
            raise e

    def _insert_block_cursor(self, cursor: Any, block: Block) -> None:
        txs_data = [tx.to_dict() for tx in block.transactions]
        txs_json = json.dumps(txs_data)

        cursor.execute('''
            INSERT OR REPLACE INTO blocks 
            (block_index, block_hash, previous_hash, timestamp, bits, nonce, merkle_root, data_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            block.index, block.hash, block.previous_hash, block.timestamp, 
            block.bits, block.nonce, block.merkle_root, txs_json
        ))

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
        res = cursor.fetchone()
        return res[0] if res[0] else 0

    def get_headers_range(self, start_hash: str, limit: int = 2000) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        start_index = 0
        if start_hash:
            cursor.execute('SELECT block_index FROM blocks WHERE block_hash = ?', (start_hash,))
            row = cursor.fetchone()
            if row: start_index = row[0] + 1

        cursor.execute('''
            SELECT block_index, block_hash, previous_hash, timestamp, bits, nonce, merkle_root 
            FROM blocks WHERE block_index >= ? ORDER BY block_index ASC LIMIT ?
        ''', (start_index, limit))
        
        headers: List[Dict[str, Any]] = []
        for r in cursor.fetchall():
            headers.append({
                "index": int(r[0]), "hash": self._ensure_str(r[1]), "prev_hash": self._ensure_str(r[2]),
                "timestamp": int(r[3]), "bits": self._ensure_str(r[4]), "nonce": int(r[5]), 
                "merkle_root": self._ensure_str(r[6])
            })
        return headers

    def _ensure_str(self, val: Any) -> str:
        if val is None: return ""
        if isinstance(val, bytes): return val.decode('utf-8')
        return str(val)

    def _map_row_to_block(self, row: Tuple[Any, ...]) -> Block:
        # Mapeo Básico
        idx, b_hash, prev_hash, ts, bits, nonce, merkle, data_json = row
        
        # Deserialización TXs
        raw_txs: List[Dict[str, Any]] = json.loads(self._ensure_str(data_json))
        transactions: List[Transaction] = []
        
        for tx_dict in raw_txs:
            inputs: List[TxInput] = [] 
            for i in tx_dict.get('inputs', []):
                # ScriptSig limpio
                sig_val = self._ensure_str(i.get('script_sig', ''))
                inputs.append(TxInput(
                    previous_tx_hash=self._ensure_str(i['previous_tx_hash']), 
                    output_index=int(i['output_index']), 
                    # El constructor de TxInput se encarga de convertir a bytes
                    script_sig=sig_val 
                ))
            
            outputs: List[TxOutput] = []
            for o in tx_dict.get('outputs', []):
                # ScriptPubKey limpio
                pub_val = self._ensure_str(o['script_pubkey'])
                outputs.append(TxOutput(
                    value_alba=int(o['value_alba']), 
                    # El constructor de TxOutput se encarga de convertir a bytes
                    script_pubkey=pub_val
                ))
            
            tx = Transaction(
                tx_hash=self._ensure_str(tx_dict['tx_hash']),
                timestamp=int(tx_dict['timestamp']),
                inputs=inputs,
                outputs=outputs,
                fee=int(tx_dict.get('fee', 0))
            )
            transactions.append(tx)

        return Block(
            index=idx, timestamp=ts, previous_hash=self._ensure_str(prev_hash),
            bits=self._ensure_str(bits), merkle_root=self._ensure_str(merkle),
            nonce=nonce, block_hash=self._ensure_str(b_hash),
            transactions=transactions
        )