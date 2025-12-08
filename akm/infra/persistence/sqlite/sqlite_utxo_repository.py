# akm/infra/persistence/sqlite/sqlite_utxo_repository.py
import logging
from typing import List, Optional, Dict, Any, Union
from akm.core.interfaces.i_utxo_repository import IUTXORepository
from akm.core.models.tx_output import TxOutput
from akm.infra.persistence.database_manager import DatabaseManager

class SqliteUTXORepository(IUTXORepository):

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.conn = self.db_manager.get_connection()
        self._create_table()

    def _create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS utxos (
                tx_hash TEXT,
                output_index INTEGER,
                amount INTEGER,
                address BLOB, 
                PRIMARY KEY (tx_hash, output_index)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_utxo_address ON utxos (address)')
        self.conn.commit()

    def add_utxo(self, tx_hash: str, index: int, output: TxOutput) -> None:
        try:
            cursor = self.conn.cursor()
            # Aseguramos que address sea bytes para consistencia
            addr_val = output.script_pubkey
            if isinstance(addr_val, str):
                addr_val = addr_val.encode('utf-8')

            cursor.execute('''
                INSERT OR REPLACE INTO utxos (tx_hash, output_index, amount, address)
                VALUES (?, ?, ?, ?)
            ''', (tx_hash, index, output.value_alba, addr_val))
            self.conn.commit()
        except Exception as e:
            logging.error(f"Error guardando UTXO: {e}")
            self.conn.rollback()

    def remove_utxo(self, tx_hash: str, index: int) -> None:
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM utxos WHERE tx_hash = ? AND output_index = ?', (tx_hash, index))
            self.conn.commit()
        except Exception as e:
            logging.error(f"Error eliminando UTXO: {e}")
            self.conn.rollback()

    def get_utxo(self, tx_hash: str, index: int) -> Optional[TxOutput]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT amount, address FROM utxos WHERE tx_hash = ? AND output_index = ?', (tx_hash, index))
        row = cursor.fetchone()
        if row:
            addr = row[1]
            if isinstance(addr, str):
                addr = addr.encode('utf-8')
            return TxOutput(value_alba=int(row[0]), script_pubkey=addr)
        return None

    def get_utxos_by_address(self, address: Union[str, bytes]) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        
        # Normalizar a bytes para la búsqueda
        addr_query = address
        if isinstance(address, str):
            addr_query = address.encode('utf-8')

        cursor.execute('SELECT tx_hash, output_index, amount, address FROM utxos WHERE address = ?', (addr_query,))
        rows = cursor.fetchall()
        
        # ⚡ CORRECCIÓN DE TIPADO: Declaración explícita del tipo de lista
        results: List[Dict[str, Any]] = []
        
        for row in rows:
            # Al recuperar, mantenemos bytes en el objeto interno
            addr_stored = row[3]
            out_obj = TxOutput(value_alba=int(row[2]), script_pubkey=addr_stored)
            
            results.append({
                "tx_hash": row[0],
                "output_index": int(row[1]),
                "amount": int(row[2]),
                "output_object": out_obj
            })
        return results

    def get_total_supply(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute('SELECT SUM(amount) FROM utxos')
        res = cursor.fetchone()
        return res[0] if res[0] else 0

    def clear(self) -> None:
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM utxos')
            self.conn.commit()
            logging.warning("⚠️ UTXO Set vaciado en disco.")
        except Exception as e:
            self.conn.rollback()
            raise e