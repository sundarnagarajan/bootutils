#!/usr/bin/env python
import sys
import os
from common_utils import require_root_or_exit
from efiutils import (
    DiskDetails,
    update_fstab_boot_efi,
    show_available_disks,
)


if __name__ == '__main__':
    require_root_or_exit()
    if len(sys.argv) < 3:
        print('Usage: %s dev_path root_partition [nombr]' % (
            os.path.basename(sys.argv[0]),))
        print('')
        print('    dev_path:       full path to disk (e.g. /dev/sdh}')
        print('    root_partition: root partition path (e.g. /dev/sdh3)')
        print('')
        print('    nombr: if third argument is nombr, then grub-mbr is NOT ')
        print('         installed to MBR EVEN if BIOS partition is present')
        print('')
        print('Following are available disks')
        show_available_disks()
        exit(1)
    boot_dev = sys.argv[1]
    root_partition = sys.argv[2]
    update_mbr = True
    if len(sys.argv) > 3:
        update_mbr = (sys.argv[3] != 'nombr')

    d = DiskDetails(boot_dev)
    partnum = d.partnum_by_path(root_partition)
    msg = 'Confirm disk. Data will not be affected %s' % (d.devpath,)
    if d.confirm_action(msg, partnum):
        d.make_bootable(root_partition, update_mbr)
        update_fstab_boot_efi(boot_dev, root_partition)
