#!/bin/bash

if [ "$RFKILL_TYPE" != "bluetooth" ]; then
	exit 0
fi

EXPECTED_PLATFORM="OBDA8723"
EXPECTED_RFKILL_STATE="0"
PROG=$(basename $0)
BT_START_SCRIPT=/root/hardware/bluetooth/rtl8723bs_bt/start_bt.sh

ACTUAL_PLATFORM=${RFKILL_NAME%:*}


if [ "$ACTUAL_PLATFORM" != "$EXPECTED_PLATFORM" ]; then
  /usr/bin/logger -t r8723bs_bt_firmware "${PROG}: ignoring platform=${ACTUAL_PLATFORM}"
  exit 0
fi
if [ "$RFKILL_STATE" != "$EXPECTED_RFKILL_STATE" ]; then
	/usr/bin/logger -t r8723bs_bt_firmware "${PROG}: ignoring RFKILL_STATE=$RFKILL_STATE"
	exit 0
fi
if [ ! -x $BT_START_SCRIPT ]; then
	/usr/bin/logger -t r8723bs_bt_firmware "${PROG}: not executable: $BT_START_SCRIPT"
	exit 0
fi

/usr/bin/logger -t r8723bs_bt_firmware "${PROG}: running for platform=${ACTUAL_PLATFORM} RFKILL_STATE=$RFKILL_STATE"
$BT_START_SCRIPT 2>&1 | /usr/bin/logger -t r8723bs_bt_firmware
