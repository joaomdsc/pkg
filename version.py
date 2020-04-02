#!/usr/bin/python
# version.py - 

import os
import re
from lxml import etree

#-------------------------------------------------------------------------------
# Version - 
#-------------------------------------------------------------------------------

class Version():
    def __init__(self, epoch, ver, rel):
        self.epoch = epoch
        self.ver = ver
        self.rel = rel

    def __str__(self):
        return f'version: epoch={self.epoch}, ver={self.ver}, rel={self.rel}\n'

    def to_csv(self):
        return f'{self.epoch}\t{self.ver}\t{self.rel}'

    @classmethod
    def csv_header(cls):
        return f'epoch\tver\trel'

if __name__ == '__main__':
    print("""This module is not meant to run directly.""")
