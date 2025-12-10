# akm/infra/persistence/database_manager.py
import sqlite3
import logging
import os
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
        
        # ✅ CORRECCIÓN CRÍTICA: Usar la ruta completa (db_path)
        # Esto incluye el directorio data_dir específico de cada nodo
        self.db_path = config.persistence.db_path 
        
        # Asegurar que el directorio exista antes de conectar
        directory = os.path.dirname(self.db_path)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                logging.info(f"📂 Directorio creado: {directory}")
            except OSError as e:
                logging.error(f"❌ Error creando directorio DB: {e}")
            
        logging.info(f"🔌 Conectando al archivo: {self.db_path}")

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        
        # 1. Tabla de Bloques
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
        
        # 2. Tabla de UTXOs (Necesaria para el sistema de saldos)
        # Sin esta tabla, el repositorio de UTXO fallaría
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