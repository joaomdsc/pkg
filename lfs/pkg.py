# pkg.py - Linux From Scratch packages

import os
import re
import sys
import json
import tarfile
import requests
from urllib.request import urlopen
from urllib.parse import urlparse
from subprocess import run, PIPE, STDOUT

import common

#-------------------------------------------------------------------------------
# Pkg - 
#-------------------------------------------------------------------------------
    
class Pkg():
    def __init__(self, name, size, url, md5, version=None, filename=None):
        self.name = name
        self.size = size
        self.url = url
        self.md5 = md5
        self.version = version
        self.filename = None
        if filename is None:
            self.filename = self.url.rsplit('/', maxsplit=1)[1]

    #---------------------------------------------------------------------------
    # JSON encode/decode
    #---------------------------------------------------------------------------
   
    def to_json_encodable(self):
        """Create a json-encodable object representing this object."""
        # print('  Pkg: to_json_encodable')
        d = {}
        for k, v in self.__dict__.items():
            if not (v is None or v == '' or v == [] or v == {}):
                d[k] = v
                
        if self.md5:
            d['md5'] = self.md5.to_json_encodable()
        return d

    @classmethod
    def from_json_decoded(cls, obj):
        """Return an LFSBook object from a json-decoded object."""
        d = {}
        # We iterate on the members actually present, ignoring absent ones.
        for k, v in obj.items():
            d[k] = v            
        return cls(**d)
    
    def download(self):
        """Download the file, if we don't have it already"""
        path = os.path.join(common.lfs_data, 'pkgs')
        if not os.path.isdir(path):
            os.mkdir(path)
        filepath = os.path.join(path, self.filename)
        if os.path.isfile(filepath):
            print(f'Already have: "{self.url}"')
        else:
            print(f'Retrieving: "{self.url}"')
            p = urlparse(self.url)
            if p.scheme in ['http', 'https']:
                response = requests.get(self.url)
                data = response.content
            elif p.scheme == 'ftp':
                with urlopen(self.url) as f:
                    data = f.read()
            else:
                print(f'Unsupported scheme "{p.scheme}"')
                return
            with open(filepath, 'wb') as f:
                f.write(data)

        # Verify the checksum
        print(f'Checksum: {"ok" if self.md5.check(filepath) else "NOK"}')

#-------------------------------------------------------------------------------
# Global functions
#-------------------------------------------------------------------------------
    
def get_lfs_file(version, filename):
    """Ensure we have the file, and return the number of lines"""
    baseurl = f'http://www.linuxfromscratch.org/lfs/downloads/{version}'
    pkgs_path = os.path.join(common.lfs_data, 'pkgs')
    filepath = os.path.join(pkgs_path, filename)
    if not os.path.isfile(filepath):
        url = f'{baseurl}/{filename}'
        r = requests.get(url)
        with open(filepath, 'w') as f:
            f.write(r.text)

    with open(filepath, 'r') as f:
        lines = f.readlines()

def non_std_subdir(filepath):
    """List tarfile contents and determine sub-directory.

    Extract from the tarfile listing the name of the sub-directory that
    will be created when the archive is extracted. Return it if it
    doesn't match the standard rule, None otherwise.
    """
    filename = filepath.rsplit('/', maxsplit=1)[1]
    try:
        with tarfile.open(filepath) as t:
            m = t.getmembers()[0]
    except tarfile.ReadError as e:
        print(f"tarfile.open: {filename}: {e}")
        return
    dir_name = m.name.split('/', maxsplit=1)[0]

    # In the standard case, the part of the archive filename before '.tar'
    # is the sub-directory name that will be created. 
    m = re.match(r'(.*)\.tar\.(gz|xz|bz2)', filename)
    if not (m and m.group(1) == dir_name):
        # Non-standard sub-directory name
        return dir_name

def get_non_std_subdirs(pkgs_path):
    # Get all the non-standard sub-directory names
    d = {}
    print('Determining archive sub-directories, this may take a while')
    for filename in os.listdir(pkgs_path):

        # tzdata2019b.tar.gz and systemd-man-pages-241.tar.xz are archive
        # files, but they're not packages to be built, they're just data for
        # other packages to use.

        # FIXME a better strategy would be: when a section tries to untar and
        # fails, list the tar file contents to determine the right
        # sub-directory name.
        dir_name = non_std_subdir(os.path.join(pkgs_path, filename))
        if dir_name:
            d[filename] = dir_name

    # Write them out to a json file
    filepath = os.path.join(pkgs_path, 'subdir_names')
    with open(filepath, 'w') as f:
        f.write(json.dumps(d, indent=4))

def get_all(version, pkgs_path):
    # We have no packages at all, get them all (pkgs + patches )at once
    print('Downloading all packages, this may take a while')

    # Some commands need to be run inside the directory holding the packages
    curr_dir = os.getcwd()
    os.chdir(pkgs_path)

    # --input-filelist is the reason why we need to be inside this dir
    get_lfs_file(version, 'wget-list')
    r = run(['wget', '--input-file=wget-list', '--continue',
             f'--directory-prefix={pkgs_path}'], stdout=PIPE, stderr=STDOUT)
    if r.returncode != 0:
        print(f'Wget returned: {r.returncode}')

    # Ensure we have the list of md5 checksums and verify them
    get_lfs_file(version, 'md5sums')
    print('Verifying all checksums')
    # md5sums is the reason why we need to be inside this dir
    r = run(['md5sum', '-c', 'md5sums'], stdout=PIPE, stderr=STDOUT)
    if r.returncode != 0:
        print(f'md5sum returned: {r.returncode}')

    # Checking results
    cnt = 0
    for line in r.stdout.decode().split('\n'):
        line = line.strip()
        if len(line) == 0:
            continue
        if not line.endswith(': OK'):
            cnt += 1
            print(f'error: line="{line}", len={len(line)}')
    if cnt:
        print('Checksum verification failed, exiting')
        exit()

    get_non_std_subdirs(pkgs_path)

    # Move back to the original directory
    os.chdir(curr_dir)

def wget_files(version, pkgs_path):
    """Ensure that we have all the correct packages for this version"""

    # Ensure we have all the package files, with checksum, and sub-directory
    l = os.listdir(pkgs_path)
    if len(l) <= 2:
        # We have no packages at all, get them all at once
        get_all(version, pkgs_path)
    print(f'Packages are present in {pkgs_path}')

    # FIXME I don't have name and version here. Instead of doing all this
    # upfront, I could code it on-demand: in sections 5 and 6, when a package
    # is needed, do this work for that package.

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    print("""This module is not meant to run directly.""")
    pkgs_path = os.path.join(common.lfs_data, 'pkgs')
    get_non_std_subdirs(pkgs_path)
