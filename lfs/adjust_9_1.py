# adjust_9.1.py - adjusting for a specific version of the book

"""Configuration data to adjust the build process for version 9.1.

This file defines two data structures:
- directives: new or modified snippets to adjust the build instructions
- param_mapping: what variables should replace the placeholders in snippets ?

The variables themselves (with the actual values you want to use) are defined
in a third structure called 'variables', in the config.py file.

Collectively, these data structures define the behaviour of the software.
Directives and param_mapping are used to adapt the build to a specific version
of the book, and variables customizes the build for a given environment.
"""

#-------------------------------------------------------------------------------
# directives
#-------------------------------------------------------------------------------

# Directives are commands to change the behaviour from that which is prescribed
# by the LFS book. This is mostly done to adapt commands that were meant for
# interactive use to the new situation where everything is being done in a
# batch script, but it can also be done simply to adapt the build process to
# your personal tastes and preferences.

# FIXME once you start testing with different versions, you see what a bad idea
# it is to organize the sections based on their id, because this can change
# from one version to another (adding just one new package changes the id of
# all the subsequent packages). 

# The 'directives' dictionary uses section ids as keys. The value associated to
# a key may be:

# - a simple string, which is a command such as 'ignore' (curr.the only one)
# - an array of tuples, each tuple describes a directive

# A directive tuple has the form
# - target id
# - command
# - argument (optional)

# The target id is either the id of a snippet to which the directive will be
# applied, or it's just a number used to ensure the correct ordering of
# directives. The tuples in a section value should always be ordered by target
# id.

# Commands may be:
# - ignore: just skip the section or snippet

# - replace: like the name says, whatever snippet (userinput or screen) was
# parsed from the book gets replaced with the snippet from this directive
# (argument). The new snippet may include <code> elements which will be
# replaced, *if* you don't forget to add them to param_mapping.

# - push: from this point on, script code being generated must be re-directed
# to a new file, named in the directive (and normally used on the previous
# command). The code and filename get pushed onto a stack. The argument is the
# filename.

# - pop: pop code from stack, write it to file

# - add: add a new snippet. Be sure to use a non-integer target id, as integer
# target id's come from parsing the book, and the code may make some assumtions
# about that.

directives = {
    # Help
    '1.05': 'ignore',

    # Host System Requirements
    '2.02': [
        # Add an automated check on the system requirements. We check that sh
        # is a symbolic link to bash, and that no required command is
        # missing. We don't check for mismatched versions.
        
        # Snippet 2.02_0 already runs "bash version-check.sh", but if I did a
        # 'replace', I'd have to include the entire script here, and that
        # wouldn't help readability.
        (0.5, 'add', """# Note the "|&" to pipe stdout and stderr together
bash version-check.sh |& grep -E \\
    "(ERROR: /bin/sh does not point to bash|: command not found)" &> /dev/null
err=$?
if [ $err -eq 1 ]; then
    # grep exit code is 1 if no lines were selected
    echo Check: 2.02: no errors detected.
else
    echo Check: 2.02: host system requirements FAILED, exiting.
    exit
fi
rm -f version-check.sh"""
        ),
    ],

    # Creating a File System on the Partition
    '2.05': [
        (1, 'ignore'),  # I already have a swap partition
    ],

    # Mounting the New Partition
    '2.07': [
        # Snippet #0 did the mount, so from this point on, $LFS is accessible
        
        # Attempting to copy the kernel config file will fail the first time
        # around, this is expected and can be safely ignored.
        (0.5, 'add', """mkdir $LFS/pkg_lfs
cp /var/tmp/lfs/<code>lfs_version</code>/script_0?.sh $LFS/pkg_lfs
cp /var/tmp/lfs/<code>lfs_version</code>/6.*_expected.txt $LFS/pkg_lfs
cp /var/tmp/lfs/<code>lfs_version</code>/6.*_script.sh $LFS/pkg_lfs
cp /var/tmp/lfs/<code>lfs_version</code>/config.<code>kernel_version</code> $LFS/pkg_lfs"""
        ),

        # Use this if you have multiple partitions for LFS, we don't.
        (1, 'ignore'),

        # LFS partition will be remounted when we run the scripts again
        (2, 'ignore'),

        # We're not creating a swap partition
        (3, 'ignore'),
    ],

    #  Introduction
    '3.01': [
        # Packages are downloaded the first time the parsing script runs, so
        # here we just need to copy them from LFS_DATA to $LFS/sources.
        (2, 'replace', 'cp <code>pkg_repository</code>/*.* $LFS/sources'),

        # Checksums have been checked after download, see pkg.py:get_all().
        (3, 'ignore'),
    ],

    # Adding the LFS User
    '4.03': [
        # We never login with user 'lfs', so it doesn't need a password
        (1, 'ignore'),

        # All the shell script code that needs to be run as user 'lfs' will be
        # generated by the python code and written into the script_01.sh file,
        # which we execute at this point.
        (4, 'replace', 'su - lfs /var/tmp/lfs/<code>lfs_version</code>/script_01.sh'),
        
        # This snippet is used internally by the python code to indicate "start
        # accumulating into a new file" and "push a new script on the script
        # stack"
        (4.5, 'push', '/var/tmp/lfs/<code>lfs_version</code>/script_01.sh'),
    ],

    # This is a tricky part, for two reasons. First, snippet #0 just puts an
    # 'exec' command into ~/.bash_profile file, it doesn't run it. Then snippet
    # #2 sources the file, and that's when the 'exec' gets executed. Second,
    # executing the 'su' command with a script makes the shell non-interactive,
    # hence it will not read .bashrc. This is solved by snippet #2.6.

    # Setting Up the Environment
    '4.04': [
        # Note the r-string here, otherwise \u gets interpreted as unicode escape
        (0, 'replace', r"""cat > ~/.bash_profile << "EOF"
exec env -i HOME=$HOME TERM=$TERM PS1='\u:\w\$ ' \
/bin/bash /var/tmp/lfs/<code>lfs_version</code>/script_02.sh
EOF"""
        ),
        # 4.04 #1 will be run normally, we're still inside script_01.sh. We
        # replace just to put a placeholder, to avoid hardcoding /mnt/lfs.
        (1, 'replace', """cat > ~/.bashrc << "EOF"
set +h
umask 022
LFS=<code>lfs_mount_point</code>
LC_ALL=POSIX
LFS_TGT=$(uname -m)-lfs-linux-gnu
PATH=/tools/bin:/bin:/usr/bin
export LFS LC_ALL LFS_TGT PATH
EOF"""
        ),
    
        # 4.04 #2 runs 'source ~/.bash_profile', which runs 'exec', thereby
        # starting a new shell running the script file script_02.
        (2.5, 'push', '/var/tmp/lfs/<code>lfs_version</code>/script_02.sh'),

        # This snippet inserts code at the very beginning of script_02.sh. We
        # do this because 'su' runs a non-interactive shell which does not read
        # /.bashrc, and we need it to be sourced (it defines LFS).
        (2.6, 'add', 'source ~/.bashrc')
    ],

    # About SBUs
    '4.05': 'ignore',  # But maybe set MAKEFLAGS="-j 8" elsewhere?

    # Toolchain Technical Notes
    '5.02': 'ignore',

    # Package building sections
    '5.07': [(2, 'ignore')],  # harmless warning
    '5.11': [(2, 'ignore')],  # tests are optional in chapter 5
    '5.12': [(3, 'ignore')],  # tests are optional in chapter 5
    '5.13': [(2, 'ignore')],  # tests are optional in chapter 5
    '5.14': [(3, 'ignore')],  # tests are optional in chapter 5
    '5.16': [(2, 'ignore')],  # tests are optional in chapter 5
    '5.17': [(2, 'ignore')],  # tests are optional in chapter 5
    '5.19': [(2, 'ignore')],  # tests are optional in chapter 5
    '5.20': [(2, 'ignore')],  # tests are optional in chapter 5
    '5.21': [(2, 'ignore')],  # tests are optional in chapter 5
    '5.22': [(2, 'ignore')],  # tests are optional in chapter 5
    '5.23': [(2, 'ignore')],  # tests are optional in chapter 5
    '5.25': [(2, 'ignore')],  # tests are optional in chapter 5
    '5.26': [(2, 'ignore')],  # tests are optional in chapter 5
    '5.27': [(2, 'ignore')],  # tests are optional in chapter 5
    '5.28': [(2, 'ignore')],  # tests are optional in chapter 5
    '5.31': [(2, 'ignore')],  # tests are optional in chapter 5
    '5.32': [(2, 'ignore')],  # tests are optional in chapter 5
    '5.33': [(2, 'ignore')],  # tests are optional in chapter 5
    '5.34': [(2, 'ignore')],  # tests are optional in chapter 5 [Xz-5.24]

    # Normally I would've ignored the entire "Stripping" section, but I need a
    # place to add the 2.7 snippet after all the sections in chapter 5 have
    # been done (and their sbus calculated). FIXME add a mechanism to add a
    # section.

    # Stripping
    '5.35': [
        (0, 'ignore'),
        (1, 'ignore'),
        (2, 'ignore'),
        (2.5, 'pop'),  # end of script_02.sh, pushed in 4.04_2.5
        (2.6, 'pop'),  # end of script_01.sh, pushed in 4.03_4.5
        # Back to the 'root' user, sending script code to script_00.sh
        (2.7, 'add', """cp /var/tmp/lfs/<code>lfs_version</code>/sbu_in_secs.txt $LFS/pkg_lfs
cp /var/tmp/lfs/<code>lfs_version</code>/sbu_total.txt $LFS/pkg_lfs"""
        ),
    ],

    # Package Management
    '6.03': 'ignore',
    
    # Entering the Chroot Environment
    '6.04': [
        # Note the r-string here, otherwise \u gets interpreted as unicode escape
        (0, 'replace', r"""chroot "$LFS" /tools/bin/env -i \
HOME=/root \
TERM="$TERM" \
PS1='(lfs chroot) \u:\w\$ ' \
PATH=/bin:/usr/bin:/sbin:/usr/sbin:/tools/bin \
/tools/bin/bash --login +h /pkg_lfs/script_03.sh"""
        ),
        (0.5, 'push', '/var/tmp/lfs/<code>lfs_version</code>/script_03.sh'),
    ],

    # Creating Essential Files and Symlinks
    '6.06': [(4, 'ignore')],  # don't care about the prompt

    # Glibc-2.31
    '6.09': [
        (12, 'ignore'),  # this is an alternative
        (15, 'ignore'),  # we set the time zone in one of our variables
    ],

    # Binutils-2.34
    '6.18': [(2, 'ignore')],  # alternate error message    

    # GMP-6.2.0
    '6.19': [
        (0, 'ignore'),  # not building for 32-bit x86
        (1, 'ignore'),  # optimize for host processor
    ],

    # Shadow-4.8.1
    '6.24': [
        (2, 'ignore'),  # don't build with Cracklib support
        (7, 'ignore'),  # don't enable shadowed passwords
        (8, 'ignore'),  # don't enable shadowed group passwords
        (9, 'ignore'),  # let useradd create a mailbox
        
        # Here you have the root password 'abcdef01' in the clear, this is done
        # so that the entire build script can be run unattended. Don't forget
        # to change it later, if securing access to the LFS system is
        # important.
        (10, 'replace', 'echo root:abcdef01 | chpasswd'),  # passwd root
    ],

    # GCC-9.2.0
    '6.25': [(21, 'ignore')],  # 32-bit version of the previous result

    # Ncurses-6.2
    '6.27': [(9, 'ignore')],  # don't create non-wide-character libraries

    # Bash-5.0
    '6.35': [
        (6, 'replace', 'exec /bin/bash --login +h /pkg_lfs/script_04.sh'),
        (6.5, 'push', '/var/tmp/lfs/<code>lfs_version</code>/script_04.sh'),
    ],

    # Texinfo-6.7
    '6.71': [(5, 'ignore')],  # only if the dir file needs to be recreated

    # Vim-8.2.0190
    '6.72': [
        (9, 'ignore'),  # vim -c ':options'
        (10, 'ignore'),  # spell files
    ],

    # Util-linux-2.35.1
    '6.74': [(3, 'ignore')],  # Running the test suite as root can be harmful

    # Stripping Again
    '6.80': 'ignore',  # snippet #1 does an 'exec', need more study here

    # Cleaning Up
    '6.81': [
        # Snippet #0 must still be run in the current chroot environment
        (0.5, 'pop'),  # end of script_04.sh, pushed in 6.35_6.5
        (0.6, 'pop'),  # end of script_03.sh, pushed in 6.04_0.5
        # Back to script_00.sh
        # Note the r-string here, otherwise \u gets interpreted as unicode escape
        (1, 'replace', r"""chroot "$LFS" /usr/bin/env -i \
HOME=/root \
TERM="$TERM" \
PS1='(lfs chroot) \u:\w\$ ' \
PATH=/bin:/usr/bin:/sbin:/usr/sbin \
/bin/bash --login /pkg_lfs/script_05.sh"""
        ),
        (1.5, 'push', '/var/tmp/lfs/<code>lfs_version</code>/script_05.sh'),
        # Snippets #2 and #3 will be generated into script_05.sh
    ],

    # Overview of Device and Module Handling
    '7.03': 'ignore',

    # Managing Devices
    '7.04': 'ignore',

    # General Network Configuration
    '7.05': [
        (3, 'ignore'),  # syntax
        (4, 'ignore'),  # valid address ranges
    ],

    # System V Bootscript Usage and Configuration
    '7.06': [
        # Set your own keyboard layout here
        (2, 'replace', """cat > /etc/sysconfig/console << "EOF"
KEYMAP=<code>fr</code>
EOF"""
        ),
        (3, 'ignore'),  # example
        (4, 'ignore'),  # example
        (5, 'ignore'),  # example
        (6, 'ignore'),  # example
        (7, 'ignore'),  # sysklogd_parms ?
        # Snippet 8 has class "auto", not "userinput"
    ],

    # Configuring the System Locale
    '7.07': [
        (0, 'ignore'),  # example commands
        (1, 'ignore'),  # example commands
        (2, 'ignore'),  # example output
        (3, 'ignore'),  # example commands
        (4, 'ignore'),  # example output
        (5, 'ignore'),  # example output
        # snippet #6 is all we need, to create the /etc/profile file
    ],

    # Creating the /etc/fstab File
    '8.02': [
        # Not using swap
        (0, 'replace', """cat > /etc/fstab << "EOF"
# file system  mount-point  type     options             dump  fsck
#                                                              order
/dev/<code>xxx</code>     /            <code>fff</code>    defaults            1     1
proc           /proc        proc     nosuid,noexec,nodev 0     0
sysfs          /sys         sysfs    nosuid,noexec,nodev 0     0
devpts         /dev/pts     devpts   gid=5,mode=620      0     0
tmpfs          /run         tmpfs    defaults            0     0
devtmpfs       /dev         devtmpfs mode=0755,nosuid    0     0

# End /etc/fstab
EOF"""
        ),
        (1, 'ignore'),  # optional
        (2, 'ignore'),  # optional
        (3, 'ignore'),  # optional
    ],

    # Linux-5.5.3
    '8.03': [
        (1, 'ignore'),  # example kernel configurations 
        (2, 'ignore'),  # UEFI support option
        
        # Once a kernel has been built, snippets 8.03_3.5 (below) and 9.03_0.6
        # in that build run have saved the kernel config file outside of the
        # chrooted environment. In the next run, snippet 2.07_0.5 copies the
        # config file back to $LFS (or / inside the chroot'ed environment) and
        # here we copy it back into the source directory.
        (2.5, 'add', 'cp /pkg_lfs/config.<code>kernel_version</code> .config'),

        ########################################################################
        # Snippet #3 is the 'make menuconfig' step. It needs to be run the
        # first time, to produce a .config file, so initially we do not ignore
        # the snippet (keep it commented out).
        #
        # Uncomment the next line after a first kernel has been built, and a
        # config file has been saved to /var/tmp/lfs/{version}, that file will
        # be reused.
        # (3, 'ignore'),
        ########################################################################

        # After running 'make menuconfig' once manually, a config file was
        # created in /sources/linux-5.28 (inside the chroot'ed environment).
        # Here we save it to /pkg_lfs (i.e. $LFS outside the chroot) before the
        # source directory gets removed).
        (3.5, 'add', 'cp .config /pkg_lfs/config.<code>kernel_version</code>'),

        (6, 'ignore'),  # we don't have a separate boot partition
    ],

    # We're not going to install grub on the target LFS system, we assume we're
    # building on a host Linux system that has grub installed, and we simply
    # add a menuentry for the new LFS system.
    
    # Normally I would keep this section, ignore most existing snippets, and
    # replace one of them with a new snippet to append some code to
    # grub.cfg. However, section 8.04 runs inside the chroot'ed environment
    # where the hosts's grub.cfg is not accessible, so this needs to be
    # postponed to section 9.03.

    # Using GRUB to Set Up the Boot Process
    '8.04': 'ignore',

    # The End
    '9.01': [
        (0, 'replace', 'echo <code>lfs_version</code> > /etc/lfs-release'),
        (1, 'replace', """cat > /etc/lsb-release << "EOF"
DISTRIB_ID="Linux From Scratch"
DISTRIB_RELEASE="<code>lfs_version</code>"
DISTRIB_CODENAME="<code>builder_name</code>"
DISTRIB_DESCRIPTION="Linux From Scratch"
EOF"""
        ),
        (2, 'replace', """cat > /etc/os-release << "EOF"
NAME="Linux From Scratch"
VERSION="<code>lfs_version</code>"
ID=lfs
PRETTY_NAME="Linux From Scratch <code>lfs_version</code>"
VERSION_CODENAME="<code>builder_name</code>"
EOF"""
        ),
    ],

    # Rebooting the System
    '9.03': [
        (0, 'ignore'),  # the next 'pop' logs us out
        (0.5, 'pop'),  # end of script_05.sh, pushed in 6.81_1.5
        # Back to the 'root' user, and out of the chroot'ed
        # environment. All script code will now go to script_00.sh.

        # Save the kernel config file from $LFS/pkg_lfs to /var/tmp
        (0.6, 'add', ('cp $LFS/pkg_lfs/config.<code>kernel_version</code>'
                          + ' /var/tmp/lfs/<code>lfs_version</code>')),
                          
        # Add a new LFS entry to the host's grub.cfg file, checking that it's
        # not already there
        (0.7, 'add', """# Add a new menuentry to grub.cfg, but only if it's not there already

# Create a file with the new menuentry we need in grub.cfg
temp1=$(mktemp new_menuentry.XXXXXX)
cat > $temp1 <<EOF

# Manually added for LFS
menuentry "GNU/Linux, Linux <code>kernel_version</code>-lfs-<code>lfs_version</code>" {
	  insmod ext2
	  set root=(hd0,<code>linux_part_nbr</code>)
	  linux /boot/vmlinuz-<code>kernel_version</code>-lfs-<code>lfs_version</code> root=/dev/<code>linux_partition</code> ro
}
EOF
nbr_lines=$(wc $temp1 | awk '{print $1}')

# Get the tail of grub.cfg for the same number of lines
temp2=$(mktemp grub_tail.XXXXXX)
tail -$nbr_lines <code>grub_cfg_path</code>/grub.cfg > $temp2

# If the files are identical, the menuentry we want is already present
diff $temp1 $temp2 > /dev/null
err=$?
if [ $err -eq 1 ]; then
    # Files differ, the new menuentry isn't there yet, I can append it
    cat $temp1 >> <code>grub_cfg_path</code>/grub.cfg
fi
rm -f $temp1 $temp2"""
        ),
        (3, 'ignore'),  # we don't have multiple partitions
        (4, 'ignore'),  # don't reboot automatically
    ],
    # You may now write script_00.sh to file
}

#-------------------------------------------------------------------------------
# Mapping variables or values to parameters
#-------------------------------------------------------------------------------

# If you add entries to 'directives', either 'add' or 'replace', that contain
# placeholders, then you must also add them here for replacement to occur.

param_mapping = {
    # section, snippet, args
    '2.05': [
        (0, ['linux_partition']),
        (1, ['swap_partition']),
    ],
    '2.06': [
        (0, ['lfs_mount_point']),
    ],
    '2.07': [
        (0, ['linux_partition']),
        (0.5, ['lfs_version', 'lfs_version', 'lfs_version', 'lfs_version', 'kernel_version']),
        (1, ['linux_partition', '']),
        (2, ['linux_partition', 'lfs_mount_point', 'fs_type']),
        (3, ['swap_partition']),
    ],
    '3.01': [
        (2, ['pkg_repository']),
    ],
    '4.03': [
        (4, ['lfs_version']),
        (4.5, ['lfs_version']),
    ],
    '4.04': [
        (0, ['lfs_version']),
        (1, ['lfs_mount_point']),
        (2.5, ['lfs_version']),
    ],
    '5.35': [
        (2.7, ['lfs_version', 'lfs_version']),
    ],
    '6.04': [
        (0.5, ['lfs_version']),
    ],
    '6.35': [
        (6.5, ['lfs_version']),
    ],
    '6.09': [
        (16, ['time_zone']),
    ],
    '6.59': [
        (0, ['paper_size']),
    ],
    '6.81': [
        (1.5, ['lfs_version']),
    ],
    '7.05': [
        (0, ['iface', 'onboot', 'iface', 'service', 'ip_address', 'gateway', 'prefix', 'broadcast']),
        (1, ['domain_name', 'nameserver1', 'nameserver2']),
        (2, ['hostname']),
        (5, ['fqdn', 'hostname', 'ip_address', 'fqdn', 'hostname', 'host_aliases']),
    ],
    '7.06': [
        (2, ['keymap']),
    ],
    '7.07': [
        (6, ['locale_params']),
    ],
    '8.02': [
        (0, ['linux_partition', 'fs_type']),
    ],
    '8.03': [
        (2.5, ['kernel_version']),
        (3.5, ['kernel_version']),
    ],
    '9.01': [
        (0, ['lfs_version']),
        (1, ['lfs_version', 'builder_name']),
        (2, ['lfs_version', 'lfs_version', 'builder_name']),
    ],
    '9.03': [
        (0.6, ['kernel_version', 'lfs_version']),
        (0.7, ['kernel_version', 'lfs_version', 'linux_part_nbr',
                   'kernel_version', 'lfs_version', 'linux_partition',
                   'grub_cfg_path', 'grub_cfg_path']),
    ],
}

# End of adjust_9.1.py
#===============================================================================