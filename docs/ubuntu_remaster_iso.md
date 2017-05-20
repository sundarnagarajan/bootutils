
# ubuntu_remaster_iso.sh
## Remastering stages
-  Extract ISO contents
-  Extract squashfs
-  Recreate modified squashfs
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
- In the case of ```chroot```, commands are executed after chroot-ing into the extracted squashfs - so ```.remaster``` will be ```/.remaster```
- ```.remaster``` will be deleted after **chroot** stage. Anything that needs to be kept needs to be copied by a script under ```.remaster/commands```. Contents of ```.remaster``` is retained in extracted ISO between iso_pre and iso_post (except ```commands``` directory).
- If any command exits with an error, subsequent commands **are still executed**. To avoid execution of subsequent commands plugin command scripts must maintain state on the filesystem.

## iso_pre stage
**IF** iso_pre directory is present, commands under ```iso_pre/commands``` are executed sequentially within extracted ISO (not chroot-ed).

I have not found a use for executing scripts at this stage. Perhaps one may want to inspect and store the state of the extracted ISO filesystem for comparison with post-modification state.

## Execute chroot scripts in chroot inside extracted squashfs
**IF** chroot directory is present, commands under ```chroot/commands``` are executed sequentially within extracted squashfs (chrooted).

A lot of the interesting capabilities are achieved by scripts running at this stage:
- You want the custom kernel to be automatically installed while installing from the live ISO
- You want to install additional packages that are available in the live session AND carried into the installed image
- You want to add additional files - e.g. utilities, scripts, data files - that are available in the live session AND carried into the installed image
- You want to create an updated ISO with all packages updated

## Execute iso_post scripts within extracted ISO (not chroot-ed)
**IF** iso_post directory is present, commands under ```iso_post/commands``` are executed sequentially within extracted ISO (not chroot-ed).

Some uses:
- Copy custom kernel to location inside ISO so that live session also uses custom kernel (and initrd)
- You want to make a UEFI-compatible 64-bit Linux ISO image bootable on a machine with a 32-bit EFI loader


## Usage and command line parameters
- Needs to be executed as root (```sudo ubuntu_remaster_iso.sh```)
- Executing without any parameters provides usage help:

```
ubuntu_remaster_iso.sh ISO_PATH EXTRACT_DIR OUTPUT_ISO

    ISO_PATH:      Full path to ISO to extract
    EXTRACT_DIR:  Dir to extract under. Will be (re-)created
    OUTPUT_ISO: Full path to output ISO
```

```REMASTER_CMDS_DIR```: If this environment variable is set, it is expected to point at directory with sub-directories named ```iso_pre```, ```chroot```, ```iso_post```.
- If the variable is set and the directory is not found, no remaster commands are executed.
- If the variable is not set it defaults to ```bootutils/remaster```
- If any of the directories ```iso_pre```, ```chroot```, ```iso_post``` do not exist, they are ignored. If any of the directories are empty or commands directory is empty or does not contain any executable files, that stage is skipped

## Best practices
- Do not choose ```REMASTER_CMDS_DIR``` to be a directory name containing spaces / special characters
- Do not use spaces or special characters in names of commands in ```commands``` directory

## Sample remaster commands
| Stage | Command | What it does | Default state |
| ----- | ------- | ------------ | ------------- |
| chroot | 01_install_firmware.sh | Install firmware required by RTL 8723bs Wifi chipset | Disabled |
| chroot | 02_install_kernels.sh | Install custom kernels does nothing if kernel_debs dir is empty | Enabled |
| chroot | 03_remove_old_kernels.sh | Removes all kernels **EXCEPT** kernels installed by ```02_install_kernels.sh```. Does nothing if ```02_install_kernels.sh``` did nothing | Enabled |
| chroot | 04_install_r8723_bluetooth.sh | Install systemd service and udev rules to make Bluetooth work on RTL 8723bs chipset | Disabled |
| chroot | 05_update_all_packages.sh | Update all packages | Enabled |
| chroot | 06_install_grub_packages.sh | Install UEFI-i386 UEFI-amd64 and non-UEFI grub packages | Enabled |
| chroot | 07_apt_cleanup.sh | apt autoremove and cleanup apt cache | Enabled |
| chroot | 08_copy_scripts.sh | Copy scripts under /root/remaster | Enabled |
| iso_post | 01_iso_kernel.sh | Update kernel in ISO (live session) if kernel was updated in chroot stage by ```02_install_kernels.sh```. Does nothing otherwise | Enabled |
| iso_post | 02_update_efi.sh | Makes ISO bootable in 32-bit and 64-bit EFI loaders | Enabled |

## File layout
```
bootutils  ---------- TOPLEVEL DIR
│
├── scripts  -------- Boot-disk related
│                     Contains remaster_iso_functions.sh, ubuntu_remaster_iso.sh
│                     Need to be copied / symlinked under remaster/chroot if desired 
│
└── remaster
    ├── chroot
    │   │
    │   ├── commands
    │   │   ├── commands.list (optional)
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
    │   │   ├── commands.list (optional)
    │   │   ├── 01_iso_kernel.sh
    │   │   └── 02_update_efi.sh
    │   │
    │   └── efi - example used by 02_update_efi.sh
    │
    │
    └── iso_pre
        │ 
        └── commands
            └── commands.list (optional)
```

