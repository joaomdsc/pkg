#!/usr/bin/python
# apt_repo.py - object representation of a repo definition

"""This module implements a python representation of the apt repository
descriptions found in Debian 10, in /etc/apt/sources.list.
"""

import os
import re
import sys

#-------------------------------------------------------------------------------
# Source: 
#-------------------------------------------------------------------------------

class Source():
    """This class represents one repository description.

    These descriptions are found in the sources.list file. Each file
    contains several descriptions. Currently we implement the
    one-line-style format only.name
"""
    def __init__(self, type=None, uri=None, suite=None):
        self.type = type
        self.uri = uri
        self.suite = suite
        self.components = []

    def __str__(self):
        s = ''
        s += f'type: {self.type}\n'
        s += f'uri: {self.uri}\n'
        s += f'suite: {self.suite}\n'
        s += f"components: {', '.join(self.components)}"
        return s

    #---------------------------------------------------------------------------
    # Create Source instances from .repo files (in .ini format)
    #---------------------------------------------------------------------------

    @classmethod
    def from_file(cls, filepath):
        """Return an array of Source instances from a .list file."""
        srcs = []
        with open(filepath, 'r') as f:
            for line in f:
                # A '#' character anywhere on a line marks the remainder of
                # that line as a comment
                m = re.match('([^#]*)#', line)
                if m:
                    # Start a new repo
                    line = m.group(1)
                line = line.strip()
                if line == '':
                    # Empty lines are ignored
                    continue
                
                # Ignoring options for now
                fields = line.split()
                type = fields[0]
                uri = fields[1]
                suite = fields[2]
                comps = fields[3:]
                
                src = cls(type, uri, suite)
                src.components = comps
                srcs.append(src)
        return srcs

    #---------------------------------------------------------------------------
    # Get the repomd.xml file (called Packages.xz) for this repository
    #---------------------------------------------------------------------------

    def get_repomd(self, component, arch):
        # Using uri, suite, component, arch, build the URL for the Packages
        # file. Retrieve it. Check it ? Write it to file, then parse it and
        # create the python objects.
        url = f'{self.uri}dists/{suite}/{component}/binary-{arch}/Packages.xz'
        print(f'Retrieving: "{url}"')
        response = requests.get(url)

        # Write out the Packages.xz file
        filename = f'{self.suite}_{component}_Packages.xz'
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        # Create the object from the file
        return Sourcesmd.from_file(filename)

if __name__ == '__main__':
    # print("""This module is not meant to run directly.""")
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <filepath>')
        exit(-1)
    filepath = sys.argv[1]

    srcs = Source.from_file(filepath)
    # for s in srcs:
    #     print('---------------------------------------------')
    #     print(s)
