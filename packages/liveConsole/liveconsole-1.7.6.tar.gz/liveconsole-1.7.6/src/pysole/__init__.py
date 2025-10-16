from .pysole import probe, _standalone, InteractiveConsole
import sys

sys.modules['liveConsole'] = sys.modules[__name__]