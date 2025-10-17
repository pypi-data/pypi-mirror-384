__doc__ = """
An API for working with Bladed results.
"""

import sys

if not sys.version_info.major == 3 or not sys.version_info.minor >= 9:
    raise ImportError("Unsupported Python version: 3.9 or greater is required.")

is_64bits:bool = sys.maxsize > 2**32

if sys.version_info.minor == 9 :
    if is_64bits == True:
        from .python_39_x64.ResultsAPI_Python import *
    else:
        from .python_39_x86.ResultsAPI_Python import *
elif sys.version_info.minor == 10:
    if is_64bits:
        from .python_310_x64.ResultsAPI_Python import *
    else:
        from .python_310_x86.ResultsAPI_Python import *
elif sys.version_info.minor == 11:
    if is_64bits:
        from .python_311_x64.ResultsAPI_Python import *
    else:
        from .python_311_x86.ResultsAPI_Python import *
elif sys.version_info.minor == 12:
    if is_64bits:
        from .python_312_x64.ResultsAPI_Python import *
    else:
        from .python_312_x86.ResultsAPI_Python import *
elif sys.version_info.minor == 13:
    if is_64bits:
        from .python_313_x64.ResultsAPI_Python import *
    else:
        from .python_313_x86.ResultsAPI_Python import *
elif sys.version_info.minor == 14:
    if is_64bits:
        from .python_314_x64.ResultsAPI_Python import *
    else:
        from .python_314_x86.ResultsAPI_Python import *
else:
    raise ImportError("Unsupported Python version: currently only 3.9 to 3.14 is supported.")