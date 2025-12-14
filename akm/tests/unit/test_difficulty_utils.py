# akm/tests/unit/test_difficulty_utils.py
'''
Test Suite para DifficultyUtils:
    Verifica la conversión correcta entre formato compacto (Bits) y numérico (Target).
    Esencial para la validación de Proof-of-Work.

    Functions::
        test_bits_to_target_genesis(): Verifica la conversión del valor estándar Génesis.
        test_bits_to_target_invalid_format(): Verifica el manejo defensivo de formatos erróneos.
        test_target_to_bits_genesis(): Verifica la conversión inversa correcta.
        test_round_trip_conversion(): Verifica que bits -> target -> bits sea consistente.
        test_max_target_cap(): Verifica que la dificultad nunca sea más fácil que el límite.
'''

import sys
import os

# --- AJUSTE DE RUTA PARA EJECUCIÓN DIRECTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '../../..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from akm.core.utils.difficulty_utils import DifficultyUtils

def test_bits_to_target_genesis():
    print(">> Ejecutando: test_bits_to_target_genesis...")
    
    # 1. Bits estándar de Génesis (Dificultad mínima)
    genesis_bits = "1d00ffff"
    
    # 2. Conversión
    target = DifficultyUtils.bits_to_target(genesis_bits)
    
    # 3. Verificación
    # El valor esperado es MAX_TARGET (ya que "1d00ffff" define el límite)
    assert target == DifficultyUtils.MAX_TARGET
    print("[SUCCESS] Conversión de bits Génesis correcta.\n")

def test_bits_to_target_invalid_format():
    print(">> Ejecutando: test_bits_to_target_invalid_format...")
    
    # Casos inválidos (longitud incorrecta, caracteres no hex, etc.)
    invalids = ["", "123", "patata", "1d00ff"] 
    
    for bad_bits in invalids:
        target = DifficultyUtils.bits_to_target(bad_bits)
        # Debe retornar MAX_TARGET por defecto (comportamiento defensivo)
        assert target == DifficultyUtils.MAX_TARGET
        
    print("[SUCCESS] Formatos inválidos manejados correctamente (Fallback a MAX_TARGET).\n")

def test_target_to_bits_genesis():
    print(">> Ejecutando: test_target_to_bits_genesis...")
    
    # 1. Usamos el MAX_TARGET numérico
    max_target = DifficultyUtils.MAX_TARGET
    
    # 2. Convertimos a bits
    bits = DifficultyUtils.target_to_bits(max_target)
    
    # 3. Debe ser exactamente "1d00ffff"
    if bits != "1d00ffff":
        print(f"   [DEBUG] Error: Esperaba '1d00ffff', recibí '{bits}'")
        
    assert bits == "1d00ffff"
    print("[SUCCESS] Conversión inversa a bits correcta.\n")

def test_round_trip_conversion():
    print(">> Ejecutando: test_round_trip_conversion...")
    
    # Un valor de dificultad arbitrario (más difícil que génesis)
    # Ej: 0x1b0404cb (Dificultad histórica de Bitcoin)
    original_bits = "1b0404cb"
    
    # 1. Bits -> Target
    target = DifficultyUtils.bits_to_target(original_bits)
    
    # 2. Target -> Bits
    calculated_bits = DifficultyUtils.target_to_bits(target)
    
    # La conversión debe ser simétrica
    if calculated_bits != original_bits:
        print(f"   [DEBUG] Error Round-Trip: Orig '{original_bits}' -> Calc '{calculated_bits}'")

    assert calculated_bits == original_bits
    print("[SUCCESS] Round-trip (Ida y Vuelta) consistente.\n")

def test_max_target_cap():
    print(">> Ejecutando: test_max_target_cap...")
    
    # Un target absurdamente alto (más fácil que el génesis)
    # Intentamos crear una dificultad 10 veces más fácil que lo permitido
    huge_target = DifficultyUtils.MAX_TARGET * 10
    
    # Al convertir a bits, la utilidad debe toparlo a "1d00ffff" (Génesis)
    # para proteger el protocolo.
    bits = DifficultyUtils.target_to_bits(huge_target)
    
    if bits != "1d00ffff":
        print(f"   [DEBUG] Error de CAP: Esperaba '1d00ffff', recibí '{bits}'")
        print("   -> SUGERENCIA: Verifica que tengas el bloque 'if target > MAX_TARGET' en DifficultyUtils.target_to_bits")

    assert bits == "1d00ffff"
    print("[SUCCESS] Límite de dificultad (Cap) aplicado correctamente.\n")

# --- PUNTO DE ENTRADA PARA EJECUCIÓN MANUAL ---
if __name__ == "__main__":
    print("=======================================")
    print("   EJECUTANDO TESTS DIFFICULTY UTILS   ")
    print("=======================================\n")

    try:
        test_bits_to_target_genesis()
        test_bits_to_target_invalid_format()
        test_target_to_bits_genesis()
        test_round_trip_conversion()
        test_max_target_cap()

        print("==========================================")
        print("   TODOS LOS TESTS PASARON EXITOSAMENTE   ")
        print("==========================================")
    except AssertionError as e:
        print(f"\nFALLO DE ASERCIÓN: {e}")
    except Exception as e:
        print(f"\nERROR INESPERADO: {e}")