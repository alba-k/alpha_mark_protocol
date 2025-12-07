# akm/infra/persistence/database_manager.py
import sqlite3
import logging
from akm.core.config.config_manager import ConfigManager

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Leemos el nombre que pusiste en el código
        config = ConfigManager()
        self.db_path = config.persistence.db_name
        
        logging.info(f"🔌 Conectando al archivo: {self.db_path}")

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                block_index INTEGER PRIMARY KEY,
                block_hash TEXT UNIQUE NOT NULL,
                previous_hash TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                bits TEXT NOT NULL,
                nonce INTEGER NOT NULL,
                merkle_root TEXT NOT NULL,
                data_json TEXT NOT NULL
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hash ON blocks(block_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prev_hash ON blocks(previous_hash)')
        self.conn.commit()

    def get_connection(self):
        return self.conn