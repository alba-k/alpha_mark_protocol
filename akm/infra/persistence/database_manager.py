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
        config = ConfigManager()
        self.db_path = config.persistence.db_name
        
        logging.info(f"🔌 Conectando al archivo: {self.db_path}")

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        # Tabla de Bloques
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

    def close(self):
        """
        Método público para cerrar la conexión limpiamente.
        """
        if self.conn:
            try:
                self.conn.close()
                logging.info("🔌 Conexión a DB cerrada.")
            except Exception as e:
                logging.error(f"Error cerrando DB: {e}")

    @classmethod
    def reset(cls):
        """
        Método público para resetear el Singleton (Testing).
        Cierra la conexión existente y limpia la instancia.
        """
        if cls._instance:
            cls._instance.close()
            cls._instance = None
            logging.info("♻️  Singleton DatabaseManager reseteado.")