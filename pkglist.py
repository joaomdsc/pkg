#!/usr/bin/python
# pkglist.py - get a repository's metadata, the actual list of packages

import os
import re
import sys
from lxml import etree

from version import Version
from lfs.checksum import Checksum

#-------------------------------------------------------------------------------
# PkgTime - 
#-------------------------------------------------------------------------------

class PkgTime():
    def __init__(self, file, build):
        self.file = file
        self.build = build

    def __str__(self):
        return f'time: file={self.file}, build={self.build}\n'

    def to_csv(self):
        return f'{self.file}\t{self.build}'

    @classmethod
    def csv_header(cls):
        return f'file\tbuild'

#-------------------------------------------------------------------------------
# Size - 
#-------------------------------------------------------------------------------

class Size():
    def __init__(self, package, archive, installed):
        self.package = package
        self.archive = archive
        self.installed = installed

    def __str__(self):
        return (f'size: package={self.package}, archive={self.archive}'
                    + f', installed={self.installed}\n')

    def to_csv(self):
        return f'{self.package}\t{self.archive}\t{self.installed}'

    @classmethod
    def csv_header(cls):
        return f'package\tarchive\tinstalled'

#-------------------------------------------------------------------------------
# Pkg - 
#-------------------------------------------------------------------------------

class Pkg():
    def __init__(self, type, name, arch, version, checksum, summary, description,
                 packager, url, pkg_time, size, location, format):
        self.type = type
        self.name = name
        self.arch = arch
        self.version = version
        self.checksum = checksum
        self.summary = summary
        self.description = description
        self.packager = packager
        self.url = url
        self.pkg_time = pkg_time
        self.size = size
        self.location = location
        self.format = format

    def __str__(self):
        s = f'{self.name}\n'
        s += f'    type: {self.type}\n'
        s += f'    arch: {self.arch}\n'
        s += f'    {str(self.version)}'
        s += f'    {str(self.checksum)}'
        s += f'    summary: {self.summary}\n'
        s += f'    description: {self.description}\n'
        s += f'    packager: {self.packager}\n'
        s += f'    url: {self.url}\n'
        s += f'    {str(self.pkg_time)}'
        s += f'    {str(self.size)}'
        s += f'    location: {self.location}\n'
        s += '\n'
        return s

    def to_csv(self):
        # Don't put multiline values in cells 
        x = self.description.split('\n', maxsplit=1)[0] if self.description else ''
        s = f'{self.name}\t{self.type}\t{self.arch}'
        s += f'\t{self.version.to_csv()}'
        s += f'\t{self.checksum.to_csv()}'
        # s += f'\t{self.summary}\t{self.description}\t{self.packager}\t{self.url}'
        s += f'\t{self.summary}\t{x}\t{self.packager}\t{self.url}'
        s += f'\t{self.pkg_time.to_csv()}\t{self.size.to_csv()}'
        s += f'\t{self.location}'
        return s

    @classmethod
    def csv_header(cls):
        s = f'name\ttype\tarch'
        s += f'\t{Version.csv_header()}'
        s += f'\t{Checksum.csv_header()}'
        s += f'\tsummary\tdescription\tpackager\turl'
        s += f'\t{PkgTime.csv_header()}\t{Size.csv_header()}'
        s += f'\tlocation'
        return s

#-------------------------------------------------------------------------------
# PkgList - metalinks for repository metadata access
#-------------------------------------------------------------------------------

class PkgList():
    def __init__(self):
        self.packages = []

    def __str__(self):
        s = ''
        for p in self.packages:
            s += f'{p}'
        return s

    def to_csv(self, filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f'{Pkg.csv_header()}\n')
            for p in self.packages:
                f.write(f'{p.to_csv()}\n')

    def handle_pkg(nd):
        type = nd.attrib['type']
        
        for k in nd:
            tag = etree.QName(k.tag).localname

            # Store in local variables during the 'for' loop
            if tag == 'name':
                name = k.text
            if tag == 'arch':
                arch = k.text
            if tag == 'version':
                version = Version(k.attrib['epoch'], k.attrib['ver'], k.attrib['rel'])
            if tag == 'checksum':
                checksum = Checksum(k.attrib['type'], k.text, pkgid=k.attrib['pkgid'])
            elif tag == 'summary':
                summary = k.text
            elif tag == 'description':
                description = k.text
            elif tag == 'packager':
                packager = k.text
            elif tag == 'url':
                url = k.text
            elif tag == 'time':
                pkg_time = PkgTime(k.attrib['file'], k.attrib['build'])
            elif tag == 'size':
                size = Size(k.attrib['package'], k.attrib['archive'],
                            k.attrib['installed'])
            elif tag == 'location':
                location = k.attrib['href']

        p = Pkg(type, name, arch, version, checksum, summary, description,
                           packager, url, pkg_time, size, location, None)
        return p


    def parse_root(nd):
        pl= PkgList()
        for k in nd:
            tag = etree.QName(k.tag).localname
            if tag == 'package':
                p = PkgList.handle_pkg(k)
                pl.packages.append(p)
        return pl

    @classmethod
    def from_file(cls, filepath):
        """Return a PkgList instance from a primary.xml file."""
        root = etree.parse(filepath).getroot()
        return PkgList.parse_root(root)

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    # print("""This module is not meant to run directly.""")
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <filepath>')
        exit(-1)
    filepath = sys.argv[1]

    print(f'Parsing file "{filepath}"')
    pl = PkgList.from_file(filepath)
    print(f'Parsing done, found {len(pl.packages)} packages.')

    # # Print out a text output
    # print(f'String to be printed is {len(str(pl))} bytes long.')
    # filename = 'toto.txt'
    # print(f'Printing to file {filename}')
    # with open(filename, 'w', encoding='utf-8') as f:
    #     f.write(str(pl))

    # Create a .csv file
    print(f'Creating file toto.txt')
    pl.to_csv('toto.txt')
