# -*- coding: utf-8 -*-
"""
Basic import of gimli core extension.
"""


# start delvewheel patch
def _delvewheel_patch_1_11_2():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'pgcore.libs'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_11_2()
del _delvewheel_patch_1_11_2
# end delvewheel patch

import sys, os

if sys.platform == 'win32':
    os.environ['PATH'] = os.path.join(os.path.dirname(__file__), 'libs') + ':' + os.environ['PATH']
    #print(os.environ['LD_LIBRARY_PATH'])
elif sys.platform == 'linux':
    if os.getenv('LD_LIBRARY_PATH'):
        os.environ['LD_LIBRARY_PATH'] = os.path.join(os.path.dirname(__file__), 'libs') + ':' + os.environ['LD_LIBRARY_PATH']
    #print(os.environ['LD_LIBRARY_PATH'])

_pygimli_ = None

try:
    # from . import _pygimli_
    # from ._pygimli_ import *

    from .libs import _pygimli_ as pgcore  
    from .libs._pygimli_ import *  

except ImportError as e:
    import traceback
    print(e)
    traceback.print_exc(file=sys.stdout)
    sys.stderr.write("ERROR: cannot import the library '_pygimli_'.\n")
