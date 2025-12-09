#!/bin/bash
# akm-cli.sh

# Colores
CYAN='\033[0;36m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${CYAN}===================================${NC}"
echo -e "${CYAN}   ALPHA MARK PROTOCOL (AKM) CLI   ${NC}"
echo -e "${CYAN}   (Sistema Real - Producción)     ${NC}"
echo -e "${CYAN}===================================${NC}"
echo "1. Iniciar Nodo Completo (Full Node)"
echo "2. Iniciar Nodo Ligero (Light Node - SPV)"
echo "3. Iniciar Minero (Miner Node)"
echo "4. Salir"
echo "==================================="
read -p "Selecciona una opción [1-4]: " opcion

if [ "$opcion" == "1" ]; then
    echo -e "${GREEN}[LAUNCH] Iniciando Full Node (Validating)...${NC}"
    # Ejecuta el modo nodo con la configuración FULL
    python3 main.py --mode node --config config/node_full.json

elif [ "$opcion" == "2" ]; then
    echo -e "${GREEN}[LAUNCH] Iniciando Light Node (SPV)...${NC}"
    # Ejecuta el modo nodo con la configuración LIGHT (Prune activado)
    python3 main.py --mode node --config config/node_light.json

elif [ "$opcion" == "3" ]; then
    echo -e "${GREEN}[LAUNCH] Iniciando Minero (CPU Worker)...${NC}"
    # Ejecuta el modo minero con la configuración de minería
    python3 main.py --mode miner --config config/miner_solo.json

elif [ "$opcion" == "4" ]; then
    echo "Saliendo..."
    exit 0

else
    echo "Opción no válida."
fi