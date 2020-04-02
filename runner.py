#!/usr/bin/python
# runner.py - front-end for the various modules

import sys
import requests

from repo import Repo
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
if len(sys.argv) != 3:
    print(f'usage: {sys.argv[0]} <dirpath> <repo_id>')
    exit(-1)
dirpath = sys.argv[1]
repo_id = sys.argv[2]

# Parse the repo file for repo_id
repos = Repo.from_dir(dirpath)
x = [r for r in repos if r.repo_id == repo_id]
if len(x) == 0:
    print(f'Repository "{repo_id}" not found.')
    exit(-1)
r = x[0]

# Get the repo's metadata
md = r.get_repomd()

# Create a .csv file
filename = f'{repo_id}_repomd.txt'
print(f'Writing out .csv file to "{filename}"')
md.to_csv(filename)

# Get the repo's actual primary data set, i.e. the package list
md.get_pkg_lists(r.root_url)

# url = url.replace('repodata/repomd.xml', filename)
# print(f'Retrieving primary: "{url}"')
# response = requests.get(url)

# filename = f'{repo_id}_primary.xml'
# with open(filename, 'w') as f:
#     f.write(response.text)
