# akm/infra/persistence/sqlite/sqlite_utxo_repository.py

import logging
from typing import List, Optional, Dict, Any, Union, Tuple
from akm.core.interfaces.i_utxo_repository import IUTXORepository
from akm.core.models.tx_output import TxOutput
from akm.infra.persistence.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class SqliteUTXORepository(IUTXORepository):

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.conn = self.db_manager.get_connection()
        self._create_table()
        logger.debug("🏦 SqliteUTXORepository inicializado (Estado UTXO).")

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

    # --- [IMPORTANTE] EL TRADUCTOR QUE FALTABA ---
    def _address_to_script_pattern(self, address: Union[str, bytes]) -> bytes:
        """
        Convierte la dirección simple (ej. '1GQ...') al formato de SCRIPT (P2PKH)
        que está realmente almacenado en la base de datos.
        """
        OP_DUP = b'\x76'
        OP_HASH160 = b'\xa9'
        OP_EQUALVERIFY = b'\x88'
        OP_CHECKSIG = b'\xac'

        if isinstance(address, str):
            addr_bytes = address.encode('utf-8')
        else:
            addr_bytes = address
            
        push_op = bytes([len(addr_bytes)])
        
        # Construimos el candado para que coincida con la DB
        return (
            OP_DUP + 
            OP_HASH160 + 
            push_op + addr_bytes + 
            OP_EQUALVERIFY + 
            OP_CHECKSIG
        )

    # --- Métodos básicos ---
    def add_utxo(self, tx_hash: str, index: int, output: TxOutput) -> None:
        try:
            cursor = self.conn.cursor()
            script_blob = output.script_pubkey
            if isinstance(script_blob, str):
                script_blob = script_blob.encode('utf-8')

            cursor.execute('''
                INSERT OR REPLACE INTO utxos (tx_hash, output_index, amount, address)
                VALUES (?, ?, ?, ?)
            ''', (tx_hash, index, output.value_alba, script_blob))
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"❌ Error guardando UTXO en {tx_hash[:8]}: {e}")
            self.conn.rollback()

    def remove_utxo(self, tx_hash: str, index: int) -> None:
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM utxos WHERE tx_hash = ? AND output_index = ?', (tx_hash, index))
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"❌ Error eliminando UTXO {tx_hash[:8]}: {e}")
            self.conn.rollback()

    def update_batch(self, new_utxos: List[Tuple[str, int, TxOutput]], spent_utxos: List[Tuple[str, int]]) -> None:
        cursor = self.conn.cursor()
        
        try:
            if spent_utxos:
                cursor.executemany('DELETE FROM utxos WHERE tx_hash = ? AND output_index = ?', spent_utxos)

            new_data: List[Tuple[str, int, int, bytes]] = [] 
            for tx_hash, index, output in new_utxos:
                script_blob = output.script_pubkey
                if isinstance(script_blob, str):
                    script_blob = script_blob.encode('utf-8')
                new_data.append((tx_hash, index, output.value_alba, script_blob))
            
            if new_data:
                cursor.executemany('''
                    INSERT OR REPLACE INTO utxos (tx_hash, output_index, amount, address)
                    VALUES (?, ?, ?, ?)
                ''', new_data)

            self.conn.commit()
            logger.debug(f"🔄 UTXO Batch: +{len(new_utxos)} añadidas, -{len(spent_utxos)} eliminadas.")
            
        except Exception as e:
            logger.error(f"❌ Error CRÍTICO en UTXO batch update: {e}")
            self.conn.rollback()
            raise e

    # --- CONSULTAS ---

    def get_utxo(self, tx_hash: str, index: int) -> Optional[TxOutput]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT amount, address FROM utxos WHERE tx_hash = ? AND output_index = ?', (tx_hash, index))
        row = cursor.fetchone()
        if row:
            # Retorna el script almacenado
            return TxOutput(value_alba=int(row[0]), script_pubkey=row[1])
        return None
 
    def get_utxos_by_address(self, address: Union[str, bytes]) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        
        # [AQUÍ ESTÁ LA CORRECCIÓN CLAVE]
        # Usamos el traductor para buscar el candado correcto
        target_script = self._address_to_script_pattern(address)

        cursor.execute('SELECT tx_hash, output_index, amount, address FROM utxos WHERE address = ?', (target_script,))
        rows = cursor.fetchall()
        
        results: List[Dict[str, Any]] = []
        for row in rows:
            script_stored = row[3]
            out_obj = TxOutput(value_alba=int(row[2]), script_pubkey=script_stored)
            
            results.append({
                "tx_hash": row[0],
                "output_index": int(row[1]),
                "amount": int(row[2]),
                "output_object": out_obj
            })
            
        logger.debug(f"🔍 Consulta de balance: {len(results)} UTXOs encontrados.")
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
            logger.warning("⚠️ UTXO Set vaciado.")
        except Exception as e:
            self.conn.rollback()
            raise e