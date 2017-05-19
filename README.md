# bootutils
Utilities to create bootable disks, remaster ISO images, make multiboot disk images

## Linux distributions supported
The scripts should work on any *modern* Linux distribution. I test on Ubuntu Xenian 16.04.2 LTS. The list of packages required are specific to Ubuntu (Xenial), but the dependency is based on OS commands requried and the OS commands required are listed below, to allow usage on virtually any Linux distribution.

### Remastering ISOs
Remastering ISOs is *currently* supported **ONLY for Ubuntu ISOs**. This includes:

- Ubuntu (*standard* Unity)
- Official Ubuntu flavors such as Ubuntu Mate, xubuntu lubuntu, kubuntu, edubuntu etc)
- Ubuntu derivatives such as Linux Mint (only Linux Mint tested)

In the future, I intend to support major distributions, such as Fedora, Arch, GRML, Red Hat etc.

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

Multiboot does **NOT** support ISOs that are not *live CD images* (such as Ubuntu server install ISOs) and probably never will.

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


