from . import *
import coloredlogs #type: ignore
# default colored logs level.
# You may override it by doing the same thing with 'DEBUG' after importing deeplabel once
coloredlogs.install('INFO') #type: ignore
__version__ = '1.1.0'