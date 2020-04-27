#!/bin/bash
# Ubuntu-specific script


PROG_PATH=${PROG_PATH:-$(readlink -e $0)}
PROG_DIR=$(dirname ${PROG_PATH})
PROG_NAME=$(basename ${PROG_PATH})

if [ -f "${PROG_DIR}"/remaster_iso_functions.sh ]; then
    source "${PROG_DIR}"/remaster_iso_functions.sh
else
    source remaster_iso_functions.sh    # current dir
fi

# Needs root privileges (to mount)
exit_if_not_root

SQUASHFS_PATH=casper/filesystem.squashfs
MANIFEST_PATH=casper/filesystem.manifest
SIZE_FILE=casper/filesystem.size
EFI_IMG_FILE=boot/grub/efi.img

# Check cmdline args
function show_usage() {
    echo "${PROG_NAME} ISO_PATH EXTRACT_DIR OUTPUT_ISO"
    echo ""
    echo "    ISO_PATH:      Full path to ISO to extract"
    echo "    EXTRACT_DIR:  Dir to extract under. Will be (re-)created"
    echo "    OUTPUT_ISO: Full path to output ISO"
}

if [ -z "$3" ]; then
    show_usage
    exit 1
fi

if [ -z "$REMASTER_CMDS_DIR" ]; then
    REMASTER_CMDS_DIR=${PROG_DIR}/../remaster
fi
if [ -d $REMASTER_CMDS_DIR ]; then
    REMASTER_CMDS_DIR=$(readlink -e $REMASTER_CMDS_DIR)
else
    echo "REMASTER_CMDS_DIR not a directory: $REMASTER_CMDS_DIR"
    echo "Ignoring REMASTER_CMDS_DIR"
    REMASTER_CMDS_DIR=""
fi

ISO_PATH="$1"
EXTRACT_DIR="$2"
OUTPUT_ISO="$3"

extract_iso "$ISO_PATH" "$EXTRACT_DIR" || exit 1
extract_squashfs "$EXTRACT_DIR" "${ISO_EXTRACT_SUBDIR}"/"$SQUASHFS_PATH" || exit 1

if [ -n "$REMASTER_CMDS_DIR" ]; then
    run_remaster_commands "$EXTRACT_DIR" "${REMASTER_CMDS_DIR}"
else
    echo "No REMASTER_CMDS_DIR. Not running any remaster commands"
fi

update_squashfs "$EXTRACT_DIR" "$SQUASHFS_PATH" "${MANIFEST_PATH}" "${SIZE_FILE}"
update_iso "$EXTRACT_DIR" "${OUTPUT_ISO}" "$ISO_PATH" "$EFI_IMG_FILE" 
rmdir "$EXTRACT_DIR"
