# make_bootable.py

Sometimes your grub-install fails and you're left without a boot disk that will work. Sometimes this happens at the end of a Linux install.

This script takes two pieces of information and makes your boot disk bootable - on UEFI or non-UEFI systems

## Pre-requisites
- You must have created the disk image originally using ```erase_initialize_disk.py```
- What is important is it should have:
    - A GPT partition table (not MBR)
    - A 'BIOS' partition (GPT partition code EF02). If such a partition is not present, grub-mbr will not be used, and the disk will not boot on non-UEFI systems
    - An EFI partition (GPT partition code EF00)

## Information you need
### dev_path
The boot disk device path. This should be the path to the DISK and not a partition. So ```/dev/sda``` may be correct, but ```/dev/sda1``` is wrong

### root_partition
The path to where your partition is. It may be something like ```/dev/sda1```



This program must be run as root.

```
./make_bootable.py 
[sudo] password for sundar: 
Usage: make_bootable.py dev_path root_partition [nombr]

    dev_path:       full path to disk (e.g. /dev/sdh}
    root_partition: root partition path (e.g. /dev/sdh3)

    nombr: if third argument is nombr, then grub-mbr is NOT 
         installed to MBR EVEN if BIOS partition is present


Following are available disks
Disk path             RM    Model-Serial-Rev
/dev/nvme0n1          N     Samsung_SSD_960_EVO_250GB S3ESNX0HB04042L 1B7QCXE7
/dev/sda              N     Hitachi_HDS72105  A3EA
/dev/sdp              Y     Store_n_Go_Drive  1100
/dev/sds              Y     Voyager  1100
```
