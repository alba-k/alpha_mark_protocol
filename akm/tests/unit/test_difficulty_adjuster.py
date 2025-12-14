# akm/tests/unit/test_difficulty_adjuster.py
'''
Test Suite para DifficultyAdjuster:
    Verifica que la dificultad se ajuste correctamente según el tiempo de minado.

    Functions::
        test_increase_difficulty_when_too_fast(): Si minan rápido, dificultad debe subir.
        test_decrease_difficulty_when_too_slow(): Si minan lento, dificultad debe bajar.
'''

import sys
import os

# Ajuste de ruta
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '../../..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from akm.core.consensus.difficulty_adjuster import DifficultyAdjuster
from akm.core.models.block import Block
from akm.core.utils.difficulty_utils import DifficultyUtils
from akm.core.config.config_manager import ConfigManager

# Helper para crear bloques dummy con timestamps específicos
def create_block(timestamp: int, bits: str):
    # Aseguramos que el timestamp sea int al crear el bloque
    return Block(0, int(timestamp), "", bits, "", 0, "", [])

def test_increase_difficulty_when_too_fast():
    print(">> Ejecutando: test_increase_difficulty_when_too_fast...")
    
    adjuster = DifficultyAdjuster()
    config = ConfigManager()
    
    # Escenario: Dificultad inicial (Génesis)
    current_bits = config.initial_difficulty_bits 
    
    # Tiempo esperado para el intervalo
    expected_time = config.difficulty_adjustment_interval * config.target_block_time_sec
    
    # CASO: Minaron en la MITAD del tiempo (Muy rápido)
    start_time = 10000
    
    # CORRECCIÓN: Usamos división entera (//) o cast a int()
    # Antes: expected_time / 2 daba un float (ej. 3000.0)
    end_time = start_time + int(expected_time / 2) 
    
    prev_block = create_block(start_time, current_bits)
    last_block = create_block(end_time, current_bits)
    
    new_bits = adjuster.calculate_new_bits(prev_block, last_block)
    
    # Verificación
    old_target = DifficultyUtils.bits_to_target(current_bits)
    new_target = DifficultyUtils.bits_to_target(new_bits)
    
    # El nuevo target debe ser menor (más difícil)
    assert new_target < old_target
    print(f"   [OK] Dificultad Aumentó. Target bajó de {old_target:.2e} a {new_target:.2e}")

def test_decrease_difficulty_when_too_slow():
    print(">> Ejecutando: test_decrease_difficulty_when_too_slow...")
    
    adjuster = DifficultyAdjuster()
    config = ConfigManager()
    
    expected_time = config.difficulty_adjustment_interval * config.target_block_time_sec
    
    # CASO: Tardaron el DOBLE del tiempo (Muy lento)
    hard_bits = "1a00ffff" 
    
    start_time = 10000
    
    # Multiplicación suele dar int, pero aseguramos por consistencia
    end_time = start_time + int(expected_time * 2)
    
    prev_block = create_block(start_time, hard_bits)
    last_block = create_block(end_time, hard_bits)
    
    new_bits = adjuster.calculate_new_bits(prev_block, last_block)
    
    old_target = DifficultyUtils.bits_to_target(hard_bits)
    new_target = DifficultyUtils.bits_to_target(new_bits)
    
    # El nuevo target debe ser mayor (más fácil)
    assert new_target > old_target
    print(f"\n[OK] Dificultad Disminuyó. Target subió de {old_target:.2e} a {new_target:.2e}")

if __name__ == "__main__":
    try:
        test_increase_difficulty_when_too_fast()
        test_decrease_difficulty_when_too_slow()
        print("\nTESTS DIFFICULTY ADJUSTER PASARON EXITOSAMENTE")
    except AssertionError as e:
        print(f"\nFALLO: {e}")
    except Exception as e:
        print(f"\nERROR: {e}")