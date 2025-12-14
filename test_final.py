# test_final.py

import sqlite3
import os

# Ruta exacta que vimos en tu log del Full Node
DB_PATH = "data/blockchain/blockchain_full.db"

def la_verdad_absoluta():
    print(f"🕵️‍♂️ INSPECCIONANDO: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print("❌ ¡ERROR! El archivo .db no existe físicamente.")
        return

    # Conectamos en modo solo lectura
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cursor = conn.cursor()

    try:
        # 1. Contar Bloques
        cursor.execute("SELECT COUNT(*) FROM blocks")
        total = cursor.fetchone()[0]
        
        print("\n" + "="*40)
        print(f"📊 RESULTADO REAL: {total} Bloques encontrados")
        print("="*40 + "\n")

        if total > 0:
            # 2. Ver detalles del último
            cursor.execute("SELECT height, hash, timestamp FROM blocks ORDER BY height DESC LIMIT 1")
            ultimo = cursor.fetchone()
            print(f"🏆 CIMA DE LA CADENA (TIP):")
            print(f"   ➤ Altura: {ultimo[0]}")
            print(f"   ➤ Hash:   {ultimo[1]}")
            print(f"   ➤ Fecha:  {ultimo[2]}")
            print("\n✅ CONCLUSIÓN: Los datos ESTÁN SEGUROS, tu visor de VS Code te miente.")
        else:
            print("❌ CONCLUSIÓN: La base de datos está realmente vacía.")

    except Exception as e:
        print(f"💥 Error al leer: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    la_verdad_absoluta()