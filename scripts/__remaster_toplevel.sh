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

PROG_PATH=${PROG_PATH:-$(readlink -e $0)}
PROG_DIR=${PROG_DIR:-$(dirname ${PROG_PATH})}
PROG_NAME=${PROG_NAME:-$(basename ${PROG_PATH})}

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
    # Special case if return code is 255, bail out of remaster
    ret=$?
    if [ $ret -eq 255 ]; then
        echo "$(basename $CMD) ${STAGE}: Failed - exiting remaster script"
        exit 1
    elif [ $ret -ne 0 ]; then
        echo "$(basename $CMD) ${STAGE}: Non-zero return code"
    fi
    echo "$(basename $CMD) ${STAGE}: Completed"
done
