# parse_all.sh -

for i in 7.6 9.0 9.0-systemd 9.1-rc1 9.1-rc1-systemd ; do
    python lfs_explore.py ~/lfs/$i
done