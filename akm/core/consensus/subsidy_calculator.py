# akm/core/consensus/subsidy_calculator.py

import logging
from akm.core.config.consensus_config import ConsensusConfig

logger = logging.getLogger(__name__)

class SubsidyCalculator:
    
    def __init__(self, consensus_config: ConsensusConfig) -> None:
        try:
            self.initial_subsidy = consensus_config.initial_subsidy
            self.halving_interval = consensus_config.halving_interval
            logger.info("Calculador de subsidios activo.")
        except Exception:
            logger.exception("Error al inicializar SubsidyCalculator")

    def get_subsidy(self, block_height: int) -> int:
    
        try:
            if block_height < 0:
                return 0
                
            halvings_count = block_height // self.halving_interval
            
            subsidy_albas = self.initial_subsidy >> halvings_count 
            
            if block_height > 0 and block_height % self.halving_interval == 0:
                logger.info(f"⚡ ¡HALVING detectado! Nueva recompensa: {subsidy_albas} Albas.")

            return subsidy_albas

        except Exception:
            logger.exception(f"Bug en cálculo de subsidio para altura {block_height}")
            return 0