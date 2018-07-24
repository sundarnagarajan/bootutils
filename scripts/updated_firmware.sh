#!/bin/bash
#
# Run without any options or with -h | --help to see usage
# MUST set If environment variable FIRMWARE_GIT_DIR - directory to compare
# with /lib/firmware



function show_help()
{
    PROG_NAME=$(basename $0)
    echo "Lists firmware files that are new or have been updated under FIRMWARE_GIT_DIR"
    echo "as compared to /lib/firmware"
    echo ""
    echo "MUST set FIRMWARE_GIT_DIR - directory to compare with /lib/firmware"
    echo ""
    echo "Usage $PROG_NAME [-h | --help | -n | --new | -u | --updated"
    echo "Options:"
    echo "   -h | --help : show usage and exit"
    echo "   -n | --new : Show new firmware files"
    echo "   -u | --updated : Show updated firmware files"
}

if [ -z "$1" ]; then
    show_help
    exit 0
fi

if [ -z "$FIRMWARE_GIT_DIR" ]; then
    echo "Must set FIRMWARE_GIT_DIR"
    exit 1
fi
if [ ! -d "$FIRMWARE_GIT_DIR" ]; then
    echo "FIRMWARE_GIT_DIR not a directory: $FIRMWARE_GIT_DIR"
    exit 2
fi


case "$1" in
    -h|--help)
        show_help
        ;;
    -u|--updated)
        diff -q -r /lib/firmware $FIRMWARE_GIT_DIR | perl -wnl -e '/^Files \/lib\/firmware\/(\S+) and .*? differ$/ and print $1' | egrep -v '^(.git|WHENCE|Makefile|README|copyright|check_whence.py|LICEN[SC]E.*$)'
        ;;
    -n|--new)
        ESCAPED_DIR=$(echo $FIRMWARE_GIT_DIR | sed -e 's/\//\\\//g')
        diff -q -r /lib/firmware $FIRMWARE_GIT_DIR | egrep "^Only in $FIRMWARE_GIT_DIR" | sed -e 's/^Only in //' -e 's/: /\//' -e "s/^${ESCAPED_DIR}\///" | egrep -v '^(.git|WHENCE|Makefile|README|copyright|check_whence.py|LICEN[SC]E.*$)'
        ;;
    "")
        show_help
        ;;
    *)
        echo "Invalid option: $1"
        show_help
        exit 1
        ;;
esac

