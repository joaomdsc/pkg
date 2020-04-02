#!/usr/bin/python
# pkgformat.py - 

import os
import re
from lxml import etree

from version import Version

#-------------------------------------------------------------------------------
# HeaderRange - 
#-------------------------------------------------------------------------------

class HeaderRange():
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __str__(self):
        return f'header-range: start={self.start}, end={self.end}\n'

    def to_csv(self):
        return f'\\t{self.start}\t{self.end}'

    @classmethod
    def csv_header(cls):
        return f'\tstart\tend'

#-------------------------------------------------------------------------------
# DepsEntry - 
#-------------------------------------------------------------------------------

class DepsEntry():
    def __init__(self, name, flags):
        self.name = name
        self.flags = flags
        self.version = version

    def __str__(self):
        return f'entry: name={self.name}, flags={self.flags}\n'

    def to_csv(self):
        return f'{self.name}\t{self.flags}'

    @classmethod
    def csv_header(cls):
        return f'\tname\tflags'

#-------------------------------------------------------------------------------
# PkgFormat - 
#-------------------------------------------------------------------------------

class PkgFormat():
    def __init__(self, licence, vendor, group, buildhost, sourcerpm,
                 header_range
                 ):
        self.licence = licence
        self.vendor = vendor
        self.group = group
        self.buildhost = buildhost
        self.sourcerpm = sourcerpm
        self.header_range = header_range

    def __str__(self):
        s = ''
        s += f'licence: {self.licence}\n'
        s += f'vendor: {self.vendor}\n'
        s += f'group: {self.group}\n'
        s += f'buildhost: {self.buildhost}\n'
        s += f'sourcerpm: {self.sourcerpm}\n'
        s += f'header_range: {str(self.header_range)}\n'
        return s

    def to_csv(self):
        s = f'{self.licence}\t{self.vendor}\t{self.group}\t{self.buildhost}'
        s += f'\t{self.sourcerpm}\t{self.header_range.to_csv()}'
        return s

    @classmethod
    def csv_header(cls):
        s = f'licence\tvendor\tgroup\tbuildhost\tsourcerpm'
        s += + f'\t{HeaderRange.csv_header()}'
        return s

if __name__ == '__main__':
    print("""This module is not meant to run directly.""")
