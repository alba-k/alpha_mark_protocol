# akm/core/consensus/subsidy_calculator.py
from akm.core.config.consensus_config import ConsensusConfig

class SubsidyCalculator:
    """
    Calcula la recompensa base del bloque (subsidio) para una altura dada,
    aplicando la regla de halving.
    """
    def __init__(self, consensus_config: ConsensusConfig):
        self.initial_subsidy = consensus_config.initial_subsidy
        self.halving_interval = consensus_config.halving_interval

    def get_subsidy(self, block_height: int) -> int:
        """
        Retorna la recompensa base en Albas (entero) para la altura del bloque.
        """
        if block_height < 0:
            return 0
            
        # Determinar cuántos halvings han ocurrido
        halvings_count = block_height // self.halving_interval
        
        # El subsidio se reduce a la mitad en cada intervalo.
        # La recompensa base es siempre un ENTERO (Albas)
        subsidy_albas = self.initial_subsidy >> halvings_count 
        
        return subsidy_albas