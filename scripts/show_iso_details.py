#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True
import os  # noqa: E402
from linuxiso import get_instance  # noqa: E402

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: %s <ISO_PATH' % (os.path.basename(sys.argv[0]),))
        exit(0)
    if not os.path.isfile(sys.argv[1]):
        print('File not found: ' + sys.argv[1])
        exit(1)

    iso_path = sys.argv[1]
    c = get_instance(iso_path)
    print('%s:' % (os.path.basename(iso_path), ))
    print('    Distro: %s' % (c.distro,))
    print('    Distro type: %s' % (c.distro_type,))
    print('    Distro subtype: %s' % (c.distro_subtype,))
    print('    Friendly name: %s' % (c.friendly_name,))
    print('    Remaster info: %s' % (c.remaster_info,))
    print('    Remaster time: %s' % (c.remaster_time,))
    print('    VolID: %s' % (c.volid,))
    print('    grub.cfg: %s' % (c.grub_cfg_path,))
    print('    64-bit EFI: %s' % (c.uefi64,))
    print('    32-bit EFI: %s' % (c.uefi32,))
