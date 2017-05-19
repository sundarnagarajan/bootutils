#!/bin/bash
# This script ASSUMES a Debian-derived distro (that uses dpkg, apt-get)
# It also assumes Ubuntu-like initramfs commands / config

PROG_PATH=${PROG_PATH:-$(readlink -e $0)}
PROG_DIR=${PROG_DIR:-$(dirname ${PROG_PATH})}
PROG_NAME=${PROG_NAME:-$(basename ${PROG_PATH})}
REMASTER_DIR=/root/remaster

KERNEL_DEB_DIR=${PROG_DIR}/../kernel-debs

if [ ! -d ${KERNEL_DEB_DIR} ]; then
    echo "KERNEL_DEB_DIR not a directory: $KERNEL_DEB_DIR"
    exit 0
fi
KERNEL_DEB_DIR=$(readlink -e $KERNEL_DEB_DIR)
KP_LIST=kernel_pkgs.list
KP_LIST=${KERNEL_DEB_DIR}/$KP_LIST

if [ "S(ls -A ${KERNEL_DEB_DIR}/*.deb 2>/dev/null)" ]; then
    if [ -x /etc/grub.d/30_os-prober ]; then
        chmod -x /etc/grub.d/30_os-prober
    fi
    dpkg -i ${KERNEL_DEB_DIR}/*.deb 2>/dev/null
    echo overlay >> /etc/initramfs-tools/modules
    update-initramfs -u 2>/dev/null

    rm -f ${KP_LIST}
    for f in ${KERNEL_DEB_DIR}/*.deb
    do
        dpkg-deb -f $f Package >> ${KP_LIST}
    done
    if [ -f ${KP_LIST} ]; then
        echo "New kernel packages installed:"
        cat ${KP_LIST} | sed -u -e 's/^/    /'
        mkdir -p $REMASTER_DIR
        cp ${KP_LIST} ${REMASTER_DIR}/
    fi
else
    echo "No deb files in $KERNEL_DEB_DIR"
    exit 0
fi
