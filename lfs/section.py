# section.py - Linux From Scratch building instructions

import os
import re

from common import parse_title, parse_preps, file_header, file_footer
from common import replace_values
import common
from snippet import Snippet

#-------------------------------------------------------------------------------
# Section - build or configure instructions for a section of the LFS book
#-------------------------------------------------------------------------------

class Section():
    def __init__(self, title, snippets, with_pkg=True, sbu=None, sz=None,
                 id=None, name=None, version=None, pkg_filename=None,
                     pkg_dir=None,pkg=None):
        self.title = title
        self.snippets = snippets
        self.with_pkg = with_pkg
        self.sbu = sbu
        self.sz = sz
        self.pkg_filename = None
        self.pkg_dir = None
        self.pkg = None

        if self.with_pkg:
            # Extract section number, package name and version
            self.id, self.name, self.version = parse_title(self.title)
        else:
            self.id, self.name = parse_preps(self.title)

        # s = f'Parsed {self.id} {self.name}'
        # if self.with_pkg:
        #     s += f'-{self.version}'
        # print(s)

    def cumulate_sbus(self, running_total):
        """Return the total number of SBUs expected after building this section"""
        if not self.with_pkg:
            return running_total
        self.sbu_total = running_total + self.sbu
        return self.sbu_total

    def set_archive_subdir(self, bk):
        # Non-standard package directories have been identified previously
        # and stored in 'subdir_names'
        if self.pkg_filename in bk.subdir_names:
            # Non-std case
            self.pkg_dir = bk.subdir_names[self.pkg_filename]
        else:
            # Extract the part before '.tar'
            m = re.match(r'(.*)\.tar\.(gz|xz|bz2)', self.pkg_filename)
            self.pkg_dir = m.group(1)
        
    def set_archive_filename(self, bk):
        """Determine this section's archive filename."""
        # print(f'set_archive_filenames: {self.id}')
        # Search in section 3.2 for this sections archive filename
        self.pkg_filename = None
        for p in bk.pkgs:
            # p.name comes from chapter 3, self.name from chapter 5
            if p.name == self.name and p.version == self.version:
                self.pkg_filename = p.filename
                break
        if self.pkg_filename == None:
            # Search the filesystem (Xz and Procps-ng)
            path = os.path.join(common.lfs_data, 'pkgs')
            s = f'{self.name.lower()}-{self.version}.tar.'
            for f in os.listdir(path):
                if f.startswith(s):
                    self.pkg_filename = f
                    break
        if self.pkg_filename == None:
            print(f'Section {self.id}: {self.name}-{self.version}'
                  + ": can't determine package filename.")
        else:
            self.set_archive_subdir(bk)

    #---------------------------------------------------------------------------
    # JSON encode/decode
    #---------------------------------------------------------------------------
   
    def to_json_encodable(self):
        """Create a json-encodable object representing this object."""
        # print('  Section: to_json_encodable')
        d = {}
        for k, v in self.__dict__.items():
            if not (v is None or v == '' or v == [] or v == {}):
                d[k] = v

        # Json-encode the python objects inside collections, and add them if
        # they're not empty.
        if self.snippets:
            d['snippets'] = [x.to_json_encodable() for x in self.snippets]
            
        return d

    @classmethod
    def from_json_decoded(cls, obj):
        """Return an LFSBook object from a json-decoded object."""
        d = {}
        # We iterate on the members actually present, ignoring absent ones.
        for k, v in obj.items():
            d[k] = v

        # Properties with non-json-serializable values
        if 'snippets' in obj:
            d['snippets'] = [Snippet.from_json_decoded(x) for x in obj['snippets']]
            
        return cls(**d)

    #---------------------------------------------------------------------------
    # Generate section header in the script code
    #---------------------------------------------------------------------------

    def gen_section_hdr(self, bk):
        s = ''
        s += f"""# Section header
echo "#{'='*79}"
"""
        s += f'echo "# {self.id} {self.name}'
        if self.with_pkg:
            s += f' {self.version}'
        s += f'"\n'
        s += f"""echo "#{'='*79}"
echo
"""
        return s
    
    #---------------------------------------------------------------------------
    # apply_directive
    #---------------------------------------------------------------------------

    def apply_directive(self, directive, bk, code=None, s=None, repl_records=None):
        """Apply directives.

        The value in directive[2] depends on the command:
        'replace': the argument is the string to use as a replacement
        'push': the argument is the filepath to save into
"""
        snip_id = directive[0]
        cmd = directive[1]
        
        if cmd == 'push':
            # Perform replacements on the directive argument if necessary
            arg = directive[2]
            if repl_records is not None:
                for rec in repl_records:
                    # rec[0] = snippet id, rec[1] = array of replacement values
                    if rec[0] == snip_id:
                        arg = replace_values(arg, rec[1])
                        break
            # Save the current (code, filepath) on the stack
            bk.code_stack.append((code + s, arg))
            code = s = ''

        elif cmd == 'pop':
            # Finalize code being generated
            code += s
            # Pop up one stack level and resume that level's code generation
            prev_code, filepath = bk.code_stack.pop()
            print(f'{self.id}: apply_directive: writing "{filepath}"')

            # Write out to file
            chrooted = self.id.startswith('6.') or self.id.startswith('9.')
            with open(filepath, 'w') as f:
                f.write(file_header(filepath, bk, chrooted=chrooted)
                        + code + file_footer(filepath))

            # Reset code generation for this stack level
            code = prev_code
            s = ''

        elif cmd == 'add':
            arg = directive[2]
            t = Snippet('userinput', arg)

            # Replace placeholders with actual values
            if repl_records is not None:
                for rec in repl_records:
                    # rec[0] = snippet id, rec[1] = array of replacement values
                    if rec[0] == snip_id:
                        t.text = t.replace_values(rec[1])
                        break
            s += t.generate(f'{self.id}_{snip_id} [add]')
        else:
            print(f'Sect: {self.id}, snippet directive: {snip_id}'
                  + f', unknown command "{cmd}"')

        return code, s
    
    #---------------------------------------------------------------------------
    # Generate code for this snippet
    #---------------------------------------------------------------------------
        
    def gen_snippet(self, i, t, repl_records, arr, s):
        """Generate the shell script for this snippet."""

        # Replace placeholders with actual values
        if repl_records is not None:
            for rec in repl_records:
                # rec[0] = snippet id, rec[1] = array of replacement values
                if rec[0] == i:
                    t.text = t.replace_values(rec[1])
                    break

        # Generate the snippet code
        if t.stype == 'userinput':
            arr.append((i, t))
        elif t.stype == 'screen':
            if len(arr) > 0:
                # There's (at least) one preceding 'userinput'
                # snippet stored in arr, this snippet will be used
                # to check the result.

                # First, concatenate and generate all but the last
                # snippet from 'array'
                for index, snip in arr[:len(arr)-1]:
                    s += snip.generate(f'{self.id}_{index:>02}')

                # Generate a check on the last remaining snippet in 'array'
                # ('userinput' snippet in variable snip) against the current
                # 'screen' snippet (in variable t).
                index, snip = arr[len(arr)-1]
                prefix = f'{self.id}_{index:>02}'

                # Whitespace needs to be stripped from the expected text lines,
                # because we'll be doing the same to the script output in the
                # code we generate in snippet.py:gen_code.
                s_txt = ''.join([f'{t.strip()}\n' for t in t.text.splitlines()])

                # For the outputs to match, we need to take the 'userinput's
                # header, run it in bash, and include the output in the
                # expected text.
                s += snip.gen_check(prefix, snip.run_header(prefix) + s_txt,
                                        chrooted=self.id.startswith('6.'))
                # Clear the array
                arr = []
            else:
                # This 'screen' snippet does not follow a 'userinput' one,
                # so just ignore it
                pass
        else:
            print(f'Unknown snippet type {t.stype}')

        # These two have a longer lifespan
        return arr, s
    
    #---------------------------------------------------------------------------
    # Generate code for this section
    #---------------------------------------------------------------------------

    def pkg_header(self):
        return f"""date
# Extracting from package archive
echo '# Extracting from package archive'
cd {'$LFS' if self.id.startswith('5.') else ''}/sources
tar xvf {self.pkg_filename} > /dev/null
cd {self.pkg_dir}
start=$SECONDS
"""

    def pkg_footer(self, bk):
        s = ''
        s += f"""# Finish section {self.id}
end=$SECONDS
duration=$(( end - start ))
"""
        if self.id == '5.04':
            # Binutils pass 1 defines the SBU unit
            s += f"""
# Define and persist the SBU value in seconds
sbu_in_secs=$duration
echo $sbu_in_secs > {common.tmp_path}/sbu_in_secs.txt
sbu=1.0
sbu_total=1.0
"""
        else:
            # Path depends on whether the environment is chroot'ed or not when this
            # script gets run
            path = ('/pkg_lfs' if self.id.startswith('6.')
                        or self.id.startswith('8.') else f'{common.tmp_path}')

            s += f"""
sbu=$(bc -l <<< "scale=1; $duration / $sbu_in_secs")
sbu_total=$(bc -l <<< "scale=1; $sbu_total + $sbu")
echo $sbu_total > {path}/sbu_total.txt
"""
        s += f"""
elapsed_txt=$(elapsed $duration)
printf "{self.id}: %s = %03.1f SBUs (expected %03.1f), total: %03.1f (expected %03.1f)\
, target %03.1f\n" $elapsed_txt $sbu {self.sbu:.1f} $sbu_total {self.sbu_total:.1f} {bk.target_sbu:.1f}
cd {'$LFS' if self.id.startswith('5.') else ''}/sources
rm -rf {self.pkg_dir}

"""
        return s

    def gen_code(self, bk, snip_dirs, code):
        """Generate all the shell scripts for this section.

        snip_dirs is a non-empty array of tuples of the form
        (snippet_id, command, param), ordered by snippet_id.

        code is the script code that we've accumulated so far in this
        stack level
"""
        # Value replacements for this section?
        repl_records = None
        if self.id in bk.param_maps:
            repl_records = bk.param_maps[self.id]

        # The 's' variable will hold all the code generated inside this section
        # (inside the lifespan of this gen_code() invocation).
        s = ''
        
        # Generate the section header with some context information.
        s += self.gen_section_hdr(bk)

        # If this section builds a package
        if self.with_pkg:
            s += self.pkg_header()

        # This 'arr' object accumulates across snippets; it is used for
        # generating output checks, by matching userinput to screen.
        arr = []

        # Here's the general idea: accumulate userinput scripts until a
        # (userinput, screen) pair is found. Then generate the
        # concatenation of the initial userinput scripts, followed by the
        # (userinput, screen) pair as a check. A screen snippet either
        # matches a preceding userinput, or it is ignored.

        # Iterate over all the snippets in this section, while simultaneously
        # moving along the array of snippet directives (indexed by 'j').
        j = 0
        for i, t in enumerate(self.snippets):            
            # Invariant: directives on previous snippets have already been
            # applied. Current directive's target id (d[0]) > i-1.

            # Are there any directives to be applied?
            if len(snip_dirs) > 0 and j < len(snip_dirs):
                d = snip_dirs[j]
                while d[0] < i:
                    if len(arr) > 0:
                        # Concatenate and write out all the snippets from 'array'
                        for index, snip in arr:
                            s += snip.generate(f'{self.id}_{index:>02}')
                        arr = []
                    # Apply intermediate directives between i-1 and i. These
                    # may be push, pop or add operations.
                    code, s = self.apply_directive(d, bk, code, s, repl_records)
                    j += 1
                    if j == len(snip_dirs):
                        d = None
                        break
                    d = snip_dirs[j]

            # There is a current directive and it applies to this snippet
            if j < len(snip_dirs) and d[0] == i:
                d = snip_dirs[j]
                # ignore or replace
                if d[1] == 'replace':
                    t.text = d[2]
                    t.replace = True
                if d[1] != 'ignore':
                    # After any directives have been applied, it is now time to
                    # generate this snippet's code.
                    arr, s = self.gen_snippet(i, t, repl_records, arr, s)

                # We've applied replace/ignore, increment the directive index
                j += 1

            # Either no more directives, or they are to be applied later
            else:
                arr, s = self.gen_snippet(i, t, repl_records, arr, s)

        # After the loop ends, no more snippets
        if len(arr) > 0:
            # Concatenate and write out all the snippets from 'array'
            for index, snip in arr:
                prefix = (f'{self.id}_{index:>02}'
                              + f'{" [replace]" if snip.replace else ""}')
                s += snip.generate(prefix)

        # Are there any directives left after the last snippet?
        if len(snip_dirs) > 0:
            for d in snip_dirs[j:]:
                # Push, pop or add operations.
                code, s = self.apply_directive(d, bk, code, s, repl_records)

        # If this section builds a package
        if self.with_pkg:
            s += self.pkg_footer(bk)

        # Code accumulates across sections (but it may have been reset by a
        # push or pop operation inside an apply_directive)
        return code + s

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    print("""This module is not meant to run directly.""")
