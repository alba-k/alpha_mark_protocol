#!/bin/bash
# reset_network.sh

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=========================================${NC}"
echo -e "${YELLOW}   AKM PROTOCOL - HARD RESET (REAL DB)   ${NC}"
echo -e "${YELLOW}=========================================${NC}"
echo "ADVERTENCIA: Esto borrará permanentemente:"
echo " 1. La Blockchain completa (SQLite/LevelDB)."
echo " 2. El historial de transacciones y UTXOs."
echo " 3. Logs de ejecución y caché compilada."

read -p "¿Confirmar borrado total? (s/n): " confirm

if [[ $confirm == "s" || $confirm == "S" ]]; then
    echo -e "\n${RED}[LIMPIANDO] Borrando sistema...${NC}"

    # 1. Eliminar directorio de datos (Donde vive blockchain_oficial.db)
    # Según PersistenceConfig, esto es por defecto './data'
    if [ -d "data" ]; then
        rm -rf data
        echo " - Directorio ./data/ eliminado (Blockchain purgada)."
    fi

    # 2. Eliminar bases de datos sueltas en raíz (por si acaso versiones viejas)
    rm -f *.db
    
    # 3. Borrar logs
    rm -f *.log
    echo " - Logs eliminados."

    # 4. Limpiar caché de Python (pycache) para evitar inconsistencias de código
    find . -type d -name "__pycache__" -exec rm -rf {} +
    echo " - Caché de Python (__pycache__) eliminada."

    # 5. Recrear estructura limpia
    mkdir -p data
    
    echo -e "${GREEN}[EXITO] Red reiniciada completamente.${NC}"
    echo -e "${GREEN}El próximo inicio generará un nuevo Bloque GÉNESIS.${NC}"
else
    echo "Operación cancelada."
fi