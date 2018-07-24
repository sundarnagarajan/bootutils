#!/bin/bash
#
# Run without any options or with -h | --help to see usage
# If environment variable FIRMWARE_DIR is set, it uses that dir to look for
# firmware - defaults to /lib/firmware

FIRMWARE_DIR=${FIRMWARE_DIR:-/lib/firmware}
MODULE_DIR=/lib/modules/`uname -r`


function show_help()
{
    PROG_NAME=$(basename $0)
    echo "Shows firmware files required but missing under /lib/firmware"
    echo ""
    echo "set FIRMWARE_DIR environment variable to check against a directory other than"
    echo "/lib/firmware - e.g. latest linux-firmware-git clone"
    echo ""
    echo "Usage $PROG_NAME [-h | --help | -m | -l | -a]"
    echo "Options:"
    echo "   -h | --help : show usage and exit"
    echo ""
    echo "   -m | --missing : Show only firmware reported as missing by running kernel"
    echo "        Information comes from dmesg"
    echo ""
    echo "   -l | --loaded : Show all firmware missing based on currently loaded modules"
    echo "        (including builtins)"
    echo "        This means firmware files LISTED by the modules that are currently loaded"
    echo "        and does not necessarily mean that the module has LOADED those"
    echo "        firmware files. Large modules like amdgpu will list MANY firmware files,"
    echo "        but will only load based on hardware detected, etc."
    echo ""
    echo "   -a | --all : Show all firmware that _MAY_ be missing based on modules"
    echo "        under /lib/modules/kernel_version"
    echo "        Lists a LOT of firmware files:"
    echo "            - Many relate to modules not loaded (may never be needed)"
    echo "            - Many of these are not available under linux-firmware-git also!"
    echo "            - These may be non-free firmware"
}

function check_fw()
{
    # Reads STDIN - each line should be firmware path under FIRMWARE_DIR
    while read fw
    do
        if [ ! -f $FIRMWARE_DIR/$fw ]; then
            echo $fw
        fi
    done
}

function fw_loaded_modules()
{
    for m in /sys/module/*
    do 
        modinfo $(basename $(basename $m)) 2>/dev/null | perl -wnl -e '/^firmware: \s+ (\S+)/ and print $1'
    done
}

function module_list()
{
    (cat $MODULE_DIR/modules.builtin; cut -d: -f1 < $MODULE_DIR/modules.dep) | sort | uniq
}


function fw_kernel_all()
{
    module_list | while read mod_file
    do 
        modinfo $MODULE_DIR/$mod_file 2>/dev/null | perl -wnl -e '/^firmware: \s+ (\S+)/ and print $1'
    done
}

function fw_kernel_missing()
{
    dmesg | perl -wnl -e '/Direct firmware load for (\S+) failed/ and print $1'
}



case "$1" in
    -h|--help)
        show_help
        ;;
    -l|--loaded)
        fw_loaded_modules | check_fw
        ;;
    -a|--all)
        fw_kernel_all | check_fw
        ;;
    -m|--missing)
        fw_kernel_missing | check_fw
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

