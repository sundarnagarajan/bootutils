#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage $(basename $0) <ROOT_PARTITION>"
    echo "    ROOT_PATITION: block device"
    exit 1
fi
PROG_PATH=${PROG_PATH:-$(readlink -e $0)}
PROG_NAME=$(basename ${PROG_PATH})
ROOT_PARTITION=$1


CHROOT_DIR=$(mktemp -d -p /media "tmp_${PROG_NAME}_XXXXXXXX")
echo "CHROOT_DIR: ${CHROOT_DIR}"

mount $ROOT_PARTITION $CHROOT_DIR
if [ $? -ne 0 ]; then
    echo "mount $ROOT_PARTITION $CHROOT_DIR failed"
    exit 1
fi
sleep 5

if [ ! -d "${CHROOT_DIR}"/boot/grub ]; then
    mkdir -p /boot/grub
    if [ $? -ne 0 ]; then
        echo "${CHROOT_DIR}/boot/grub not found and cannot be created"
        exit 1
    fi
fi

for d in run proc sys dev dev/pts
do
    mount --bind /$d ${CHROOT_DIR}/$d
done

chroot ${CHROOT_DIR} <<+
grub-mkconfig > /boot/grub/grub.cfg
+

for d in run proc sys dev/pts dev
do
    umount ${CHROOT_DIR}/$d
done

sleep 2
umount "${CHROOT_DIR}"
sleep 2
\rm -rf ${CHROOT_DIR}
