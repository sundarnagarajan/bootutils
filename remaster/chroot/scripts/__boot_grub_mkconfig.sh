#!/bin/bash
# Move /boot around and then run grub-mkconfig and restore /boot


if [ -z "$1" ]; then
    echo "Usage $(basename $0) <BOOT_PARTITION> "
    echo "    BOOT_PATITION: block device"
    exit 1
fi

PROG_PATH=${PROG_PATH:-$(readlink -e $0)}
PROG_NAME=$(basename ${PROG_PATH})
BOOT_PARTITION=$1

cd /
MOVED_BOOT_DIR=$(mktemp -d -p . "moved_boot_XXXXXXXX")
TEMP_BOOT_DIR=$(mktemp -d -p . "temp_boot_XXXXXXXX")

mv /boot $MOVED_BOOT_DIR/

mount $BOOT_PARTITION ${TEMP_BOOT_DIR}
if [ $? -ne 0 ]; then
    echo "mount $BOOT_PARTITION boot failed"
    cd /media
    umount ${CHROOT_DIR}
    exit 1
fi
ln -s ${TEMP_BOOT_DIR}/boot /boot
if [ ! -d boot/grub ]; then
    mkdir -p boot/grub
    if [ $? -ne 0 ]; then
        echo "${CHROOT_DIR}/boot/grub not found and cannot be created"
        exit 1
    fi
fi
grub-mkconfig > /boot/grub/grub.cfg

cd /
rm -rf /boot
umount ${TEMP_BOOT_DIR}
rmdir ${TEMP_BOOT_DIR}
mv $MOVED_BOOT_DIR/boot /
rmdir $MOVED_BOOT_DIR
