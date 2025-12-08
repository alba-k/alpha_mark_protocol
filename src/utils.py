# src/utils.py
from typing import Any

def validate_address(address: Any) -> bool:
    """
    Verifica si la dirección es válida y segura.
    Retorna True si pasa las pruebas, False si no.
    """
    # 1. Verificación básica: Que no sea None
    if not address:
        return False
    
    # 2. Verificación de tipo: Debe ser texto (str)
    if not isinstance(address, str):
        return False

    # 3. Verificación de longitud mínima (Ej: billeteras de juguete > 10 chars)
    if len(address) < 10:
        return False
    
    # Si pasa todo:
    return True