#!/bin/bash
REQD_PKGS="grub-efi-ia32-bin grub-efi-amd64-bin grub-pc-bin grub2-common grub-common util-linux parted gdisk mount xorriso genisoimage squashfs-tools rsync"

$(dirname $0)/pkgs_missing_from.sh $REQD_PKGS
