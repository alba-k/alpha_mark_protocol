# akm/core/utils/monetary.py
import logging
from decimal import Decimal, InvalidOperation, getcontext
from typing import Union
from akm.core.config.consensus_config import ConsensusConfig 

# Configuración de precisión para cálculos financieros de alta fidelidad
getcontext().prec = 28

# Tipado de entrada
MonetaryInput = Union[str, float, Decimal]
AlbasInput = Union[int, str]

logger = logging.getLogger(__name__)

class Monetary:

    @staticmethod
    def to_albas(amount_akm: MonetaryInput) -> int:
        try:
            # 1. Normalización a Decimal (str protege contra imprecisión de floats)
            d_amount = Decimal(str(amount_akm))
            
            # 2. Factor de escala: $d\_albas = d\_amount \times \text{COIN\_FACTOR}$
            d_albas = d_amount * ConsensusConfig.COIN_FACTOR
            
            # 3. Validación de "Polvo" (No se permiten fracciones de Alba)
            if d_albas % 1 != 0:
                # Esto es un error de lógica del usuario o la UI
                return 0 # O lanzar una excepción controlada

            return int(d_albas)
            
        except (InvalidOperation, ValueError, TypeError):
            logger.exception(f"Error crítico convirtiendo AKM a Albas: {amount_akm}")
            raise ValueError("Monto AKM inválido.")

    @staticmethod
    def to_akm(amount_albas: AlbasInput) -> Decimal:
        
        try:
            # 1. Normalización segura de entrada
            value: int = 0
            
            if isinstance(amount_albas, int):
                value = amount_albas
            elif isinstance(amount_albas, str): # pyright: ignore[reportUnnecessaryIsInstance]
                value = int(amount_albas)
            else:
                raise TypeError(f"Tipo no soportado: {type(amount_albas)}")
            
            # 2. El protocolo no permite saldos negativos en la conversión base
            if value < 0:
                raise ValueError("Albas negativas.")

            # 3. Conversión matemática: $\frac{\text{value}}{\text{COIN\_FACTOR}}$
            return Decimal(value) / Decimal(ConsensusConfig.COIN_FACTOR)
            
        except (TypeError, ValueError):
            logger.exception(f"Error procesando Albas para visualización: {amount_albas}")
            raise ValueError("Monto en Albas corrupto.")