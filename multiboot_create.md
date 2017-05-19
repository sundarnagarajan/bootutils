# multiboot_create.py
This utility makes a disk (typically removable disk) bootable
on UEFI and non-UEFI systems and on UEFI systems with 32-bit or 64-bit
EFI loaders.

This program must be run as root.
Running ```sudo ./multiboot_create.py``` with no arguments will show
you the useage - similar to what is below.

```
Usage: multiboot_create.py dev_path

dev_path: full path to disk (e.g. /dev/sdh}

Following are available disks
Disk path             RM    Model-Serial-Rev
/dev/nvme0n1          N     Samsung_SSD_960_EVO_250GB S3ESNX0HB04042L 1B7QCXE7
/dev/sda              N     Hitachi_HDS72105  A3EA
/dev/sdb              N     Hitachi_HUA72302  A840
/dev/sdp              Y     Store_n_Go_Drive  1100
```

Upon choosing a disk (example below), you will be presented with a screen like
the following:

```
#./multiboot_create.py /dev/sds
Scanning partitions on /dev/sds
Confirm destroying all partitions and data on /dev/sds


Model: Verbatim Store n Go Drive (scsi)
Disk /dev/sds: 8023MB
Sector size (logical/physical): 512B/512B
Partition Table: gpt
Disk Flags:Disk /dev/sds: 15669248 sectors, 7.5 GiB
Logical sector size: 512 bytes
Disk identifier (GUID): F2DFF9D2-62A4-4688-B6A2-C052F4B2B871
Partition table holds up to 128 entries
First usable sector is 34, last usable sector is 15669214
Partitions will be aligned on 2048-sector boundaries
Total free space is 2014 sectors (1007.0 KiB)
Removable: True
Disk Model-Rev: Store_n_Go_Drive  1100

Num Start        End          Size    Code Name             FS          Path
  1 2048         43007        21.0MB  EF02 BIOSGRUB                     /dev/sds1
  2 43008        206847       83.9MB  EF00 EFI              vfat        /dev/sds2
  3 206848       15669214     7917MB  8300 BOOT             ext4        /dev/sds3

Enter "YES" to confirm:

```

If the disk that you chose had a DOS MBR partition table (and not a GPT
partition table), you would seel output that resembles the following:

```
# ./multiboot_create.py /dev/sds
Scanning partitions on /dev/sds
Confirm destroying all partitions and data on /dev/sds


Model: Corsair Voyager (scsi)
Disk /dev/sds: 8020MB
Sector size (logical/physical): 512B/512B
Partition Table: msdos
Disk Flags:***************************************************************
Found invalid GPT and valid MBR; converting MBR to GPT format
in memory. 
***************************************************************
Removable: True
Disk Model-Rev: Voyager  1100

Num Start        End          Size    Code Name             FS          Path
  1 62           15663103     8019MB  0700 Microsoft basic data vfat        /dev/sds1

Enter "YES" to confirm:

```

