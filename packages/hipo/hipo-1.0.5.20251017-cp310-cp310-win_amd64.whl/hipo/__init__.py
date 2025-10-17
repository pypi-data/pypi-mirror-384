import sys, os

if sys.platform == "win32":
    os.add_dll_directory(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

from hipo._pyhipo import *
from hipo._pyhipo.dtype.float64 import *

del os, sys
