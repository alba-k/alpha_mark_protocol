# akm/infra/persistence/sqlite/sqlite_blockchain_repository.py
import json
import logging
import sqlite3
from typing import Dict, Any, List, Optional

# Interface
from akm.core.interfaces.i_repository import IBlockchainRepository

# Infra
from akm.infra.persistence.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class SqliteBlockchainRepository(IBlockchainRepository):
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.conn = self.db_manager.get_connection()
        logger.debug("🔌 SqliteBlockchainRepository vinculado al DatabaseManager.")

    def save_block(self, block_data: Dict[str, Any]) -> bool:
        """
        Guarda un bloque (que llega como Diccionario) en la base de datos.
        """
        try:
            cursor = self.conn.cursor()
            
            # 1. Extraer el header para las columnas indexadas
            header = block_data.get('header')
            if not header:
                logger.error("❌ Estructura de bloque inválida: Falta 'header'")
                return False

            # 2. Insertar. Guardamos TODO el JSON en la columna 'data'.
            # Esto es mucho más robusto que mapear campo por campo manualmente.
            cursor.execute("""
                INSERT OR IGNORE INTO blocks 
                (hash, height, prev_hash, merkle_root, timestamp, nonce, difficulty, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                header['hash'],
                header['index'],
                header['previous_hash'],
                header['merkle_root'],
                header['timestamp'],
                header['nonce'],
                str(header.get('difficulty', header.get('bits', ''))),
                json.dumps(block_data) # <--- AQUÍ está la clave: Guardamos el JSON completo
            ))
            
            self.conn.commit()
            return True
            
        except sqlite3.IntegrityError:
            return True # Ya existe, todo bien.
        except Exception as e:
            idx = block_data.get('header', {}).get('index', '???')
            logger.error(f"❌ Error crítico guardando bloque #{idx} en SQLite: {e}")
            return False

    def save_blocks_atomic(self, chain_data: List[Dict[str, Any]]) -> bool:
        """Guarda múltiples bloques en una sola transacción."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute("DELETE FROM blocks") # Reemplazo total (Sync)
            
            for block_data in chain_data:
                header = block_data['header']
                cursor.execute("""
                    INSERT INTO blocks 
                    (hash, height, prev_hash, merkle_root, timestamp, nonce, difficulty, data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    header['hash'],
                    header['index'],
                    header['previous_hash'],
                    header['merkle_root'],
                    header['timestamp'],
                    header['nonce'],
                    str(header.get('difficulty', header.get('bits', ''))),
                    json.dumps(block_data)
                ))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Rollback ejecutado. Error guardando cadena: {e}")
            raise

    def get_last_block(self) -> Optional[Dict[str, Any]]:
        """Recupera el último bloque como Diccionario."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT data FROM blocks ORDER BY height DESC LIMIT 1")
            row = cursor.fetchone()
            
            if row:
                return json.loads(row[0]) # JSON -> Dict
            return None
        except Exception as e:
            logger.error(f"Error leyendo último bloque: {e}")
            return None

    def get_block_by_hash(self, block_hash: str) -> Optional[Dict[str, Any]]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT data FROM blocks WHERE hash = ?", (block_hash,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None
        except Exception:
            return None

    def get_blocks_range(self, start_index: int, limit: int) -> List[Dict[str, Any]]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT data FROM blocks 
                WHERE height >= ? 
                ORDER BY height ASC 
                LIMIT ?
            """, (start_index, limit))
            
            rows = cursor.fetchall()
            return [json.loads(row[0]) for row in rows]
        except Exception as e:
            logger.error(f"Error leyendo rango de bloques: {e}")
            return []

    def count(self) -> int:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM blocks")
            row = cursor.fetchone()
            return row[0] if row else 0
        except Exception:
            return 0
    
    def get_headers_range(self, start_hash: str, limit: int = 2000) -> List[Dict[str, Any]]:
        # Recuperamos solo datos ligeros para SPV
        cursor = self.conn.cursor()
        
        # Buscar desde dónde empezar
        start_height = 0
        if start_hash:
            cursor.execute("SELECT height FROM blocks WHERE hash = ?", (start_hash,))
            row = cursor.fetchone()
            if row:
                start_height = row[0] + 1
        
        cursor.execute("""
            SELECT height, hash, prev_hash, timestamp, difficulty, nonce, merkle_root
            FROM blocks 
            WHERE height >= ? 
            ORDER BY height ASC 
            LIMIT ?
        """, (start_height, limit))
        
        headers: List[Dict[str, Any]] = []
        for r in cursor.fetchall():
            headers.append({
                "index": r[0], "hash": r[1], "previous_hash": r[2],
                "timestamp": r[3], "bits": r[4], "nonce": r[5], "merkle_root": r[6]
            })
        return headers