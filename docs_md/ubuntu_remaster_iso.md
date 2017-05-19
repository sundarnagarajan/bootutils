
# ubuntu_remaster_iso.sh
## Remastering stages
-  Extract ISO contents
-  Execute iso_pre scripts within extracted ISO (not chroot-ed)
-  Extract squashfs
-  Execute chroot scripts in chroot inside extracted squashfs
-  Recreate modified squashfs
-  Execute iso_post scripts within extracted ISO (not chroot-ed)
-  Recreate modified ISO

## Script plugin model
At each of the following stages, one or more scripts can be run

- iso_pre: **after** ISO extract, **before** extracting from squashfs
- chroot: **after** extracting squashfs within extracted squashfs as chroot
- iso_post **after** creating (modified) squashfs, **before** recreating modified ISO

At each stage, the following happens:

- The corresponding directory structure under ```remaster``` is copied to
a directory named ```.remaster``` (within extracted ISO or whthin extracted squashfs as the case may be).
- If that directory already existed, it is deleted and overwritten.
- All **executable** files under ```commands``` dir will be executed in lexicographic order
- If ```.remaster/commands/commands.list``` is present, only executable files under ```.remaster/commands``` listed in ```.remaster/commands/commands.list``` are executed.
- ```.remaster/commands/commands.list``` itself is **NEVER** executed - even if present and executable.
- For each command the working directory will be .remaster/commands
- ```.remaster``` will be deleted after **EACH** stage. Anything that needs to be kept needs to be copied by a script under ```.remaster/commands```.
- In the case of ```chroot```, commands are executed after chroot-ing into the extracted squashfs - so ```.remaster``` will be ```/.remaster```

## Execute iso_pre scripts within extracted ISO (not chroot-ed)

## Execute chroot scripts in chroot inside extracted squashfs

## Execute iso_post scripts within extracted ISO (not chroot-ede)

## File layout
```
bootutils  ---------- TOPLEVEL DIR
│
├── scripts  -------- Boot-disk related
│                     Contains remaster_iso_functions.sh, ubuntu_remaster_iso.sh
│                     Need to be copied / symlinked under remaster/chroot if desired 
│
│
└── remaster
    ├── chroot
    │   │
    │   ├── commands
    │   │   ├── commands.list
    │   │   ├── 01_install_firmware.sh
    │   │   ├── 02_install_kernels.sh
    │   │   ├── 03_remove_old_kernels.sh
    │   │   ├── 04_install_r8723_bluetooth.sh
    │   │   ├── 05_update_all_packages.sh
    │   │   └── 06_copy_scripts.sh
    │   │
    │   │
    │   ├── firmware - example (used by 01_install_firmware.sh)
    │   │
    │   ├── kernel-debs - example (used by 01_install_kernels.sh)
    │   │
    │   ├── r8723bs-bluetooth - example (used by 01_install_r8723_bluetooth.sh)
    │   │
    │   └── scripts - example (used by 01_copy_scripts.sh)
    │
    │
    ├── iso_post
    │   │ 
    │   ├── commands
    │   │   ├── 01_iso_kernel.sh
    │   │   └── 02_update_efi.sh
    │   │
    │   └── efi - example used by 02_update_efi.sh
    │
    │
    └── iso_pre
        │ 
        └── commands
```

