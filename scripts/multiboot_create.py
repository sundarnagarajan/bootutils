#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True
import os  # noqa: E402
from common_utils import require_root_or_exit  # noqa: E402
from efiutils import (
    DiskDetails,
    show_available_disks,
    erase_partition_table,
)  # noqa: E402


if __name__ == '__main__':
    require_root_or_exit()
    if len(sys.argv) < 2:
        print('Usage: %s dev_path' % (os.path.basename(sys.argv[0]),))
        print('')
        print('dev_path: full path to disk (e.g. /dev/sdh}')
        print('')
        print('Following are available disks')
        show_available_disks()
        exit(1)

    msg = 'Confirm destroying all partitions and data on %s' % (sys.argv[1],)
    try:
        d = DiskDetails(sys.argv[1])
        resp = d.confirm_action(msg)
    except:
        resp = erase_partition_table(sys.argv[1])
    if not resp:
        exit(0)
    d = DiskDetails(sys.argv[1])
    d.multiboot_erase_create()
