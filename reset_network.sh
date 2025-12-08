#!/bin/bash

# Colores para que se vea pro
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=========================================${NC}"
echo -e "${YELLOW}   AKM PROTOCOL - LIMPIEZA DE RED (RESET) ${NC}"
echo -e "${YELLOW}=========================================${NC}"
echo "Este script eliminará TODA la base de datos de la blockchain local."
echo "Se borrarán:"
echo "  1. La Blockchain completa (Full Node DB)"
echo "  2. Las cabeceras ligeras (Light Node DB)"
echo "  3. Los archivos de Logs"

read -p "¿Estás seguro de que quieres reiniciar la red desde cero? (s/n): " confirm

if [[ $confirm == "s" || $confirm == "S" ]]; then
    echo -e "\n${RED}[LIMPIANDO] Eliminando datos antiguos...${NC}"

    # 1. Limpiar datos del Full Node
    if [ -d "./data/blockchain_db" ]; then
        rm -rf ./data/blockchain_db
        echo " - Base de datos Full Node eliminada."
    fi

    # 2. Limpiar datos del Light Node
    if [ -d "./data/headers_db" ]; then
        rm -rf ./data/headers_db
        echo " - Base de datos Light Node eliminada."
    fi

    # 3. Recrear carpetas vacías (Acondicionamiento)
    mkdir -p ./data/blockchain_db
    mkdir -p ./data/headers_db
    mkdir -p ./logs
    
    # 4. Crear un archivo de bloqueo o 'lock' (Simulación de entorno listo)
    touch ./data/.fresh_state

    echo -e "${GREEN}[EXITO] Entorno AKM acondicionado y limpio.${NC}"
    echo -e "${GREEN}[LISTO] Ahora puedes iniciar el Nodo Maestro para generar el Bloque Génesis.${NC}"

else
    echo "Operación cancelada. No se borró nada."
fi