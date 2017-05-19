#!/usr/bin/env python
from common_utils import require_root_or_exit
from efiutils import show_available_disks

if __name__ == '__main__':
    require_root_or_exit()
    show_available_disks()
