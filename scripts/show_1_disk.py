#!/usr/bin/env python
import sys
sys.dont_write_bytecode = True
from common_utils import require_root_or_exit  # noqa: E402
from efiutils import show_available_disks, DiskDetails  # noqa: E402

if __name__ == '__main__':
    require_root_or_exit()
    if len(sys.argv) < 2:
        show_available_disks()
        exit(0)
    try:
        d = DiskDetails(sys.argv[1])
    except ValueError as e:
        print(e.message)
        exit(1)
    print(d)
