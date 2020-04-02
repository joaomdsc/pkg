# snippet.py - Linux From Scratch building instructions

import os
import re
import sys
import shutil
from datetime import datetime
from subprocess import run, PIPE, STDOUT

from common import parse_title, parse_preps, commentify, tar_extract
from common import replace_values
import common

#-------------------------------------------------------------------------------
# write_to_file - 
#-------------------------------------------------------------------------------

def write_to_file(dir, filename, s):
    with open(os.path.join(dir, filename), 'w') as f:
        f.write(s)
    
#-------------------------------------------------------------------------------
# Snippet - a small piece of code or program output
#-------------------------------------------------------------------------------

class Snippet():
    """A Snippet is a multiline piece of text, either code or program output.

    Snippets appear in the LFS book with special formatting, inside a
    box with some background color, with a particular font, etc. In the
    HTML file, these elements have a 'class' attribute, with the value
    'userinput' denoting shell script code (commands to be input), and
    the value 'screen' denoting program output produced by the
    commands.

    As of LFS 9.0, there's another value 'root' in section 7.9, but as
    far as I can tell it's identical to 'userinput'.
"""
    def __init__(self, stype, text):
        """stype is 'userinput' or 'screen'."""
        self.stype = stype
        self.text = text
        self.replace = None

    #---------------------------------------------------------------------------
    # JSON encode/decode
    #---------------------------------------------------------------------------
   
    def to_json_encodable(self):
        """Create a json-encodable object representing this object."""
        # print('  Snippet: to_json_encodable')
        d = {}
        for k, v in self.__dict__.items():
            if not (v is None or v == '' or v == [] or v == {}):
                d[k] = v
        return d

    @classmethod
    def from_json_decoded(cls, obj):
        """Return a Snippet instance from a json-decoded object."""
        d = {}
        # We iterate on the members actually present, ignoring absent ones.
        for k, v in obj.items():
            d[k] = v            
        return cls(**d)

    #---------------------------------------------------------------------------
    # Replace placeholders with actual values
    #---------------------------------------------------------------------------

    def replace_values(self, values):
        """Replace values in the snippet text.

        Placeholders in the text are replaced with actual values, and
        the result is returned.
"""
        return replace_values(self.text, values)

    #---------------------------------------------------------------------------
    # Code generation
    #---------------------------------------------------------------------------

    def gen_header(self, prefix):
        """Generate the snippet header to document the snippet's code.

        Each script starts by echoing the commands that it will execute,
        *before* actually runnning them. This makes it easier to read
        the log files, because it shows you the code that produced the
        output you're looking at.
        """
        t = self.text
        s = ''
        s += f"echo '#{'-'*79}'\n"
        s += f"echo '# Snippet {prefix}'\n"
        s += f"echo '#{'-'*79}'\n"
        s += commentify(t)
        s += f"echo '#{'-'*79}'\n"
        return s

    def run_header(self, prefix):
        """Run the snippet header.

        The snippet header echoes the commands that will be executed,
        for documentation purposes.
        """
        s = self.gen_header(prefix)
        r = run(['/bin/bash', '-c', s], stdout=PIPE, stderr=STDOUT)
        return r.stdout.decode()

    def generate(self, prefix, check=False):
        """Generate the script code that will be written to file."""
        t = self.text
        s = self.gen_header(prefix)
        s += f'{t}\n'

        # When checking, we must preserve the command's output, not pollute it
        # with this extra code
        if not check:
            s += f"""err=$?
if [ $err -ne 0 ]; then
    echo Error: {prefix} returned exit code $err
fi
echo

"""
        return s

    def gen_check(self, prefix, expected, chrooted):
        """Generate shell script code to verify the output of a snippet.

        When the book has indicated the expected output of a script
        snippet, we generate code to perform the comparison and warn us
        when the actual output is not what was expected.
        """
        # Write to file because we're going to generate a 'diff' command
        script_filename = f'{prefix}_script.sh'
        expected_filename = f'{prefix}_expected.txt'

        # In chapter 5 we can find the files in /var/tmp/lfs, but in chapter 6
        # we are chroot'ed, the path needs to be local. But when generating
        # this code, the filesystem is not mounted on $LFS yet, so we do the
        # same thing we do for scripts : write to /var/tmp/lfs at generation
        # time, then copy into $LFS after the mount is done (see directives.py)
        write_to_file(common.tmp_path, script_filename,
                      self.generate(prefix, check=True))
        write_to_file(common.tmp_path, expected_filename, expected)

        # Path depends on whether the environment is chroot'ed or not when this
        # script gets run
        path = '/pkg_lfs' if chrooted else f'{common.tmp_path}'
        
        s = self.gen_header(prefix)

        # NOte that when we run the script, we strip leading and trailing
        # whitespace from the output lines. This is because sometimes the
        # expected result in the book (in a 'screen'-type snippet) does not
        # include the same whitespace. This means whitespace now needs to be
        # trimmed from *every* expected text.
        s += rf"""output_filename=$(mktemp {prefix}_output.XXXXXX)
bash {path}/{script_filename} | sed -e "s/^\s\+\|\s\+$//g" > {path}/$output_filename
diff {path}/$output_filename {path}/{expected_filename}
err=$?
if [ $err -eq 1 ]; then
    echo Check: {prefix}: unexpected output
else
    echo Check: {prefix}: output is as expected.
fi

"""
        return s

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    print("""This module is not meant to run directly.""")
