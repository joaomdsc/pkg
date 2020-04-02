# book.py - python representation of the LFS book

# import os
import json
import datetime
from datetime import datetime
from dateutil.parser import parse
from importlib import import_module

from common import file_header, file_footer, set_tmp_path
import common
from pkg import Pkg
from snippet import Snippet
from section import Section
from config import variables

#-------------------------------------------------------------------------------
# KJson: specialize the JSON encoders/decoders
#-------------------------------------------------------------------------------

# encode: from python object to JSON: json.dump
# decode: from JSON to python object: json.load

# JSON serializes a number of basic objects, array, dict's, and combinations
# thereof, but it won't serialize objects that contain other python objects.
# So the more complex python objects require specialized JSON encoders and
# decoders.

class LfsJsonEncoder(json.JSONEncoder):
    """Return a json-encodable representation of  objects.

    This is an new object, built entirely out of dictionaries and lists
    of elementary types. Usage: json.dumps(obj, cls=LfsJsonEncoder). The
    'dumps' function will call this 'default' method, which in turn
    calls an appropriate 'to_json_encodable' function.
"""
    def default(self, obj):
        if (
                # Administration service
                isinstance(obj, LFSBook) or
                isinstance(obj, Snippet) or
                isinstance(obj, Section) or
                isinstance(obj, Pkg)
            ):
            return obj.to_json_encodable()
        elif isinstance(obj, datetime.date):
            return str(obj)
        else:
            print(f'obj={obj}, type(obj)={type(obj)}')
            return super(LfsJsonEncoder, self).default(self, obj)

#-------------------------------------------------------------------------------
# LFSBook - a set of packages and build instructions
#-------------------------------------------------------------------------------

class LFSBook():
    # __init__ needs all possible parameters because of from_json_decoded
    def __init__(self, lfs_data, version, pub_date, pkgs=None, patches=None,
                 sections=None, script_args=None, subdir_names=None):
        self.lfs_data = lfs_data
        self.version = version
        self.pub_date = pub_date
        self.code_stack = []

        self.pkgs = []
        if pkgs is not None:
            self.pkgs = pkgs
            
        self.patches = []
        if patches is not None:
            self.patches = patches
        
        self.sections = []
        if sections is not None:
            self.sections = sections
        
        self.script_args = None

        self.subdir_names = {}
        if subdir_names is not None:
            self.subdir_names = subdir_names

        # Directives and parameter mappings are specific to each version of the
        # book, they are defined in modules named adjust_{version}.py (with
        # dots '.' in the version replaced by underscores '_' to avoid
        # conflicts with python's import mechanism), as they are used to adjust
        # the behaviour described in the book.

        # Install directives and param_mapping in this book instance.
        adj = import_module(f"adjust_{self.version.replace('.', '_')}")
        self.directives = adj.directives
        self.param_mapping = adj.param_mapping

    def apply_mapping(self):
        """Copy param mappings while replacing placeholders with actual values
        """
        self.param_maps = {}
        for k, v in self.param_mapping.items():
            self.param_maps[k] = [
                (snip_id, [variables[y] if y in variables else y
                               for y in values]) for snip_id, values in v
            ]
        
    #---------------------------------------------------------------------------
    # JSON encode/decode
    #---------------------------------------------------------------------------
   
    def to_json_encodable(self):
        """Create a json-encodable object representing this object."""
        # print('LFSBook: to_json_encodable')
        d = {}
        for k, v in self.__dict__.items():
            if not (v is None or v == '' or v == [] or v == {}):
                d[k] = v

        # Json-encode the python objects inside collections, and add them if
        # they're not empty.
        if self.pkgs:
            d['pkgs'] = [x.to_json_encodable() for x in self.pkgs]
        if self.patches:
            d['patches'] = [x.to_json_encodable() for x in self.patches]
        if self.sections:
            d['sections'] = [x.to_json_encodable() for x in self.sections]

        return d

    @classmethod
    def from_json_decoded(cls, obj):
        """Return an LFSBook object from a json-decoded object."""
        d = {}
        # We iterate on the members actually present, ignoring absent ones.
        for k, v in obj.items():
            if k == 'pub_date':
                d[k] = parse(v).date()
            d[k] = v

        # Properties with non-json-serializable values
        if 'pkgs' in obj:
            d['pkgs'] = [Pkg.from_json_decoded(x) for x in obj['pkgs']]
        if 'patches' in obj:
            d['patches'] = [Pkg.from_json_decoded(x) for x in obj['patches']]
        if 'sections' in obj:
            d['sections'] = [Section.from_json_decoded(x) for x in obj['sections']]
            
        return cls(**d)

    def __str__(self):
        return f'LFS {self.version} ({self.pub_date})'

    def cumulate_sbus(self):
        running_total = 0
        for sect in self.sections:
            running_total = sect.cumulate_sbus(running_total)
        self.target_sbu = running_total
        
    def get_kernel_version(self):
        for p in self.pkgs:
            if p.name == 'Linux':
                return p.version

    def set_archive_filenames(self):
        """Determine each section's archive filename."""
        for sect in self.sections:
            if sect.with_pkg:
                sect.set_archive_filename(self)

    def gen_code(self):
        """Generate bash shell scripts to build and configure LFS

        Iterate in parallel over self.sections and 'directives' (the
        latter holds a subset of the sections). If a section is not
        present in 'directives', just generate its code, otherwise the
        special processing indicated by the directives should be
        applied.
        """
        # Set the value of common.tmp_path        
        set_tmp_path(self.version)
        
        # The first file to run is the one written last
        code = ''

        for sect in self.sections:
            # Snippet directives
            snip_dirs = []
            if sect.id in self.directives:
                d = self.directives[sect.id]
                if d == 'ignore':
                    # Ignore the entire section
                    continue
                snip_dirs = d
            # d is an array of tuples, each one is a snippet directive
            code = sect.gen_code(self, snip_dirs, code)

        # The first file to run is the one written last
        filepath = f'{common.tmp_path}/script_00.sh'
        print(f'gen_code: writing "{filepath}"')

        # File header (specific to the first script)
        hdr = ''
        hdr += """
# Checking effective user, must be root to build LFS
if [ $EUID -ne 0 ]; then
    echo "This script requires root privileges"
    exit
fi
"""
        # The file_header() function tests for the existence of sbu_total.txt,
        # to clear a previous run I need to remove the file before calling it.
        hdr += f"""
# Clearing SBU values from previous runs
rm -f {common.tmp_path}/sbu_in_secs.txt
rm -f {common.tmp_path}/sbu_total.txt
"""
        hdr += file_header(filepath, self)
        # Write out to file
        with open(filepath, 'w') as f:
            f.write(hdr + code + file_footer(filepath))

    #---------------------------------------------------------------------------
    # Persistency
    #---------------------------------------------------------------------------

    def save(self, filepath):
        s = json.dumps(self, cls=LfsJsonEncoder)
        with open(filepath, 'w') as f:
            f.write(s)

    @classmethod
    def restore(cls, filepath):
        with open(filepath, 'r') as f:
            obj = json.load(f)
        return LFSBook.from_json_decoded(obj)

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    print("""This module is not meant to run directly.""")
    
