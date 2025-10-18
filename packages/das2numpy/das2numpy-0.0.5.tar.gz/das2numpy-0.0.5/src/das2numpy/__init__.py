""" Module for efficient loading of both optasense and silixa data data.
    @author: Erik genthe
"""

import os as OS
import numpy as NP
from . import utils


def loader(root_path:str, predefined_setup:str, num_worker_threads):

    if predefined_setup.upper() == "SILIXA":
        from .setups import silixa
        chunk = silixa.init(root_path, num_worker_threads)
    elif predefined_setup.upper() == "SILIXA_200HZ":
        from .setups import silixa_200hz
        chunk = silixa_200hz.init(root_path, num_worker_threads)
    elif predefined_setup.upper() == "OPTASENSE":
        from .setups import optasense_b35idefix
        chunk = optasense_b35idefix.init()
    else:
        raise RuntimeError("Unknown setup: ", predefined_setup)
    
    return chunk
        

