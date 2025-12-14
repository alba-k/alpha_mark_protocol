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

    # --- Métodos básicos (add_utxo, remove_utxo) ---
    def add_utxo(self, tx_hash: str, index: int, output: TxOutput) -> None:
        try:
            cursor = self.conn.cursor()
            addr_val = output.script_pubkey
            if isinstance(addr_val, str):
                addr_val = addr_val.encode('utf-8')

            cursor.execute('''
                INSERT OR REPLACE INTO utxos (tx_hash, output_index, amount, address)
                VALUES (?, ?, ?, ?)
            ''', (tx_hash, index, output.value_alba, addr_val))
            self.conn.commit()
            
            logger.debug(f"➕ UTXO Añadido: {tx_hash[:8]}... index {index} ({output.value_alba} Alba)")
            
        except Exception as e:
            logger.error(f"❌ Error guardando UTXO en {tx_hash[:8]}: {e}")
            self.conn.rollback()

    def remove_utxo(self, tx_hash: str, index: int) -> None:
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM utxos WHERE tx_hash = ? AND output_index = ?', (tx_hash, index))
            self.conn.commit()
            
            logger.debug(f"➖ UTXO Gastado/Eliminado: {tx_hash[:8]}... index {index}")
            
        except Exception as e:
            logger.error(f"❌ Error eliminando UTXO {tx_hash[:8]}: {e}")
            self.conn.rollback()

    def update_batch(self, new_utxos: List[Tuple[str, int, TxOutput]], spent_utxos: List[Tuple[str, int]]) -> None:
        """Aplica adición y eliminación de UTXOs en una transacción atómica."""
        cursor = self.conn.cursor()
        
        try:
            # 1. Eliminar UTXOs gastados (Inputs)
            # spent_utxos ya está en el formato requerido List[Tuple[str, int]]
            spent_data_for_db = spent_utxos
            
            if spent_data_for_db:
                # Usamos executemany para eficiencia en la eliminación
                cursor.executemany('DELETE FROM utxos WHERE tx_hash = ? AND output_index = ?', spent_data_for_db)

            # 2. Insertar nuevas UTXOs (Outputs)
            # Definimos new_data con una sugerencia de tipo explícita para evitar 'Unknown'
            # Los elementos serán (tx_hash, index, amount, address_bytes)
            new_data: List[Tuple[str, int, int, bytes]] = [] 
            
            for tx_hash, index, output in new_utxos:
                addr_val = output.script_pubkey
                
                # Aseguramos que la dirección sea bytes para la base de datos (BLOB)
                if isinstance(addr_val, str):
                    addr_val = addr_val.encode('utf-8')
                
                new_data.append((tx_hash, index, output.value_alba, addr_val))
            
            if new_data:
                # Usamos executemany para inserción eficiente (INSERT OR REPLACE)
                cursor.executemany('''
                    INSERT OR REPLACE INTO utxos (tx_hash, output_index, amount, address)
                    VALUES (?, ?, ?, ?)
                ''', new_data)

            self.conn.commit()
            logger.debug(f"🔄 UTXO Batch: +{len(new_utxos)} añadidas, -{len(spent_utxos)} eliminadas.")
            
        except Exception as e:
            logger.error(f"❌ Error CRÍTICO en UTXO batch update: {e}")
            self.conn.rollback()
            raise e # Es un error crítico, debe propagarse

    # --- Métodos de consulta (mantienen su lógica) ---

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
        
        addr_query = address
        if isinstance(address, str):
            addr_query = address.encode('utf-8')

        cursor.execute('SELECT tx_hash, output_index, amount, address FROM utxos WHERE address = ?', (addr_query,))
        rows = cursor.fetchall()
        
        results: List[Dict[str, Any]] = []
        for row in rows:
            addr_stored = row[3]
            out_obj = TxOutput(value_alba=int(row[2]), script_pubkey=addr_stored)
            
            results.append({
                "tx_hash": row[0],
                "output_index": int(row[1]),
                "amount": int(row[2]),
                "output_object": out_obj
            })
            
        logger.debug(f"🔍 Consulta de balance: {len(results)} UTXOs encontrados para la dirección.")
        return results

    def get_total_supply(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute('SELECT SUM(amount) FROM utxos')
        res = cursor.fetchone()
        total = res[0] if res[0] else 0
        logger.info(f"📊 Suministro total circulante: {total} Alba")
        return total

    def clear(self) -> None:
        """Limpia todo el estado UTXO. Usar con extrema precaución."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM utxos')
            self.conn.commit()
            logger.warning("⚠️ CRÍTICO: UTXO Set vaciado completamente de la base de datos.")
        except Exception as e:
            logger.error(f"❌ Fallo al limpiar UTXO Set: {e}")
            self.conn.rollback()
            raise e