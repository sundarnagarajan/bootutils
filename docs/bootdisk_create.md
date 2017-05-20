# bootdisk_create.py

This script creates a UEFI-only bootable disk that contains ONLY EFI partition and /boot partition. It also has a built-in reference to UUID of the root filesystem. It is useful in situations like:
- You have a disk that is seen and is usable in Linux, but an older UEFI firmware cannot see the disk and boot from it. An example I have is a PCI-Express NVME M.2 disk that cannot be seen by my UEFI firmware.

This method puts a file named ```grub_fs_uuid.cfg``` in the root dir of the EFI partition. The embedded grub config looks for and reads this file to locate the root disk and locate grub.cfg.

If the root partition is recreated - e.g. from a backup - only ```grub_fs_uuid.cfg``` needs to be updated with the new UUID.

If the additional steps listed at  the bottom are performed, ```update-grub``` will update ```boot/grub.cfg``` through the ```/boot``` symlink

This program must be run as root.

```
Usage: bootdisk_create.py dev_path boot_dir

dev_path: path to disk (e.g. /dev/sdh}
boot_dir: path to copy boot files from

Following are available disks
Disk path             RM    Model-Serial-Rev
/dev/nvme0n1          N     Samsung_SSD_960_EVO_250GB S3ESNX0HB04042L 1B7QCXE7
/dev/sda              N     Hitachi_HDS72105  A3EA
/dev/sdp              Y     Store_n_Go_Drive  1100
/dev/sds              Y     Voyager  1100
```

Upon choosing a disk, you will see output like the following:

```
# ./bootdisk_create.py /dev/sds
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
```

## Additional steps required after creating boot disk
Customize as requried

```bash
cd /
mkdir -p /mnt/boot
ln -s /mnt/boot/boot /boot
```

Add line to ```/etc/fstab``` to mount ```/boot``` and ```/boot/efi```from boot disk created:
```
UUID=86b56faf-910c-4e56-9eb0-883774bc2a09 /mnt/boot       ext4    errors=remount-ro 0       2
UUID=2398-BBB5  /mnt/boot/boot/efi       vfat    umask=0077      0       2
```
