# Cleanup host system after an interrupted LFS build

umount /mnt/lfs
userdel lfs
rm -rf /home/lfs
rm /tools
