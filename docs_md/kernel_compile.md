# Download, patch and compile the kernel

# Packages required
The following list is for ubuntu. It should be very similar or identical on
Ubuntu flavours like Mint and very similar on other Debian distributions

```
sudo apt-get install git build-essential kernel-package fakeroot libncurses5-dev libssl-dev ccache libfile-fcntllock-perl
```

Copy and paste the script below and save it as ane executable shell script
in the directory where you wish to compile the kernel and build the DEB
packages.

Also place the file named ```kernel_config``` in the same directory
Edit the first few lines to set 

  - LINUX_NEXT_COMMIT
  - CONFIG_FILE
  - PATCH_FILE


## Script
```bash
#!/bin/bash
LINUX_NEXT_COMMIT=db55616926f9e4826d266795f17512c77fe1bc8c
# Path to config file relative to dir with this script
CONFIG_FILE=./config.4.12
# Patch file path relative to dir with this script
PATCH_FILE=./0001_linux-next-rdp_bluetooth.patch
IMAGE_NAME=bzImage      # Typically uImage on ARM

#-------------------------------------------------------------------------
# Probably don't have to change anything below this
#-------------------------------------------------------------------------

CURDIR=$(readlink -f $PWD)
START_END_TIME_FILE=$CURDIR/start_end.time
if [ -z "$NUM_THREADS" ]; then
    NUM_THREADS=$(lscpu | grep '^CPU(s)' | awk '{print $2}')
fi
echo "Using NUMTHREADS=$NUM_THREADS"
MAKE_THREADED="make -j$NUM_THREADS"

date > $START_END_TIME_FILE

if [ -z "$BUILD_DIR" ]; then
    BUILD_DIR=${CURDIR}/linux-next-${LINUX_NEXT_COMMIT}
    echo "Setting BUILD_DIR from LINUX_NEXT_COMMIT: $BUILD_DIR"
    if [ ! -d "$BUILD_DIR" ]; then
        wget -O - -nd "https://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next.git/snapshot/linux-next-${LINUX_NEXT_COMMIT}.tar.gz" | tar zxf -
    fi

    # Only apply patch once immediately after downloading
    if [ -n "$PATCH_FILE" ]; then
        if [ -f ${CURDIR}/${PATCH_FILE} ]; then
            cd ${BUILD_DIR}
            patch -p1 < ${CURDIR}/${PATCH_FILE}
            if [ $? -ne 0 ]; then
                echo "Patch failed"
                exit 1
            fi
        fi
    fi
fi
if [ ! -d "$BUILD_DIR" ]; then
    echo "Directory not found: BUILD_DIR: $BUILD_DIR"
    exit 1
fi

cd $BUILD_DIR
if [ ! -f .config ]; then
    if [ -f ${CURDIR}/${CONFIG_FILE} ]; then
        cp ${CURDIR}/${CONFIG_FILE} .config
        echo "Restored config"
    else
        echo ".config not found: ${CONFIG_FILE}"
        exit 1
    fi
fi


$MAKE_THREADED silentoldconfig

$MAKE_THREADED $IMAGE_NAME
$MAKE_THREADED bindeb-pkg

date >> $START_END_TIME_FILE
cat $START_END_TIME_FILE
```
