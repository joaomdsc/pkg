# parser.py - parse the Linux From Scratch book

import os
import re
import sys
import json
import datetime
from dateutil.parser import parse
from lxml import etree, html

from common import get_html_root
import common
from book import LFSBook, variables
from snippet import Snippet
from section import Section
from pkg import Pkg, wget_files, get_non_std_subdirs

from checksum import Checksum

#-------------------------------------------------------------------------------
# Title - version and date
#-------------------------------------------------------------------------------

def get_version(root):
    nd = root.find(f'.//div[@class="book"]/div[@class="titlepage"]/div')
    subs = nd.findall(f'.//div/h2[@class="subtitle"]')
    ver = dt = None
    for sub in subs:
        s = sub.text.strip()
        m = re.match('Version (.*)$', s)
        if m:
            ver = m.group(1)
        else:
            m = re.match('Published (.*)$', s)
            if m:
                dt = parse(m.group(1)).date()
    return ver, dt

#-------------------------------------------------------------------------------
# Chapter 3 - packages and patches
#-------------------------------------------------------------------------------
    
def parse_pkg(dt, dd, has_ver=True):
    # Term: element <span class="term">
    k = dt[0]
    s = k.text.replace('\n', '')
    # packages have a version number, patches do not
    pat = r'([^(]+)\(([^)]+)\)' if has_ver else r'(.*) -'
    m = re.match(pat, s)
    if m:
        name = m.group(1).strip()
        version = None
        if has_ver:
            version = m.group(2)
    else:
        print(f'Term: unable to parse "{s}"')

    # Element <span class="token">
    k = k[0]
    s = k.text
    m = re.match(r'([0-9,]+)', s)
    if m:
        size = int(m.group(1).replace(',', ''))
    else:
        print(f'Token: unable to parse "{s}"')

    # Definition
    for k in dd:
        if k.tag == 'p':
            s = k.text.strip()
            if s.startswith('Download:'):
                kk = k[0]
                url = kk.attrib['href']
            if s.startswith('MD5 sum:'):
                kk = k[0]
                md5 = Checksum('md5', kk.text)

    return Pkg(name, size, url, md5, version)

def parse_pkg_list(root, id, has_ver=True):
    nd = root.find(f'.//a[@id="{id}"]')
    if nd is None:
        # As of version 9.1
        nd = root.find(f'.//a[@id="ch-{id}"]')
    for i in range(5):
        nd = nd.getparent()

    # <div class="sect1" lang="en" xml:lang="en">
    pkgs = []
    for dt, dd in zip(nd.findall('.//div/div/dl/dt'),
                      nd.findall('.//div/div/dl/dd')):
        p = parse_pkg(dt, dd, has_ver=has_ver)
        pkgs.append(p)
    return pkgs

#-------------------------------------------------------------------------------
# sect1 - run commands
#-------------------------------------------------------------------------------

def get_em_code(nd, request_mark=False):
    s = ''
    for k in nd:
        if k.tag == 'em':
            mark_it = False
            if 'class' in k.attrib:
                kl = k.attrib['class']
                if kl == 'replaceable':
                    # Next sub-element of type <code> must mark the code to be
                    # replaced
                    mark_it = True
            if k.text:
                s += k.text
            s += get_em_code(k, mark_it)
            if k.tail:
                s += k.tail
        elif k.tag == 'code':
            if k.text:
                if request_mark:
                    s += f'<code>{k.text}</code>'
                else:
                    s += k.text
            s += get_em_code(k)
            if k.tail:
                s += k.tail
        else:
            print(f'get_em_code: unhandled element with tag <{k.tag}>')

    return s
                
def get_kbds_script(kbds):
    s = ''
    for kbd in kbds:
        # One or more <code>, or <em><code>
        if kbd.text:
            s += kbd.text
        s += get_em_code(kbd)

    return s

# HTML elements with class "sect1" rather than "wrap" correspond to series of
# instructions to be executed, that do not build a software package.
    
def parse_sect1(nd):
    # Title has package name and version
    title = ''
    a = nd.find('.//div/div/div/h2/a')
    if a is None or a.tail is None:
        return

    # Parse the section title
    title = a.tail.strip()
    title = re.sub('\s+', ' ', title)

    # Extract build instructions
    snippets = []
    for pre in nd.findall('.//pre'):
        s = ''
        if pre.text:
            t = pre.text.strip()
            s += t
        if 'class' in pre.attrib:
            kl = pre.attrib['class']
            # Note: <pre class="root" has only been found in sect1 sections
            if kl in ['userinput', 'root']:
                # This is a code snippet
                kbds = pre.findall('.//kbd[@class="command"]')
                s += get_kbds_script(kbds)
                if len(s) > 0:
                    snippets.append(Snippet('userinput', s))
            elif kl == 'screen':
                # This is some program output
                s += get_em_code(pre)
                if len(s) > 0:
                    snippets.append(Snippet('screen', s))

    # Only create section object if there are instructions
    if len(snippets) > 0:
        return Section(title, snippets, with_pkg=False)

#-------------------------------------------------------------------------------
# Chapters 5 and 6 - building system software
#-------------------------------------------------------------------------------

# This parses the paragraph following the section title which gives the
# estimated build time in SBUs and the approximate disk size.

def parse_package(nd):
    x = nd.find('.//div[@class="segmentedlist"]/div[@class="seglistitem"]')
    segs = x.findall('.//div[@class="seg"]')
    # print(f'Found {len(segs)} segs')
    sbu = 0.0
    sz = 0.0
    for k in segs:
        # One seg for build time, another one for disk size
        build_time = False
        for kk in k:
            if kk.tag == 'strong':
                if kk.text == 'Approximate build time:':
                    build_time = True
            elif kk.tag == 'span':
                if build_time:
                    if kk.text == 'less than 0.1 SBU':
                        kk.text = '0.1 SBU'
                    m = re.match(r'(\d+(\.\d+)?) SBU', kk.text)
                    if m:
                        sbu = float(m.group(1))
                    # else:
                    #     print(f'Can\'t parse "{kk.text}" as build time')
                else:
                    # Disk space
                    m = re.match(r'(\d+(\.\d+)?) (G|M)B', kk.text)
                    if m:
                        sz = float(m.group(1))
                    # else:
                    #     print(f'Can\'t parse "{kk.text}" as disk size')
    return sbu, sz

def parse_wrap(nd):
    """This parses one section with class="wrap" (it builds a package) """
    # Title has package name and version
    title = ''
    a = nd.find('.//div/div/div/h2/a')
    if a is None or a.tail is None:
        return

    # Parse the section title
    title = a.tail.strip()
    title = re.sub('\s+', ' ', title)

    # Patch
    title = title.replace('xml::parser', 'xml-parser')
    
    # Extract build instructions
    snippets = []
    divs = nd.findall('./div')
    with_pkg = False
    sbu = sz = None
    for div in divs:
        # A section may have different (sub-)classes 
        if 'class' in div.attrib:
            kl = div.attrib['class']
            if kl == 'package':
                sbu, sz = parse_package(div)
                # print(f'{title}, {sbu} SBU, {sz} GB')
                with_pkg = True
                continue
            # sect2 is used for the 8.4 grub section
            if kl not in ['installation', 'configuration', 'sect2']:
                continue
            for pre in div.findall('.//pre'):
                s = ''
                if pre.text:
                    t = pre.text.strip()
                    s += t
                if 'class' in pre.attrib:
                    kl = pre.attrib['class']
                    # Note: <pre class="root" has only been found in sect1 sections
                    if kl in ['userinput', 'root']:
                        # This is a code snippet
                        kbds = pre.findall('.//kbd[@class="command"]')
                        s += get_kbds_script(kbds)
                        if len(s) > 0:
                            snippets.append(Snippet('userinput', s))
                    elif kl == 'screen':
                        # This is some program output
                        s += get_em_code(pre)
                        if len(s) > 0:
                            snippets.append(Snippet('screen', s))

    # Only create section object if there are instructions
    if len(snippets) > 0:
        return Section(title, snippets, with_pkg=with_pkg, sbu=sbu, sz=sz)

def parse_all_chapters(root):
    sections = []
    for chap_div in root.findall('.//div[@class="chapter"]'):
        a = chap_div.find(f'.//a')
        id = a.attrib['id']

        # Chapter title
        title = ''
        if a.tail:
            title = a.tail.strip()
            title = re.sub('\s+', ' ', title)

        # <div class="chapter" lang="en" xml:lang="en">
        for div in chap_div.findall('.//div'):
            kl = ''
            if 'class' in div.attrib:
                kl = div.attrib['class']
                sect = None
                if kl == 'wrap':
                    sect = parse_wrap(div)
                if kl == 'sect1':
                    sect = parse_sect1(div)
                if sect is not None:
                    sections.append(sect)
    return sections

#-------------------------------------------------------------------------------
# parse_book - 
#-------------------------------------------------------------------------------

def parse_book(root):
    """Return an LFSBook instance from an LFS book HTML tree."""
    version, pub_date = get_version(root)

    # Get packages, checksums, subdir names, ...
    pkgs_path = os.path.join(common.lfs_data, 'pkgs')
    if not os.path.isdir(pkgs_path):
        os.mkdir(pkgs_path)
    wget_files(version, pkgs_path)

    # Initialize book object
    bk = LFSBook(common.lfs_data, version, pub_date)

    # Get the packages data, including name, version and archive filename. In
    # particular, this is where we find the linux kernel version.
    bk.pkgs = parse_pkg_list(root, 'materials-packages')

    # Set the values of dynamic variables
    variables.update(dict(
        pkg_repository=pkgs_path,
        lfs_version=version,
        kernel_version=bk.get_kernel_version(),
    ))
    bk.apply_mapping()

    # FIXME parsing functions should be in LFSBook 
    bk.sections = parse_all_chapters(root)

    # Calculate expected number of SBUs
    bk.cumulate_sbus()

    # Used by set_archive_filenames
    filepath = os.path.join(pkgs_path, 'subdir_names')
    if not os.path.isfile(filepath):
        get_non_std_subdirs(pkgs_path)
    with open(filepath, 'r') as f:
        bk.subdir_names = json.load(f)

    # Determine each section's archive filename and set it here. This is needed
    # because the package names in chapter 3, the archive filenames in chapter
    # 3, and the package (section) names in chapter 5 don't always match.
    bk.set_archive_filenames()

    return bk

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
    bk = parse_book(get_html_root(version))
    print(f'Found {len(bk.pkgs)} pkgs, {len(bk.sections)} sections')

    bk.gen_code()
