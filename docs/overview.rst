Overview
========

What's in here ?
----------------

This repository holds python scripts dealing with the common topic of software
packages (source or binary) and their use on building applications or entire
systems such as Linux.

Most of it is work-in-progress on debian or yum-based packaging, aiming towards
a single, common API to support the usual operations, that has not yet reached
the point where it could be useful to anyone. 

One sub-project, however, has achieved actual usability, and that's the **lfs**
(as in `Linux From Scratch`_) sub-project, which automates the building of an
entire linux system from source code, as described in `the LFS book`_.

pkg_lfs
-------

Linux From Scratch is a community-maintained online book with instructions for
downloading, configuring, and compiling all the necessary software to obtain a
bootable, usable Linux system. The book is an extraordinary resource, embodying
the collective knowledge and the efforts of all the LFS volunteers who study
every individual piece of the linux machinery to determine a set of compatible
parameters to make it all work together.

This project, referred to as **pkg_lfs** in this documentation, aims to relieve
you of the manual repetitive task of running each piece of shell script one
after the other. It's a set of python scripts that parse the LFS book and
generate shell scripts that are then used to automate the building
process. Using pkg_lfs, you basically just set the values of a few variables,
launch a script, and wait a few hours: when the script is done, you can boot
your new Linux system.

Hopefully pkg_lfs will reduce the time and effort required to unlock the huge
value of the LFS book and to get that customized Linux system up and
running. For all the details on how to use the software, see the pkg_lfs
documentation in :ref:`automating-lfs`.

.. _Linux From Scratch: http://www.linuxfromscratch.org/
.. _the LFS book: http://www.linuxfromscratch.org/lfs/view/stable-systemd/

.. sectionauthor:: Joao Moreira <joao.moreiradsc@gmail.com>
