# Require python 3

import sys

min_ver = ( 3, 6 )

exitcode = 0
py_ver = ( sys.version_info[0:2] )
if py_ver < min_ver:
    exitcode=1
sys.exit( exitcode )
