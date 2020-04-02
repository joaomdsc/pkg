#!/usr/bin/python
# repomd.py - get a repository's metadata

"""First get the metalink.xml file with the list of mirrors. Pick one, then
retrieve repomd.xml from it. There's a list of data types, retrieve primary.

"""

import os
import re
import requests
from lxml import etree
from lfs.checksum import Checksum

#-------------------------------------------------------------------------------
# DataSet - 
#-------------------------------------------------------------------------------

class DataSet():
    # type, checksum, location, timestamp, size: mandatory...
    def __init__(self, type, checksum, location, timestamp, size,
                 open_checksum=None, open_size=None, header_checksum=None,
                    header_size=None, database_version=None):
        self.type = type
        self.checksum = checksum
        self.location = location
        self.timestamp = timestamp
        self.size = size
        if open_checksum:
            self.open_checksum = open_checksum
        if open_size:
            self.open_size = open_size
        if header_checksum:
            self.header_checksum = header_checksum
        if header_size:
            self.header_size = header_size
        if database_version:
            self.database_version = database_version

    def __str__(self):
        s = ''
        s += f'type: {self.type}\n'
        s += f'    checksum: {self.checksum.value}\n'
        s += f'    location: {self.location}\n'
        s += f'    timestamp: {self.timestamp}\n'
        s += f'    size: {self.size}\n'
        if hasattr(self, 'open_checksum'):
            s += f'    open_checksum: {self.open_checksum.value}\n'
        if hasattr(self, 'open_size'):
            s += f'    open_size: {self.open_size}\n'
        if hasattr(self, 'header_checksum'):
            s += f'    header_checksum: {self.header_checksum.value}\n'
        if hasattr(self, 'header_size'):
            s += f'    header_size: {self.header_size}\n'
        if hasattr(self, 'database_version'):
            s += f'    database_version: {self.database_version}\n'
        return s

    def to_csv(self):
        o_sum = self.open_checksum.value if hasattr(self, 'open_checksum') else ''
        o_sz = self.open_size if hasattr(self, 'open_size') else ''
        h_sum = self.header_checksum.value if hasattr(self, 'header_checksum') else ''
        h_sz = self.header_size if hasattr(self, 'header_size') else ''
        db_ver = self.database_version if hasattr(self, 'database_version') else ''

        return (f'{self.type}\t{self.checksum.value}\t{self.location}'
                    + f'\t{self.timestamp}\t{self.size}\t{o_sum}\t{o_sz}'
                    + f'\t{h_sum}\t{h_sz}\t{db_ver}')

    @classmethod
    def csv_header(cls):
        return ('type\tchecksum\tlocation\ttimestamp\tsize\topen_checksum'
                    + '\topen_size\theader_checksum\theader_size'
                    + f'\tdatabase_version')

    def location_checks(self):
        t = self.type
        v = self.checksum.value
        
        if t.startswith('group'):
            loc = f'repodata/{v}-comps-Everything.x86_64.xml'
            if t.endswith('_xz'):
                loc += '.xz'
            elif t.endswith('_zck'):
                loc += '.zck'
        elif t.endswith('_db'):
            loc = f'repodata/{v}-{t[:-3]}.sqlite.xz'
        elif t.endswith('_zck'):
            loc = f'repodata/{v}-{t[:-4]}.xml.zck'
        else:
            loc = f'repodata/{v}-{t}.xml.gz'
        # print(f'     loc={loc}')
        # print(f'location={self.location}')
        return loc == self.location

#-------------------------------------------------------------------------------
# Repomd - metalinks for repository metadata access
#-------------------------------------------------------------------------------

class Repomd():
    def __init__(self, revision):
        self.revision = revision
        self.data_sets = []

    def __str__(self):
        s = f'{self.revision}\n'
        for ds in self.data_sets:
            s += f'{ds}\n'
        return s

    def to_csv(self, filepath):
        with open(filepath, 'w') as f:
            f.write(DataSet.csv_header() + '\n')
            for ds in self.data_sets:
                f.write(ds.to_csv() + '\n')

    def handle_data(nd):
        type = nd.attrib['type']

        open_checksum = None
        open_size = None
        header_checksum = None
        header_size = None
        database_version = None
        
        for k in nd:
            tag = etree.QName(k.tag).localname
            
            if tag == 'checksum':
                checksum = Checksum(k.attrib['type'], k.text)
            elif tag == 'open-checksum':
                open_checksum = Checksum(k.attrib['type'], k.text)
            elif tag == 'location':
                location = k.attrib['href']
            elif tag == 'timestamp':
                timestamp = k.text
            elif tag == 'size':
                size = int(k.text)
            elif tag == 'open-size':
                open_size = int(k.text)
            elif tag == 'header-checksum':
                header_checksum = Checksum(k.attrib['type'], k.text)
            elif tag == 'header-size':
                header_size = int(k.text)
            elif tag == 'database_version':
                database_version = k.text

        ds = DataSet(type, checksum, location, timestamp, size,
                       open_checksum=open_checksum, open_size=open_size,
                       header_checksum=header_checksum, header_size=header_size,
                           database_version=database_version)
        if not ds.location_checks():
            print('Location check failed')
        return ds

    def parse_root(nd):
        for k in nd:
            tag = etree.QName(k.tag).localname
            if tag == 'revision':
                md = Repomd(k.text)
            elif tag == 'data':
                ds = Repomd.handle_data(k)
                md.data_sets.append(ds)
        return md

    @classmethod
    def from_file(cls, filepath):
        """Return a Repomd instance from a repomd.xml file."""
        root = etree.parse(filepath).getroot()
        return Repomd.parse_root(root)

    def get_pkg_lists(self, root_url):
        for ds in self.data_sets:
            url = f'{root_url}/{ds.location}'
            print(f'type={ds.type}, sz={ds.size}, url={url}')
            if ds.type == 'primary':
                print(f'  Retrieving primary: "{url}"')
                response = requests.get(url)

                filename = url.rsplit('/', maxsplit=1)[1]
                with open(filename, 'wb') as f:
                    f.write(response.content)

                print(f'  Checksum: {"ok" if ds.checksum.check(filename) else "NOK"}')

if __name__ == '__main__':
    print("""This module is not meant to run directly.""")
