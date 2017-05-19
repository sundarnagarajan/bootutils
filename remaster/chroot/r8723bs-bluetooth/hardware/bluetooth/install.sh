#!/bin/bash
PROG_DIR=$(readlink -e $(dirname $0))
SCRIPTS_DIR=${PROG_DIR}/scripts

# Check that required scripts are present
if [ ! -x ${SCRIPTS_DIR}/bluetooth_udev_rules.sh ]; then
    echo "Missing or not executable: ${SCRIPTS_DIR}/bluetooth_udev_rules.sh"
    exit 1
elif [ ! -f ${SCRIPTS_DIR}/bluetooth_r8723bs.rules ]; then
    echo "Missing: ${SCRIPTS_DIR}/bluetooth_r8723bs.rules"
    exit 1
elif [ ! -f ${SCRIPTS_DIR}/r8723bs_bluetooth.service ]; then
    echo "Missing: ${SCRIPTS_DIR}/r8723bs_bluetooth.service"
    exit 1
fi

\cp -fv ${SCRIPTS_DIR}/bluetooth_r8723bs.rules /etc/udev/rules.d/
\cp -fv ${SCRIPTS_DIR}/r8723bs_bluetooth.service /etc/systemd/system/

mkdir -p /etc/systemd/system/bluetooth.service.wants
\rm -fv /etc/systemd/system/bluetooth.service.wants/r8723bs_bluetooth.service

ln -sv /etc/systemd/system/r8723bs_bluetooth.service /etc/systemd/system/bluetooth.service.wants/
