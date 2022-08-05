#!/usr/bin/env python3
'''
Example program
read+eval input and emit errors
integer number N: eat N kilobytes of memory
float number N: wait N seconds
Exception: raise an exception
other: print the input
'''

import sys
import time

for s in sys.stdin:
    v = eval(s)
    if type(v) is int:
        res = list(range(v*1024//8))
        print(sys.getsizeof(res))
    elif type(v) is float:
        time.sleep(v)
        print(v, v)
    elif isinstance(v, Exception): # or issubclass(v, Exception):
        raise v
    else:
        print(v)
