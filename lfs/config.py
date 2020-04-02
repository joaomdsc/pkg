# config.py - local configuration for your LFS build

"""Configuration data to customize the LFS build.

This file defines a dictionary of configuration values that are used by ths
python code to customize the code snippets from the book.

If you want to see exactly how each variable gets used, take a look at the
'param_mapping' structure in the adjust_{version}.py file, it indicates for
each snippet which variable must be used to replace each placeholder."""

#-------------------------------------------------------------------------------
# variables
#-------------------------------------------------------------------------------

variables = dict(
    linux_partition='sda3',
    linux_part_nbr='3',
    swap_partition='',
    lfs_mount_point='/mnt/lfs',
    time_zone='Europe/Paris',
    paper_size='A4',
    # Network config with systemd
    network_device='',
    domain_name='',
    nameserver1='192.168.0.254',
    nameserver2='',    
    hostname='lfshost',
    fqdn='',    
    ip_address='',    
    host_aliases='',    
    locale_params='en_US.utf8',    
    fs_type='ext4',
    grub_cfg_path='/boot/grub',  # distribution-dependent
    builder_name='<your name here>',
    keymap='fr'
    # Network config in /etc/sysconfig without systemd
    onboot='yes',
    iface='eth0',
    service='ipv4-static',
    gateway='192.168.1.1',
    prefix='24',
    broadcast='192.168.1.255',
    # The following variables are dynamic, filled in by parse_book()
    pkg_repository='',
    lfs_version='',
    kernel_version='',
)

# End of config.py
#===============================================================================