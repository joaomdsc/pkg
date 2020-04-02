#!/usr/bin/python
# apt_runner.py - front-end for the apt modules

import sys
import requests

from apt_repo import Source
from repomd import Repomd

#-------------------------------------------------------------------------------
# I want stdout to be unbuffered, always
#-------------------------------------------------------------------------------

class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

sys.stdout = Unbuffered(sys.stdout)
#-------------------------------------------------------------------------------

# Check cmd line args
if len(sys.argv) != 2:
    print(f'Usage: {sys.argv[0]} <filepath>')
    exit(-1)
filepath = sys.argv[1]

srcs = Source.from_file(filepath)
for s in srcs:
    print('---------------------------------------------')
    print(s)
