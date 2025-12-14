# akm/infra/persistence/database_manager.py

import sqlite3
import logging
import os
from akm.core.config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        config = ConfigManager()
        self.db_path = config.persistence.db_path 
        
        # Asegurar directorios
        directory = os.path.dirname(self.db_path)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
            except OSError:
                pass
            
        logger.info(f"🔌 Conectando al archivo: {self.db_path}")

        # Conexión
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        # [SOLUCIÓN] 👇 ESTAS LÍNEAS OBLIGAN A ESCRIBIR EN EL ARCHIVO REAL 👇
        # Desactivamos el modo WAL y forzamos escritura síncrona
        try:
            self.conn.execute("PRAGMA journal_mode=DELETE;") 
            self.conn.execute("PRAGMA synchronous=FULL;")
        except Exception as e:
            logger.warning(f"No se pudo configurar PRAGMA: {e}")
        # ---------------------------------------------------------------

        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        
        # 1. Tabla de Bloques
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                height INTEGER PRIMARY KEY,
                hash TEXT UNIQUE NOT NULL,
                prev_hash TEXT NOT NULL,
                merkle_root TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                nonce INTEGER NOT NULL,
                difficulty TEXT NOT NULL, 
                data JSON NOT NULL
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hash ON blocks(hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prev_hash ON blocks(prev_hash)')
        
        # 2. Tabla de UTXOS
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

    def get_connection(self):
        return self.conn

    def close(self):
        if self.conn:
            try:
                self.conn.close()
                logger.info("🔌 Conexión a DB cerrada.")
            except Exception:
                pass

    @classmethod
    def reset(cls):
        if cls._instance:
            cls._instance.close()
            cls._instance = None