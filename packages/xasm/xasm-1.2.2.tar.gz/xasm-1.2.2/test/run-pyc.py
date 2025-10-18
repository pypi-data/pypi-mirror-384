#!/usr/bin/env python
# Read in a pyc file and execute it.
import sys
from xdis import load_module
import types
pyc_file = sys.argv[1]
(version, timestamp, magic_int, co, is_pypy,
 source_size) = load_module(pyc_file)
print(type(co))
if not isinstance(co, types.CodeType):
    if hasattr(co, "to_native"):
        co = co.to_native()
    else:
        raise RuntimeError("code type not executable")
exec(co)
