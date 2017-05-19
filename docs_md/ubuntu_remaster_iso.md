
# ubuntu_remaster_iso.sh
## Remastering stages
-  Extract ISO contents
-  Execute iso_pre scripts within extracted ISO (not chroot-ed)
-  Extract squashfs
-  Execute chroot scripts in chroot inside extracted squashfs
-  Recreate modified squashfs
-  Execute iso_post scripts within extracted ISO (not chroot-ede)
-  Recreate modified ISO

## Script plugn model
At each of the following stages, one or more scripts can be run

- iso_pre: **after** ISO extract, **before** extracting from squashfs
- chroot: **after** extracting squashfs within extracted squashfs as chroot
- iso_post **after** creating (modified) squashfs, **before** recreating modified ISO

At each stage, the corresponding directory structure under ```remaster``` is copied to
a directory named ```.remaster``` (within extracted ISO or whthin extracted squashfs as the case may be). If that directory already existed, it is deleted and overwritten.

All **executable** files under ```commands``` dir will be executed in lexicographic order

If ```.remaster/commands/commands.list``` is present, only executable files under ```.remaster/commands``` listed in ```.remaster/commands/commands.list``` are executed. ```.remaster/commands/commands.list``` itself is **NEVER** executed - even if present and executable.

```.remaster``` will be deleted after **EACH** stage. Anything that needs to be kept needs to be copied by a script under ```.remaster/commands```.

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
    ├── chroot  ----- Everything under this is copied under /.remaster in squashfs
    │   │             and /.remaster/toplevel.sh is executed in CHROOT which will run
    │   │             all executable files under /.remaster/commands in lexicographic
    │   │             order
    │   │             if /.remaster/commands/commands.list is present only executable files
    │   │             under /.remaster/commands listed in /.remaster/commands/commands.list
    │   │             are executed. /.remaster/commands/commands.list is NEVER executed -
    │   │             even if present and executable
    │   │
    │   │             /.remaster will be deleted after this step - anything that needs
    │   │             to be kept needs to be copied by a script under /.remaster/commands
    │   │
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
    ├── iso_post ---- Everything in this directory is copied under /.remaster in ISO
    │   │             extract directory. This is done AFTER executing under chroot
    │   │             OVERWRITING (but NOT deleting) anything that may have been in
    │   │             that dir after running iso_pre. /.remaster/toplevel.sh is
    │   │             executed, which will run all executable files under
    │   │             /.remaster/commands in lexicographic order
    │   │             if /.remaster/commands/commands.list is present only executable files
    │   │             under /.remaster/commands listed in /.remaster/commands/commands.list
    │   │             are executed. /.remaster/commands/commands.list is NEVER executed -
    │   │             even if present and executable
    │   │ 
    │   │             /.remaster will be deleted after this step - anything that needs
    │   │             to be kept needs to be copied by a script under /.remaster/commands
    │   │
    │   │ 
    │   ├── commands
    │   │   ├── 01_iso_kernel.sh
    │   │   └── 02_update_efi.sh
    │   │
    │   └── efi - example used by 02_update_efi.sh
    │
    │
    └── iso_pre ----- Everything in this directory is copied under /.remaster in ISO
        │             This is done BEFORE executing under chroot
        │             /.remaster/toplevel.sh is, which will run all executable files under
        │             /.remaster/commands in lexicographic order
        │             if /.remaster/commands/commands.list is present only executable files
        │             under /.remaster/commands listed in /.remaster/commands/commands.list
        │             are executed. /.remaster/commands/commands.list is NEVER executed -
        │             even if present and executable
        │
        │             /.remaster will NOT be deleted after this step - will be deleted
        │             after iso_post step
        │
        │ 
        └── commands
```

