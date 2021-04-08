#!/bin/bash
PROG_DIR=$(dirname "$BASH_SOURCE")
PROG_DIR=$(readlink -e "$PROG_DIR")
PROG_NAME=$(basename "$BASH_SOURCE")

source "$PROG_DIR"/efi_functions.sh || {
    >&2 echo "Could not source: $PROG_DIR/disk_partition_functions.sh"
    exit 1
}


create_update_efi $@
ret=$?
[[ $ret -ne 0 ]] && {
    >&2 echo "${PROG_NAME} : create_update_efi failed: Return code: $ret"
    exit $ret
}
