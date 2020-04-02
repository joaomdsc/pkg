#!/usr/bin/python
# aptmd.py - get a repository's metadata

"""Create  apython representation of debian's Package file."""

import sys
from lzma import LZMAFile
import apt_data_set

#-------------------------------------------------------------------------------
# Aptmd - metadat = package description
#-------------------------------------------------------------------------------

class Aptmd():
    def __init__(self):
        self.packages = []

    def parse_file(f):
        pkgs = []
        d = {}
        for line in f:
            line = line.strip()
            if line == '':
                # Blank/empty line finishes a package description
                ds = apt_data_set.DataSet(**d)
                pkgs.append(ds)
                d = {}
                continue
            try:
                fields = line.split(':', maxsplit=1)
                name = fields[0].strip().lower().replace('-', '_')
                value = fields[1].strip()
                d[name] = value
            except IndexError:
                print(f'IndexError: line="{line}""')
        # I'm assuming there's a last blank line at the end of the file
        return pkgs

    @classmethod
    def from_file(cls, filepath):
        """Return a Aptmd instance from a Packages.xz file."""
        # with LZMAFile(filepath, 'r') as f:
        with open(filepath, 'r') as f:
            pkgs =  Aptmd.parse_file(f)
        md = cls()
        md.packages = pkgs

        return md

    def to_csv(self, filepath):
        with open(filepath, 'w') as f:
            f.write(apt_data_set.DataSet.csv_header() + '\n')
            for ds in self.packages:
                f.write(ds.to_csv() + '\n')

#-------------------------------------------------------------------------------
# Helper functions
#-------------------------------------------------------------------------------
                
def get_names_from_package_file(filepath):
    d = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line == '':
                continue
            fields = line.split(':', maxsplit=1)
            name = fields[0].strip().lower().replace('-', '_')
            d[name] = None
    return d

def get_names_from_doc(filepath):
    d = {}
    with open(filepath, 'r') as f:
        for line in f:
            name = line.strip()
            d[name] = None
    return d

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    # print("""This module is not meant to run directly.""")
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <filepath>')
        exit(-1)
    filepath = sys.argv[1]

    md = Aptmd.from_file(filepath)
    md.to_csv('deb_pkgs.txt')

    # # Get the entire list of filed names: merge the ilst I got from debian's
    # # documentation with what I extract from this Package file.
    
    # d1 = get_names_from_package_file(filepath)
    # d2 = get_names_from_doc('names_from_doc.txt')
    # print(f'Package file: {len(d1)} names, debian doc: {len(d2)} names.')

    # d1.update(d2)
    # print(f'Merged: {len(d1)} names')

    # with open('apt_data_set_params.txt', 'w') as f:
    #     for name in d1:
    #         f.write(name + '\n')

        