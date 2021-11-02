#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True
from common_utils import require_root_or_exit  # noqa: E402
from efiutils import (
    DiskDetails, show_available_disks, erase_partition_table
)  # noqa: E402

if __name__ == '__main__':
    require_root_or_exit()
    if len(sys.argv) < 2:
        print('Usage: create_efi.py dev_path [nombr]')
        print('')
        print('dev_path: full path to disk (e.g. /dev/sdh)')
        print('nombr: if parameter present, BIOS partition is NOT created')
        print('')
        print('If second parameter is missing or anything other than nombr')
        print('BIOS partition is created for compatibility with grub-mbr')
        print('')
        print('Following are available disks')
        show_available_disks()
        exit(1)

    need_bios_partition = True
    if len(sys.argv) > 2:
        need_bios_partition = (sys.argv[2] != 'nombr')
    msg = 'Confirm destroying all partitions and data on %s' % (sys.argv[1],)
    try:
        d = DiskDetails(sys.argv[1])
        resp = d.confirm_action(msg)
    except:
        resp = erase_partition_table(sys.argv[1])
    if not resp:
        exit(0)
    d = DiskDetails(sys.argv[1])
    d.erase_disk()
    d.create_efi_partition(bios_partition=need_bios_partition)
    print(d)
