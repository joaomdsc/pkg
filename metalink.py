#!/usr/bin/python
# metalink.py - get a repository's metalink file

"""First get the metalink.xml file with the list of mirrors. Pick one, then
retrieve repomd.xml from it. There's a list of data types, retrieve primary.

"""

import os
import re
from lxml import etree
from lfs.checksum import Checksum

#-------------------------------------------------------------------------------
# Resource - 
#-------------------------------------------------------------------------------

class Resource():
    def __init__(self, protocol, type, location, preference, url):
        self.protocol = protocol
        self.type = type
        self.location = location
        self.preference = preference
        self.url = url

    def to_csv(self):
        return (f'{self.protocol};{self.type};{self.location};{self.preference}'
                 + f';{self.url}')

    @classmethod
    def csv_header(cls):
        return ('protocol;type;location;preference;url')

#-------------------------------------------------------------------------------
# Metalink - metalinks for repository metadata access
#-------------------------------------------------------------------------------

class Metalink():
    def __init__(self, name, timestamp=None, size=None):
        # Information on the repomd.xml file
        self.name = name
        self.timestamp = timestamp
        self.size = size
        # Checksums to verify the repomd.xml file
        self.hashes = []
        # List of URL's to download the repomd.xml file
        self.resources = []

    def __str__(self):
        s = f'{self.name}\n'
        if self.timestamp:
            s += f'  timestamp={self.timestamp}\n'
        if self.size:
            s += f'  size={self.size}\n'
        s += '  resources:\n'
        for r in self.resources:
            s += f'    {r.url}\n'

        return s

    def to_csv(self):
        print(Resource.csv_header())
        for r in self.resources:
            print(r.to_csv())
        
    def handle_verif(nd):
        # Parse the <verification> element sub-tree into an array of Checksum instances
        arr = []
        for k in nd:
            tag = etree.QName(k.tag).localname
            if tag == 'hash':
                arr.append(Checksum(k.attrib['type'], k.text))
        return arr

    def handle_file(nd):
        # Parse the <file> element sub-tree into a Metalink instance
        name = nd.attrib['name']
        ml = Metalink(name)
        
        for k in nd:
            tag = etree.QName(k.tag).localname
            if tag == 'timestamp':
                ml.timestamp = k.text
            elif tag == 'size':
                ml.size = int(k.text)
            elif tag == 'verification':
                ml.hashes = Metalink.handle_verif(k)
            elif tag == 'resources':
                res = []
                for kk in k:
                    tag = etree.QName(kk.tag).localname
                    if tag == 'url':
                        r = Resource(
                            kk.attrib['protocol'],
                            kk.attrib['type'],
                            kk.attrib['location'],
                            kk.attrib['preference'],
                            kk.text,  # url
                            )
                        res.append(r)
                ml.resources = res
        return ml

    def parse_node(nd):
        # Print this node's tag
        tag = etree.QName(nd.tag).localname

        if tag == 'file':
            return Metalink.handle_file(nd)
        # Recurse over children
        for k in nd:
            return  Metalink.parse_node(k)

    @classmethod
    def from_file(cls, filepath):
        """Return a Metalink instance from a metalink file."""
        root = etree.parse(filepath).getroot()
        return Metalink.parse_node(root)

    def get_best_data_url(self):
        r = sorted([r for r in self.resources
                    if r.protocol in ['http', 'https']],
                       key=lambda x: x.preference)[0]
        return r.url

if __name__ == '__main__':
    print("""This module is not meant to run directly.""")
