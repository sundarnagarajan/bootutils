# multiboot_install_grub.py

This script updates grub on a multiboot disk (or ANY disk that has
an EFI partition and a 'bios' partition of type EF02.
Partitions andpartition table are not affected and ONLY grub and EFI files are
updated.

This program must be run as root.
```
Usage: multiboot_install_grub.py dev_path

    dev_path: full path to disk (e.g. /dev/sdh}

Following are available disks
Disk path             RM    Model-Serial-Rev
/dev/nvme0n1          N     Samsung_SSD_960_EVO_250GB S3ESNX0HB04042L 1B7QCXE7
/dev/sda              N     Hitachi_HDS72105  A3EA
/dev/sdp              Y     Store_n_Go_Drive  1100
/dev/sds              Y     Voyager  1100
```

Upon choosing a disk, you will see output like the following:

```
# ./multiboot_install_grub.py /dev/sds
Scanning partitions on /dev/sds
Confirm disk to update grub. Data will not be affected /dev/sds


Model: Corsair Voyager (scsi)
Disk /dev/sds: 8020MB
Sector size (logical/physical): 512B/512B
Partition Table: gpt
Disk Flags:Disk /dev/sds: 15663104 sectors, 7.5 GiB
Logical sector size: 512 bytes
Disk identifier (GUID): 8943D01D-3963-460C-8B69-D52642E3BEAB
Partition table holds up to 128 entries
First usable sector is 34, last usable sector is 15663070
Partitions will be aligned on 2048-sector boundaries
Total free space is 2014 sectors (1007.0 KiB)
Removable: True
Disk Model-Rev: Voyager  1100

Num Start        End          Size    Code Name             FS          Path
  1 2048         43007        21.0MB  EF02 BIOSGRUB                     /dev/sds1
  2 43008        15663070     7997MB  EF00 EFI              vfat        /dev/sds2

Enter "YES" to confirm:
YES
MountedDir: Executing: mount /dev/sds2 /media/tmp_MountedDir_71gV4K
MountedDir: Executing: umount /media/tmp_MountedDir_71gV4K
MountedDir: Executing: mount /dev/sds2 /media/tmp_MountedDir_8daITL
Installing for i386-pc platform.
Installation finished. No error reported.
MountedDir: Executing: umount /media/tmp_MountedDir_8daITL
```
