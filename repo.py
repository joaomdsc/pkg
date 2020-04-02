#!/usr/bin/python
# repo.py - object representation of a repo definition

"""This module implements a python representation of the dnf repository
descriptions found in Fedora 29, in /etc/yum.repos.d. The syntax and semantics
of the file contents are found in
https://dnf.readthedocs.io/en/latest/conf_ref.html."""

import os
import re
import requests
import checksum
from metalink import Metalink
from repomd import Repomd

#-------------------------------------------------------------------------------
# Repo: 
#-------------------------------------------------------------------------------

class Repo():
    """This class represents one repository description.

    These descriptions are found in the .repo files in
    /etc/yum.repos.d. Each file contains several descriptions.
"""
    def __init__(self, repo_id, name=None, baseurl=None, type=None,
            metalink=None, enabled=None, enabled_metadata=None,
            metadata_expire=None, repo_gpgcheck=None, gpgcheck=None,
            gpgkey=None, skip_if_unavailable=None, failovermethod=None):
        self.repo_id = repo_id
        # The object instance will always have all of the properties, even the
        # optional ones that were not specified in the call to __init__.
        self.name = name
        self.baseurl = baseurl
        self.type = type
        self.metalink = metalink
        self.enabled = enabled
        self.enabled_metadata = enabled_metadata
        self.metadata_expire = metadata_expire
        self.repo_gpgcheck = repo_gpgcheck
        self.gpgcheck = gpgcheck
        self.gpgkey = gpgkey
        self.skip_if_unavailable = skip_if_unavailable
        self.failovermethod = failovermethod
        self.root_url = None
        self.repo_md = None

    def __str__(self):
        s = f'repo_id: {self.repo_id}\n'
        s += f'    name: {self.name}\n'
        if self.baseurl:  # False when None 
            s += f'    baseurl: {self.baseurl}\n'
        if self.metalink:
            s += f'    metalink: {self.metalink}\n'
        if self.metadata_expire:
            s += f'    metadata_expire: {self.metadata_expire}\n'
        return s

    #---------------------------------------------------------------------------
    # Generate the text data for a .csv file
    #---------------------------------------------------------------------------

    def to_csv(self):
        s = f'{self.name}'
        s += f';{self.baseurl if self.baseurl else ""}'
        s += f';{self.type if self.type else ""}'
        s += f';{self.metalink if self.metalink else ""}'
        s += f';{self.enabled if self.enabled else ""}'
        s += f';{self.enabled_metadata if self.enabled_metadata else ""}'
        s += f';{self.metadata_expire if self.metadata_expire else ""}'
        s += f';{self.repo_gpgcheck if self.repo_gpgcheck else ""}'
        s += f';{self.gpgcheck if self.gpgcheck else ""}'
        s += f';{self.gpgkey if self.gpgkey else ""}'
        s += f';{self.skip_if_unavailable if self.skip_if_unavailable else ""}'
        s += f';{self.failovermethod if self.failovermethod else ""}'
        return s

    @classmethod
    def csv_header(cls):
        return ('name;baseurl;type;metalink;enabled;enabled_metadata'
                    + ';metadata_expire;repo_gpgcheck;gpgcheck;gpgkey'
                    + ';skip_if_unavailable;failovermethod')

    #---------------------------------------------------------------------------
    # Create a .csv file with all the repository descriptions
    #---------------------------------------------------------------------------

    @classmethod
    def to_csv_from_dir(cls, dirpath):
        """Output a .csv file from a directory of .repo files."""
        repos = Repo.from_dir(dirpath)
        print(Repo.csv_header())
        for r in repos:
            print(r.to_csv())

    #---------------------------------------------------------------------------
    # Create Repo instances from .repo files (in .ini format)
    #---------------------------------------------------------------------------

    @classmethod
    def from_file(cls, filepath):
        """Return an array of Repo instances from a .repo file."""
        repos = []
        with open(filepath, 'r') as f:
            on_going_repo = False
            for line in f:
                line = line.strip()
                m = re.match(r'\[([a-zA-Z0-9_.:-]+)\]', line)
                if m:
                    # Start a new repo
                    on_going_repo = True
                    repo_id = m.group(1)
                    d = {}
                    continue
                if line == '':
                    if on_going_repo:
                        # current repo is over
                        r = cls(repo_id, **d)
                        repos.append(r)
                        on_going_repo = False
                    continue
                if line[0] == '#':
                    # FIXME: is this really a comment ? Get the repo file spec.
                    continue
                # I'm assuming that the key will never have a '=' character.
                k, v = line.split('=', maxsplit=1)
                d[k] = v
                # When leaving the 'for' loop, there may be a current repo
            if on_going_repo:
                r = cls(repo_id, **d)
                repos.append(r)
        return repos

    #---------------------------------------------------------------------------
    # Create Repo instances from a directory of .repo files
    #---------------------------------------------------------------------------

    @classmethod
    def from_dir(cls, dirpath):
        """Return an array of Repo instances from a directory of .repo files."""
        repos = []
        for f in os.listdir(dirpath):
            if f.endswith('.repo'):
                repos.extend(Repo.from_file(os.path.join(dirpath, f)))
        return repos

    #---------------------------------------------------------------------------
    # Get the repomd.xml file for this repository
    #---------------------------------------------------------------------------

    def get_repomd(self):
        # The URL for the repomd.xml file
        url = None
        
        if self.metalink:
            # Using the mirrors is the preferred approach
            url = self.metalink.replace('$releasever', '31')
            url = url.replace('$basearch', 'x86_64')
            print(f'Retrieving metalink: "{url}"')
            response = requests.get(url)

            # Write out the XML file
            filename = f'{self.repo_id}_metalink.xml'
            with open(filename, 'w') as f:
                f.write(response.text)
 
            # Get the location of the repo's data set information
            ml = Metalink.from_file(filename)
            url = ml.get_best_data_url()
            m = re.match('(.*)/repodata/repomd\.xml', url)
            if not m:
                print(f'Incorrect url: {url}')
                return
            url = m.group(1)
        elif self.baseurl:
            # Docker CE, Google Chrome... use this mchanisms, with no mirrors.
            url = f'{self.baseurl}'.replace('$releasever', '31')
            url = url.replace('$basearch', 'x86_64')
        else:
            print(f'Neither metalink nor baseurl found in {self.repo_id}')
            return

        # Example from Fedora
        # http://distrib-coffee.ipsl.jussieu.fr/pub/linux/fedora/linux/releases/31/Everything/x86_64/os/repodata/repomd.xml

        # self.root_url does not have a traling slash '/'. All other URLs will
        # be based on it:
        #
        #     {self.root_url}/repodata/repomd.xml
        #     {self.root_url}/repodata/87aea7f[...]f7-primary.xml.gz
        #     {self.root_url}/Packages/0/...
        self.root_url = url

        # Get the actual file
        url = f'{self.root_url}/repodata/repomd.xml'
        print(f'Retrieving repomd: "{url}"')
        response = requests.get(url)
        filename = f'{self.repo_id}_repomd.xml'

        # On Windows, the line endings get changed whitout the 'newline' arg
        with open(filename, 'w', newline='\n') as f:
            f.write(response.text)

        # Check the file size and checksum, if we know what to expect
        if self.metalink:
            # Check the size of the actual fle on disk, not response.text
            l = os.stat(filename).st_size
            # print(f'File size: expected={ml.size}, actual={l}')
            print(f'File size: {"ok" if ml.size == l else "NOK"}')

            # Check all the secure hashes defined in the metalink
            for h in ml.hashes:
                if h.check(filename):
                    print(f'Checksum {h.type}: ok')
                else:
                    print(f'Checksum {h.type}: NOK')

        # Create the object from the file
        return Repomd.from_file(filename)

if __name__ == '__main__':
    print("""This module is not meant to run directly.""")
