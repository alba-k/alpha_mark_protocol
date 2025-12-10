#!/bin/bash

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directorio de logs
LOG_DIR="logs"
mkdir -p $LOG_DIR

cleanup() {
    echo -e "\n${RED}[SHUTDOWN] Deteniendo toda la red...${NC}"
    if [ ! -z "$PID_FULL" ]; then kill $PID_FULL 2>/dev/null; fi
    if [ ! -z "$PID_LIGHT" ]; then kill $PID_LIGHT 2>/dev/null; fi
    if [ ! -z "$PID_MINER" ]; then kill $PID_MINER 2>/dev/null; fi
    pkill -f "python3 main.py"
    echo -e "${GREEN}[EXITO] Red detenida.${NC}"
    exit
}
trap cleanup SIGINT

echo -e "${CYAN}==========================================${NC}"
echo -e "${CYAN}   🚀 AKM PROTOCOL - AUTO LAUNCHER 🚀   ${NC}"
echo -e "${CYAN}==========================================${NC}"

# 0. Limpieza inicial
pkill -f "python3 main.py"
sleep 1

# 1. Iniciar Full Node (Puerto API 8080)
echo -e "${GREEN}[1/3] Iniciando Full Node (Master)...${NC}"
# Forzamos el puerto 8080 para el nodo principal
export AKM_API_PORT=8080
python3 main.py --mode node --config config/node_full.json > "$LOG_DIR/full_node.log" 2>&1 &
PID_FULL=$!
sleep 5

# 2. Iniciar Light Node (Puerto API 8082)
echo -e "${GREEN}[2/3] Iniciando Light Node (SPV)...${NC}"
export AKM_API_PORT=8082
python3 main.py --mode node --config config/node_light.json > "$LOG_DIR/light_node.log" 2>&1 &
PID_LIGHT=$!
sleep 2

# 3. Iniciar Minero (Puerto API 8081)
echo -e "${GREEN}[3/3] Iniciando Minero (Worker)...${NC}"
export AKM_API_PORT=8081
python3 main.py --mode miner --config config/miner_solo.json > "$LOG_DIR/miner.log" 2>&1 &
PID_MINER=$!

echo -e "\n${GREEN}✅ RED COMPLETA OPERATIVA${NC}"
echo -e "   🖥️  Full Node UI:    http://localhost:8080/app/index.html"
echo -e "   ⛏️  Miner Node UI:   http://localhost:8081/app/index.html"
echo -e "   📱  Light Node UI:   http://localhost:8082/app/index.html"
echo -e "${YELLOW}Usa [tail -f logs/full_node.log] para ver detalles.${NC}"
echo -e "${RED}PRESIONA [CTRL+C] PARA SALIR${NC}"

while true; do sleep 1; done