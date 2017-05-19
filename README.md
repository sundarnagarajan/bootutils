# bootutils
Utilities to create bootable disks, remaster ISO images, make multiboot disk images

## Goals - who needs this?
### Use case 1: Multiboot disk image
- You want to put one or more ISO images on a single disk and be able to choose which ISO to boot
- You want to be able to boot on UEFI as well as non-UEFI systems
- You want to boot on newer Cherry Trail or Bay Trail (Intel Atom) machines that often have a 32-bit EFI loader, while typical Linux ISO images only support UEFI in 64-bit images
- You want to boot a 64-bit Linux ISO on machines having only a 32-bit EFI loader
- You do not want to have to edit grub.cfg by hand after adding ISO images

### Use case 2: Remastering ISO
- You want to add a custom kernel to an ISO to enable support for newer hardware while in the live session
- You want the custom kernel to be automatically installed while installing from the live ISO
- You want to install additional packages that are available in the live session **AND** carried into the installed image
- You want to add additional files - e.g. utilities, scripts, data files - that are available in the live session **AND** carried into the installed image
- You want to make a UEFI-compatible 64-bit Linux ISO image bootable on a machine with a 32-bit EFI loader
- You want to create an updated ISO with all packages updated

### Use case 3: Create boot disk on separate disk
- You have a disk that is seen and usable under Linux, but is not seen by the BIOS / UEFI - e.g. newer PCI-Express NVME M.2 disks
- You need a boot image that can contain ONLY /boot, which will then boot from the other disk that the BIOS / UEFI cannot see

### Use case 4: Fix grub-install errors
- Linux installer fails after grub-install step - usually bug in installer
- You want to recover and continue


## Operating system support
Linux-only. No effort spent on supporting other OS

## Linux distributions supported
The scripts should work on any *modern* Linux distribution. I test on Ubuntu Xenial 16.04.2 LTS. The list of packages required are specific to Ubuntu (Xenial), but the dependency is based on OS commands requried and the OS commands required are listed below, to allow usage on virtually any Linux distribution.

### Remastering ISOs
Remastering ISOs is *currently* supported **ONLY for Ubuntu ISOs**. This includes:

- Ubuntu (*standard* Unity)
- Official Ubuntu flavors such as Ubuntu Mate, xubuntu lubuntu, kubuntu, edubuntu etc)
- Ubuntu derivatives such as Linux Mint (only Linux Mint tested)

In the future, I intend to support major distributions, such as Fedora, Arch, GRML, Red Hat etc.

The sample remastering scripts included are Ubuntu-specific.

### Multiboot
Multiboot refers to creating a bootable disk that can contain multiple bootable ISO images, supporting a boot-time menu to choose the ISO that you want to boot.

Once a multiboot image is created, you can add ISO images by copying ISO files to *ISO* directory on the disk and run ```multiboot_update_config.py``` to automatically update the menu (```grub.cfg```).

Multiboot disk images support:
- Booting on UEFI and non-UEFI host systems
- Booting on UEFI host systems with 32-bit or 64-bit EFI loaders
- Boot 64-bit ISO on a UEFI host system with native 64-bit support even if EFI loader is 32-bit
- Boot 32-bit ISO on a UEFI host system with native 64-bit support even if EFI loader is 64-bit

Multiboot supports the following distributions within as ISOs:

- Ubuntu - all official flavors
- Linux Mint
- GRML
- Debian

In the future, I intend to support major distributions, such as Fedora, Arch, GRML, Red Hat etc.

Multiboot does **NOT** support ISOs that are not **live CD images** (such as Ubuntu server install ISOs) and probably never will.

## Commands and packages required

| Command | Ubuntu Package | Ubuntu package version tested |
| ------- | -------------- | ----------------------------- |
| lsblk | util-linux | 2.27.1-6ubuntu3.2 |
| parted | parted | 3.2-15 |
| sgdisk | gdisk | 1.0.1-1build1 |
| blkid | util-linux | 2.27.1-6ubuntu3.2 |
| umount | mount | 2.27.1-6ubuntu3.2 |
| mkfs.vfat | dosfstools | 3.0.28-2ubuntu0.1 |
| grub-install | grub2-common | 2.02~beta2-36ubuntu3.9 |
| grub-mkdevicemap | grub-common | 2.02~beta2-36ubuntu3.9 |
| grub-mkconfig | grub-common | 2.02~beta2-36ubuntu3.9 |
| grub-mkstandalone | grub-common | 2.02~beta2-36ubuntu3.9 |

On Ubuntu (or other Debian-derived distributions, probably), you can run ```required_pkgs.sh``` to find the exact missing packages you need to install.

## Help on individual utilities

[multiboot_create.py] (docs_md.multiboot_create.md)
