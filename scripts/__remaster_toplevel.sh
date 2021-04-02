#!/bin/bash

# Executes all executable files in directory 'commands' in the same
# directory as this script in lexicographic order
#
# If 'commands' directory contains a file named 'commands.list', then
# that file is expected to contain filenames within 'commands' dir
# to be executed. In that case, ONLY files in commands.list that
# are executable are executed in the order they appear in 
# commands.list
#
# commands.list is NEVER executed, even if present and executable
#
# TODOs
#   1. IGNORE user command filenames that start with underscore
#   2. Create __remaster_toplevel_functions.sh with common functions
#      Export functions using 'export -f <fn_name>'
#      See: https://unix.stackexchange.com/a/22867
#   3. Copy __remaster_toplevel_functions.sh to same dir as
#      __remaster_toplevel.sh in run_remaster_commands function
#      in __remaster_toplevel_functions.sh
#
#   4. Use common functions in user scripts:
#       a. initialize
#          Setup /etc/resolv.conf and create /etc/resolv.conf.remaster_orig
#       b. check_pkg_integrity
#       c. install_if_missing
#          Install list of packages permanently in chroot
#          use check_pkg_integrity  
#       d. install_pkgs_temporary
#          Install list of packages, but mark them to be removed
#          at the end of chroot commands
#          use check_pkg_integrity  
#       e. run_cmd_if_available
#       f. run_cmd_or_exit
#          Exits from script if command is UNAVAILABLE
#       g. run_cmd_or_fail
#          Exits remastering processif command is UNAVAILABLE
#       h. require_dir_or_exit
#       i. require_file_or_exit
#       j. require_dir_or_fail
#       k. require_file_or_fail

#   5. Create new automatic (non-user) commands
#       a. __apt_update
#          run apt-update - need to do only once in chroot
#       b. __remove_temporary_packages - at the end of chroot commands
#   6. Change __remaster_toplevel.sh to:
#       a. Run __apt_update BEFORE any user commands
#       b. Run __remove_temporary_packages AFTER ALL user commands
#   7. Change user commands
#       a. Add xx_install_packages - at the start - use install_if_missing


PROG_PATH=${PROG_PATH:-$(readlink -e $0)}
PROG_DIR=${PROG_DIR:-$(dirname ${PROG_PATH})}
PROG_NAME=${PROG_NAME:-$(basename ${PROG_PATH})}
FAILED_EXIT_CODE=127

if [ -n "$REMASTER_STAGE" ]; then
    STAGE="[$REMASTER_STAGE]"
else
    STAGE=""
fi

COMMANDS_DIR=${PROG_DIR}/commands
if [ ! -d $COMMANDS_DIR ]; then
    echo "${PROG_NAME}: Not a directory: $COMMANDS_DIR ${STAGE}"
    exit 0
fi
COMMANDS_DIR=$(readlink -e $COMMANDS_DIR)

if [ -f ${COMMANDS_DIR}/commands.list ]; then
    CMD_LIST=$(cat ${COMMANDS_DIR}/command.list)
    if [ -z "$CMD_LIST" ]; then 
        echo "${PROG_NAME}: Empty commands.list. Ignoring commands in COMMANDS_DIR ${STAGE}"
        exit 0
    fi
    echo "${PROG_NAME}: Only running specified commands in commands.list ${STAGE}"
else
    CMD_LIST=$(ls ${COMMANDS_DIR})
    if [ -z "$CMD_LIST" ]; then
        echo "${PROG_NAME}: No commands found: ${STAGE}"
        exit 0
    fi
fi

for f in $CMD_LIST
do
    f=$(basename $f)    # In case commands.list contained paths
    if [ "$f" = "commands.list" ]; then
        continue
    fi
    CMD=${COMMANDS_DIR}/$f

    if [ ! -x ${CMD} ]; then
        echo "$(basename ${CMD}) ${STAGE}: Ignoring non-executable file"
        continue
    fi
    echo "$(basename $CMD) ${STAGE}: Starting"
    $CMD 2>&1 | sed -u -e 's/^/    /'
    # Special case if return code is $FAILED_EXIT_CODE, bail out of remaster
    ret=$?
    if [ $ret -eq $FAILED_EXIT_CODE ]; then
        echo "$(basename $CMD) ${STAGE}: Failed - exiting remaster script"
        exit 1
    elif [ $ret -ne 0 ]; then
        echo "$(basename $CMD) ${STAGE}: Non-zero return code"
    fi
    echo "$(basename $CMD) ${STAGE}: Completed"
done
