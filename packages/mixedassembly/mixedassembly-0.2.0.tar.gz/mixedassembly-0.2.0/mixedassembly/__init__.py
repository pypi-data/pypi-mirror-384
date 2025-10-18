"""
mixedassembly package
Author: Germán Vallejo Palma
Developed at: Instituto de Salud Carlos III - National Centre of Microbiology
"""

__version__ = "0.2.0"
__author__ = "Germán Vallejo Palma"
__email__ = "german.vallejo@isciii.es"

# Expose key functions/modules for convenience
from .remove_frameshifts import run as remove_frameshifts_run
from .build_priors import main as build_priors_main
from .run_mixed_assembly import main as run_mixed_assembly_main
