# explore.py - collect placeholders from all the snippets 

import os
import re
import sys
from lxml import etree, html

from common import get_sect_id, get_html_root
import common

#-------------------------------------------------------------------------------
# find_snippet_params - return the replaceable parameters
#-------------------------------------------------------------------------------

def find_snippet_params(nd, marked=False):
    params = []
    for k in nd:
        if k.tag == 'kbd':
            params.extend(find_snippet_params(k))
        elif k.tag == 'em':
            mark_it = False
            if 'class' in k.attrib:
                kl = k.attrib['class']
                if kl == 'replaceable':
                    # Next <code> sub-element has the text to be replaced
                    mark_it = True
            params.extend(find_snippet_params(k, mark_it))
        elif k.tag == 'code':
            if k.text and marked:
                params.append(k.text)
            params.extend(find_snippet_params(k))
        else:
            print(f'find_snippet_params: unhandled element with tag <{k.tag}>')

    return params

#-------------------------------------------------------------------------------
# Parsing functions
#-------------------------------------------------------------------------------

def parse_section(nd):
    # Title has package name and version
    title = ''
    a = nd.find('.//div/div/div/h2/a')
    if a is None or a.tail is None:
        return

    # Parse the section title
    title = a.tail.strip()
    title = re.sub('\s+', ' ', title)

    # Get section's params
    s = ''
    s_params = ''
    for i, pre in enumerate(nd.findall('.//pre')):
        params = find_snippet_params(pre)
        if len(params) > 0:
            q_params = [f"'{p}'" for p in params]
            s_params += f"        ({i}, [{', '.join(q_params)}]),\n"
    if len(s_params) > 0:
        s += f"    '{get_sect_id(title)}': [\n"
        s += s_params
        s += '    ],\n'
    return s

def parse_all_chapters(root):
    s = ''
    for chap_div in root.findall('.//div[@class="chapter"]'):
        # <div class="chapter" lang="en" xml:lang="en">
        for div in chap_div.findall('.//div'):
            kl = ''
            if 'class' in div.attrib:
                kl = div.attrib['class']
                if kl in ['sect1', 'wrap']:
                    s += parse_section(div)
    return s

#-------------------------------------------------------------------------------
# generate_mapping - suggest contents for configuration data
#-------------------------------------------------------------------------------
   
def generate_mapping(root, version):
    s = ''
    s += f"""# Generated from LFS book version {version}.

# If you add entries to 'directives', either 'add' or 'replace', that contain
# placeholders, then you must also add them here for replacement to occur.

param_mapping = {{
    # section, snippet, args
"""
    s += parse_all_chapters(root)
    s += '}\n'

    filepath = os.path.join(common.lfs_data, "param_mapping.py")
    with open(filepath, 'w') as f:
        f.write(s)

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    # Check cmd line args
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <version>')
        exit(-1)

    # Version of the LFS book to be used
    version = sys.argv[1]

    # Get the LFS book to use as an HTML tree, and parse it
    root = get_html_root(version)
    generate_mapping(root, version)
