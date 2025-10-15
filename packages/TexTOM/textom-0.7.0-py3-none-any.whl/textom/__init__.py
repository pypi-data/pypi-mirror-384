# textom/__init__.py
import pkgutil
import importlib
import psutil
import os
from threadpoolctl import threadpool_limits

from .src.misc import get_affinity_info
from .config import n_threads
from .version import __version__

# parallelisation settings
aff_info = get_affinity_info() # this is to avoid conflicts with parallelisation via taskset
if not aff_info['restricted']:
    # set everything to single threaded
    threadpool_limits(limits=1)
    os.environ["MKL_NUM_THREADS"] = "1" 
    os.environ["NUMEXPR_NUM_THREADS"] = "1" 
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    from numba import set_num_threads
    n_threads = min(psutil.cpu_count(), n_threads) # make sure the number of threads doesn't exceed the possible ones
    set_num_threads(n_threads)

# import textom modules
__all__ = []
for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    if module_name == 'textom':  # Restrict to the textom module
        module = importlib.import_module(f"{__name__}.{module_name}")
        for name in dir(module):
            if not name.startswith("_"):  # Skip private attributes
                globals()[name] = getattr(module, name)
                __all__.append(name)

# Set package metadata
__author__ = "Moritz Frewein, Moritz Stammer, Marc Allain, Tilman Gruenewald"
__email__ = "textom@fresnel.fr"
