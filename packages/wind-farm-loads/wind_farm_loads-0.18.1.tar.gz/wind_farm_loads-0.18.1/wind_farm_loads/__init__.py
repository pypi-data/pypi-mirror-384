import importlib.metadata

import jax

__version__ = importlib.metadata.version(__name__)

# Allow JAX to operate in double precision.
# 32 bit float can still be used.
jax.config.update("jax_enable_x64", True)
