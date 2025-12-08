#!/bin/bash
echo "==================================="
echo "   ALPHA MARK PROTOCOL (AKM) CLI   "
echo "==================================="
echo "1. Iniciar Nodo Completo (Full Node)"
echo "2. Iniciar Nodo Ligero (Light Node)  <-- NUEVO"
echo "3. Iniciar Minero (Miner)"
echo "==================================="
read -p "Selecciona una opción [1-3]: " opcion

if [ "$opcion" == "1" ]; then
    python3 main.py --mode node --config config/node_full.json
elif [ "$opcion" == "2" ]; then
    # Aquí usamos el mismo código main.py, pero con la config ligera
    python3 main.py --mode node --config config/node_light.json
elif [ "$opcion" == "3" ]; then
    python3 main.py --mode miner --config config/miner_solo.json
else
    echo "Opción no válida."
fi