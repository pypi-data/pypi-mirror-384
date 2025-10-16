import warnings
warnings.warn(
    "Module 'liveConsole' is deprecated. Use 'pysole' instead.",
    DeprecationWarning,
    stacklevel=2
)

from .pysole import *