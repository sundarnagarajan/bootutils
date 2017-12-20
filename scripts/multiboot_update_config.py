#!/usr/bin/env python
import sys
sys.dont_write_bytecode = True
import os  # noqa: E402
from common_utils import require_root_or_exit  # noqa: E402
from efiutils import (
    DiskDetails,
    show_available_disks,
)  # noqa: E402


if __name__ == '__main__':
    require_root_or_exit()
    if len(sys.argv) < 2:
        print('Usage: %s dev_path' % (os.path.basename(sys.argv[0]),))
        print('')
        print('    dev_path: full path to disk (e.g. /dev/sdh}')
        print('')
        print('Following are available disks')
        show_available_disks()
        exit(1)
    d = DiskDetails(sys.argv[1])
    msg = ('Confirm disk to update grub config. '
           'Data will not be affected %s') % (d.devpath,)
    if d.confirm_action(msg):
        d.multiboot_update_config()
