#!/bin/bash

# Colores para la terminal
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}===========================================${NC}"
echo -e "${CYAN}   ALPHA MARK PROTOCOL - NODE RUNNER      ${NC}"
echo -e "${CYAN}===========================================${NC}"

# 1. LIMPIEZA DE BASURA (Python Cache)
echo -e "${YELLOW}🧹 Limpiando archivos temporales (__pycache__)...${NC}"
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# 2. VERIFICACIÓN DE ENTORNO
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Advertencia: No se detectó entorno virtual (venv).${NC}"
fi

# 3. AYUDA RÁPIDA (Si no hay argumentos)
if [ $# -eq 0 ]; then
    echo -e "${GREEN}Uso:${NC} ./run.sh <config_json> --name <nombre_instancia> [opciones]"
    echo ""
    echo "Ejemplos:"
    echo "  Miner:   ./run.sh miner.json --name minero1"
    echo "  Wallet:  ./run.sh spv.json --name mi_billetera --seeds 192.168.1.50:5000"
    exit 1
fi

# 4. EJECUCIÓN DEL MAIN
echo -e "${GREEN}▶️  Ejecutando main.py...${NC}"
echo "-------------------------------------------"

# Pasamos todos los argumentos ($@) al script de python
python3 main.py "$@"