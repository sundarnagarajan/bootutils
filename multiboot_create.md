# multiboot_create.md
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

