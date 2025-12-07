# akm/core/utils/monetary.py
from decimal import Decimal, InvalidOperation, getcontext
from typing import Union
from akm.core.config.consensus_config import ConsensusConfig 

# Configurar precisión global para evitar problemas en operaciones complejas
getcontext().prec = 28

MonetaryInput = Union[str, float, Decimal]
AlbasInput = Union[int, str]

class Monetary:
    """
    Utilidad estática para conversiones monetarias seguras (AKM <-> Alba).
    Mantiene la integridad financiera del protocolo.
    
    Regla de Oro:
    - Cálculos internos -> SIEMPRE en Albas (Enteros).
    - Visualización -> SIEMPRE en AKM (Decimal).
    """

    @staticmethod
    def to_albas(amount_akm: MonetaryInput) -> int:
        """
        Convierte AKM (visual) -> Albas (entero).
        Ejemplo: 1.5 AKM -> 150,000,000 Albas
        """
        try:
            # 1. Normalización a Decimal (str protege contra imprecisión de floats)
            d_amount = Decimal(str(amount_akm))
            
            # 2. Multiplicación por el factor de escala (ej: 100,000,000)
            d_albas = d_amount * ConsensusConfig.COIN_FACTOR
            
            # 3. Validación de "Polvo" (Decimales no permitidos en Albas)
            # Usamos % 1 para ver si hay residuo, en lugar de buscar puntos en string
            if d_albas % 1 != 0:
                raise ValueError(f"Precisión excedida. Máximo {ConsensusConfig.DECIMALS} decimales permitidos.")
            
            # 4. Retornar Entero Puro
            return int(d_albas)
            
        except (InvalidOperation, ValueError, TypeError) as e:
            raise ValueError(f"Monto AKM inválido para conversión: {e}")

    @staticmethod
    def to_akm(amount_albas: AlbasInput) -> Decimal:
        """
        Convierte Albas (entero) -> AKM (Decimal) para mostrar al usuario.
        Ejemplo: 150,000,000 Albas -> 1.5 AKM
        """
        try:
            # 1. Normalización segura de entrada
            value: int = 0
            
            if isinstance(amount_albas, int):
                value = amount_albas
            elif isinstance(amount_albas, str): # pyright: ignore[reportUnnecessaryIsInstance]
                if not amount_albas.lstrip('-').isdigit(): # Validación extra de string
                     raise ValueError("El string debe contener solo números.")
                value = int(amount_albas)
            else:
                raise TypeError(f"Tipo no soportado: {type(amount_albas)}")
            
            # 2. Validación de Negativos (El dinero no debe ser negativo en conversión base)
            if value < 0:
                raise ValueError("El monto en Albas no puede ser negativo.")

            # 3. Conversión matemática segura
            return Decimal(value) / Decimal(ConsensusConfig.COIN_FACTOR)
            
        except (TypeError, ValueError) as e:
            # Relanzamos como ValueError para que la API lo capture limpiamente (400 Bad Request)
            raise ValueError(f"Error procesando Albas: {e}")