# common.py - 

import os
import re
import tarfile
import requests
from datetime import datetime
from lxml import html

#-------------------------------------------------------------------------------
# Globals
#-------------------------------------------------------------------------------

# Under lfs_data there will be a pkgs directory. Set by parse.py.
lfs_data = None

# Files persistend in between runs. Set by set_tmp_path(), called by book.py.
tmp_path = None

sec_pat = r'(([0-9])\.([0-9]{1,2})\.?)'
pkg_pat = '(([$a-zA-Z0-9:_]+)(-[$a-zA-Z0-9:_]+)?)'
ver_pat = '([a-z0-9.]+)'

#-------------------------------------------------------------------------------
# get_sect_id - 
#-------------------------------------------------------------------------------

def get_sect_id(s):
    m = re.match(f'{sec_pat}', s)
    if m:
        # Normalize before returning 
        return f'{m.group(2)}.{m.group(3):>02}'

#-------------------------------------------------------------------------------
# normalize_sect_id - 
#-------------------------------------------------------------------------------

def normalize_sect_id(s):
    m = re.match(f'{sec_pat}', s)
    if m:
        return f'{m.group(2)}.{m.group(3):>02}'

#-------------------------------------------------------------------------------
# parse_preps - preparation titles in ch.5 and 6
#-------------------------------------------------------------------------------

def parse_preps(s):
    # Section here is not normalized
    section = name = None
    m = re.match(f'{sec_pat} (.*)$', s)
    if m:
        section = f'{m.group(2)}.{m.group(3):>02}'
        name = m.group(4)

    return section, name

#-------------------------------------------------------------------------------
# parse_title - extract information from LFS book section titles in ch.5 and 6
#-------------------------------------------------------------------------------

# Could make the version optional, and remove parse_preps
def parse_title(s):
    sect_id = name = version = None
    m = re.match(f'{sec_pat} {pkg_pat}-{ver_pat}', s)
    if m:
        sect_id = f'{m.group(2)}.{m.group(3):>02}'
        name = m.group(4)
        version = m.group(7)
    else:
        # Special case of libstdc+ and elflibs
        m = re.match(f'{sec_pat} [a-zA-Z+]+ from {pkg_pat}-{ver_pat}$', s)
        if m:
            sect_id = f'{m.group(2)}.{m.group(3):>02}'
            name = m.group(4)
            version = m.group(7)

    return sect_id, name, version

#-------------------------------------------------------------------------------
# parse_filename - extract information from the shell script filenames
#-------------------------------------------------------------------------------

def parse_filename(s):
    sect_id = sec_type = name = version = None
    pat = f'{sec_pat}_[0-9]{2}_(build|run|run_chk|check)_{pkg_pat}(-({ver_pat}))?.sh$'
    m = re.match(pat, s)
    if m:
        sect_id = m.group(1)
        sec_type = m.group(4)
        name = m.group(5)
        version = m.group(8)
    else:
        print(f'parse_filename: couldn\'t parse "{s}"')

    return sect_id, sec_type, name, version

#-------------------------------------------------------------------------------
# commentify - turn a multi-line string into a multi-line bash comment
#-------------------------------------------------------------------------------

def commentify(t):
    """Turn a multi-line string into a multi-line bash comment

    This actually turns some text into a bash script echoing the same
    text as a bash comment.

    The argument to echo will be in between single quotes, because the
    text may reference shell variables and we don't want to expand them
    here, so any single quotes in the text need to be escaped first.
    However, the bash manual clearly states that "a single quote may not
    occur between single quotes, even when preceded by a backslash".

    https://stackoverflow.com/questions/1250079 has a nice (if somewhat
    unreadable) trick for this: write the single quote in between double
    quotes (for bash), and add an outer layer of single quotes so that
    bash actually concatenates 3 strings (in single quotes, double
    quotes, and single quotes again), using the outermost single quotes
    from your echo command.
"""
    z = ''
    for s in t.splitlines():
        s = s.replace("'", "'\"'\"'")
        z += f"echo '# {s}'\n"
    return z

#-------------------------------------------------------------------------------
# replace_values - 
#-------------------------------------------------------------------------------

def replace_values(text, values):
    """Replace placeholders with actual values in the text.

    Placeholders are of the formm <code>xxx</code>. They are replaced
    with actual values from the 'values' argument, which is an array of
    strings.
"""
    s = text
    vals = iter(values)
    t = ''
    while True:
        # Note the non-greedy * operator, this is requird so we can
        # match something like <code>xxx</code><code>yyy</code>
        m = re.search('<code>.*?</code>', s, re.MULTILINE)
        if not m:
            t += s
            return t
        try:
            t += s[:m.start()] + next(vals)
        except StopIteration:
            raise RuntimeError(f'Not enough values to match text "{text}"')
        s = s[m.end():]

#-------------------------------------------------------------------------------
# tar_extract - un-tar a package file
#-------------------------------------------------------------------------------

def tar_extract(name, version):
    """Un-tar the given file in the current directory."""
    filename = get_pkg_filename(name, version)
    # print(f'Opening tarfile {filename}')
    with tarfile.open(filename) as t:
        m = t.getmembers()[0]
        t.extractall()

    # Confirm directory creation with the expected name
    pkg_dir = m.name.split('/', maxsplit=1)[0]
    if not os.path.isdir(pkg_dir):
        print(f'Expected directory {pkg_dir} not found')
        return
    return pkg_dir

#-------------------------------------------------------------------------------
# file_header - 
#-------------------------------------------------------------------------------

def file_header(filepath, book, chrooted=False):
    x = filepath.split('/', maxsplit=1)
    filename = x[1] if len(x) == 2 else x[0]
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    s = ''
    # Generate file header comments
    s += f"""
# {filepath} generated on {dt}
# from {book}
echo "#{'='*79}"
echo "# $0 user \\"$USER\\" pid $$"
echo "#{'='*79}"
date
"""
    # Path depends on whether the environment is chroot'ed or not when this
    # script gets run
    path = '/pkg_lfs' if chrooted else f'{tmp_path}'
    
    # Support for running SBU calculations
    s += f"""
# If SBU values have been calculated, get them
if [ -f {path}/sbu_in_secs.txt ]; then
    sbu_in_secs=$(cat {path}/sbu_in_secs.txt)
fi
if [ -f {path}/sbu_total.txt ]; then
    sbu_total=$(cat {path}/sbu_total.txt)
fi

# Bash function to display elapsed time as hh mm ss
function elapsed {{
    local duration=$1
    local minutes=$(( $duration/60))
    local secs=$(( $duration%60))
    printf "%02d:%02d:%02d" $(( minutes/60)) $(( minutes%60)) ${{secs}}
}}

"""
    return s
 
#-------------------------------------------------------------------------------
# file_footer - 
#-------------------------------------------------------------------------------

def file_footer(filepath):
    s = ''
    s += f"""
echo "#{'='*79}"
echo "# End of {filepath}"
echo "#{'='*79}"
"""
    return s
      
#-------------------------------------------------------------------------------
# set_tmp_path - 
#-------------------------------------------------------------------------------

def set_tmp_path(version):
    """Set the path for files persisted in between runs.

    Script files generated by parse.py are stored in this directory, so
    they can be reused, for example, if the build run is interrupted by
    a reboot.
    """
    global tmp_path
    tmp_path = os.path.join('/var/tmp/lfs', version)
    if not os.path.isdir(tmp_path):
        oldmask = os.umask(000)
        os.makedirs(tmp_path, mode=0o777, exist_ok=True)
        os.umask(oldmask)
        
#-------------------------------------------------------------------------------
# get_html_root - 
#-------------------------------------------------------------------------------

def get_html_root(version):
    """Return the path of the LFS book to be used.

    We use the single-page HTML version of the book. We search for it
    locally, and if we don't have it, then we download it from the LFS
    website.
"""    
    # Directory for LFS data such as pkgs and the book itself
    global lfs_data
    if 'LFS_DATA' in os.environ:
        lfs_data = os.environ['LFS_DATA']
        lfs_data = os.path.join(lfs_data, version)
        print(f'LFS_DATA: using {lfs_data}')
    else:
        lfs_data = os.path.join(os.environ['HOME'], 'lfs')
        lfs_data = os.path.join(lfs_data, version)
        print(f'LFS_DATA: defaulting to {lfs_data}')
    if not os.path.isdir(lfs_data):
        oldmask = os.umask(000)
        os.makedirs(lfs_data, mode=0o777, exist_ok=True)
        os.umask(oldmask)

    # Do we have the file already?
    for f in os.listdir(lfs_data):
        pat = f'LFS-BOOK-{version}-NOCHUNKS-(.*).html'
        m = re.match(pat, f)
        if m:
            # We have the file, return the root of the HTML tree
            filepath = os.path.join(lfs_data, f)
            print(f'Using local file "{filepath}"')
            with open(filepath, 'r', encoding=m.group(1)) as f:
                content = f.read()
            root = html.fromstring(content)
            return root
        
    # We couldn't find the file
    filename = f'LFS-BOOK-{version}-NOCHUNKS.html'
    print(f'No LFS book found, downloading "{filename}" from the web.')
    url = f'http://www.linuxfromscratch.org/lfs/downloads/{version}/{filename}'
    r = requests.get(url)
    if r.status_code >= 400:
        raise RuntimeError(f'[{r.status_code}] {r.text}')

    # Store the encoding from the HTTP headers in the filename
    filename = f'LFS-BOOK-{version}-NOCHUNKS-{r.encoding}.html'
    filepath = os.path.join(lfs_data, filename)
    with open(filepath, 'w', encoding=r.encoding) as f:
        f.write(r.text)

    return html.fromstring(r.text)
 
#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    print("""This module is not meant to run directly.""")
