#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True
from common_utils import require_root_or_exit  # noqa: E402
from efiutils import show_available_disks  # noqa: E402

if __name__ == '__main__':
    require_root_or_exit()
    show_available_disks()
