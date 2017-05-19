#!/usr/bin/env python
import sys
import os
from common_utils import require_root_or_exit
from efiutils import (
    DiskDetails,
    show_available_disks,
    erase_partition_table,
)


if __name__ == '__main__':
    require_root_or_exit()
    if len(sys.argv) < 2:
        print('Usage: %s dev_path boot_dir' % (
            os.path.basename(sys.argv[0]),
        ))
        print('')
        print('dev_path: path to disk (e.g. /dev/sdh}')
        print('boot_dir: path to copy boot files from')
        print('')
        print('Following are available disks')
        show_available_disks()
        exit(1)
    boot_dev = sys.argv[1]
    boot_dir = sys.argv[2]
    msg = 'Confirm destroying all partitions and data on %s' % (sys.argv[1],)
    try:
        d = DiskDetails(boot_dev)
        resp = d.confirm_action(msg)
    except:
        resp = erase_partition_table(boot_dev)
    if not resp:
        exit(0)
    d = DiskDetails(boot_dev)
    d.bootdisk_erase_create()
    boot_partition = d.partitions[-1].path
    d.bootdisk_populate_update_cfg(
        boot_partition=boot_partition, boot_dir=boot_dir)
