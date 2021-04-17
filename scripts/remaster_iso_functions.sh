#!/bin/bash

# ------------------------------------------------------------------------
# CREDITS:
#
# Originally from linuxium-install-xenial-lts-kernel-4.10.0-10.12-16.04.2-linuxium.sh
# by Ian Morrison (https://www.blogger.com/profile/16579769072594848618)
# Posted at https://linuxiumcomau.blogspot.com.au/2017/03/ubuntu-16042-and-ubuntu-1704-beta-1.html
# and hosted at https://goo.gl/pyGirj or
# https://drive.google.com/file/d/0B99O3A0dDe67R0MxMVZVN2NSVTQ/edit
#
# Extracts an ISO into a directory
#
# Usage:
#   extract_iso.sh ISO_PATH EXTRACT_DIR SQUASHFS_PATH
#       ISO_PATH:      Full path to ISO to extract
#       EXTRACT_DIR:   Dir to extract under. Will be created if required
#       SQUASHFS_PATH: RELATIVE PATH of squashfs file within ISO
# ------------------------------------------------------------------------
if [ -n "$BASH_SOURCE" ]; then
    PROG_PATH=${PROG_PATH:-$(readlink -e $BASH_SOURCE)}
else
    PROG_PATH=${PROG_PATH:-$(readlink -e $0)}
fi
PROG_DIR=${PROG_DIR:-$(dirname ${PROG_PATH})}
PROG_NAME=${PROG_NAME:-$(basename ${PROG_PATH})}

ISO_EXTRACT_SUBDIR=iso-directory-structure
SQUASHFS_EXTRACT_SUBDIR=iso-chroot
REMASTER_DIR=remaster
ISO_PRE_CMD_DIR=iso_pre
CHROOT_CMD_DIR=chroot
ISO_POST_CMD_DIR=iso_post
TOP_CMD=toplevel.sh
TMP_REMASTER_DIR=remaster_tmp


function exit_if_not_root {
    if [ $(id -u) -ne 0 ]; then
        echo "Need to be root"
        exit 1
    fi
}

function get_vol_id {
    # $1: ISO_PATH:      Full path to ISO
    # Outputs VOLID
    ISO_VOLID=$(isoinfo -d -i "${ISO_PATH}" | grep '^Volume id:') && ISO_VOLID=${ISO_VOLID##Volume id: }
    echo "$ISO_VOLID"
}

function check_ubuntu_iso {
    # $1: ISO_PATH:      Full path to ISO to extract
    # Exits if it is not a supported ISO
    # This function checks for an Ubuntu-flavour ISO

    ISO=$(readlink -f ${1})
    [ ! -f ${ISO} ] && echo "Cannot find '${ISO}' ... exiting." && exit
    ISO_TYPE=$(file -b ${ISO})
    if [ "${ISO_TYPE:0:28}" != "DOS/MBR boot sector ISO 9660" ]; then
        echo "$0: File must be a bootable ISO ... exiting."
        exit
    fi
    ISO_DISTRO=$(isoinfo -i ${ISO} -x /.DISK/RELEASE_NOTES_URL.\;1) && ISO_DISTRO=${ISO_DISTRO%%.com/getubuntu*} && ISO_DISTRO=${ISO_DISTRO##http://www.}
    if [ "${ISO_DISTRO}" != "ubuntu" ]; then
        echo "$0: ISO must be Ubuntu (or Ubuntu flavour) ... exiting."
        exit
    else
        echo "It is an Ubuntu flavour (OK)"
    fi
}

function extract_iso {
    # $1: ISO_PATH:      Full path to ISO to extract
    # $2: EXTRACT_DIR:   Dir to extract under. Will be created if required

    local local_iso=$(readlink -e "$1")
    local local_extract_dir="$2"
    if [ ! -f "${local_iso}" ]; then
        echo "${PROGNAME}: ISO_PATH not found: ${local_iso}"
        return 1
    fi
    if [ -f "${local_extract_dir}" ]; then
        echo "${PROGNAME}: EXTRACT_DIR is a file: ${local_extract_dir}"
        return 1
    fi

    echo "(extract_iso): Extracting ISO ... $(basename $local_iso)"
    sudo rm -rf "$local_extract_dir"
    sudo mkdir "$local_extract_dir"
    local old_dir=$(pwd)
    cd "$local_extract_dir"

    # mount iso
    MOUNT_DIR=$(mktemp -d "${PROG_NAME}_tmp_XXXXXXXX")
    sudo mount -o loop "$local_iso" "${MOUNT_DIR}" 1>/dev/null 2>&1

    # extract iso directory structure from iso
    sudo rm -rf "${ISO_EXTRACT_SUBDIR}"
    sudo rsync -a "${MOUNT_DIR}"/ "${ISO_EXTRACT_SUBDIR}"

    # unmount iso
    sudo umount "${MOUNT_DIR}"
    sudo rmdir "${MOUNT_DIR}"

    cd $old_dir
    echo "(extract_iso): Completed"
    return 0
}

function extract_squashfs {
    # $1: ISO_EXTRACT_DIR: Dir containing extracted ISO
    # $2: SQUASHFS_PATH:   RELATIVE PATH of squashfs file within ISO
    # For Ubuntu SQUASHFS_PATH is /casper/filesystem.squashfs

    local local_extract_dir="$1"
    local local_squash_file="$2"
    if [ ! -d "$local_extract_dir" ]; then
        echo "${PROG_NAME} (extract_squashfs): ISO_EXTRACT_DIR not a directory: $local_extract_dir"
        return 1
    fi

    local old_dir=$(pwd)
    cd "$local_extract_dir"
    
    if [ ! -f ${local_squash_file} ]; then
        cd $old_dir
        echo "${PROG_NAME} (extract_squashfs): SQUASHFS_PATH not found: ${local_squash_file}"
        return 1
    fi
    echo "(extract_squashfs): Extracting squashfs <-- $(basename $local_squash_file)"
    sudo rm -rf squashfs-root "${SQUASHFS_EXTRACT_SUBDIR}"
    sudo unsquashfs ${local_squash_file} 1>/dev/null 2>&1
    sudo mv squashfs-root "${SQUASHFS_EXTRACT_SUBDIR}"

    cd $old_dir
    echo "(extract_squashfs): Completed"
    return 0
}

function run_remaster_commands {
    # $1: ISO_EXTRACT_DIR: Dir containing extracted ISO
    # $2: REMASTER_CMDS_DIR: Dir containing iso_pre, chroot, iso_post

    local local_extract_dir=$(readlink -e "$1")
    local local_iso_dir=${local_extract_dir}/"${ISO_EXTRACT_SUBDIR}"
    local local_chroot_dir=${local_extract_dir}/"${SQUASHFS_EXTRACT_SUBDIR}"
    local local_remaster_cmds_dir=$(readlink -e $2)
    local local_remaster_log="${local_iso_dir}"/${REMASTER_DIR}/remaster.log

    # Setup remaster log
    sudo mkdir -p "${local_iso_dir}"/${REMASTER_DIR}
    # Let iso_pre and iso_post scripts know where chroot is
    export REMASTER_ISO_CHROOT_DIR=$local_chroot_dir

    # iso_pre
    REMASTER_STAGE=${ISO_PRE_CMD_DIR}
    local local_src_dir=${local_remaster_cmds_dir}/${REMASTER_STAGE}
    sudo \cp -af ${local_src_dir} $local_iso_dir/${TMP_REMASTER_DIR}
    \cp -f ${PROG_DIR}/__remaster_toplevel.sh $local_iso_dir/${TMP_REMASTER_DIR}/${TOP_CMD}
    REMASTER_STAGE=$REMASTER_STAGE $local_iso_dir/${TMP_REMASTER_DIR}/${TOP_CMD} 2>&1 | tee -a $local_remaster_log

    # chroot
    REMASTER_STAGE=${CHROOT_CMD_DIR}
    local_src_dir=${local_remaster_cmds_dir}/${REMASTER_STAGE}
    sudo \cp -af ${local_src_dir} $local_chroot_dir/${TMP_REMASTER_DIR}
    \cp -f ${PROG_DIR}/__remaster_toplevel.sh $local_chroot_dir/${TMP_REMASTER_DIR}/${TOP_CMD}

    # bind mounts for chroot
    for d in dev run
    do
        mount --bind /$d $local_chroot_dir/$d
    done
    mount -t proc none $local_chroot_dir/proc
    mount -t sysfs none $local_chroot_dir/sys
    mount -t devpts none $local_chroot_dir/dev/pts

    sudo REMASTER_STAGE=$REMASTER_STAGE chroot $local_chroot_dir /${TMP_REMASTER_DIR}/${TOP_CMD} 2>&1 | tee -a $local_remaster_log

    # unmount chroot bind mounts
    for d in proc sys dev/pts dev run
    do
        umount $local_chroot_dir/$d || umount -lf $local_chroot_dir/$d
    done

    \rm -rf $local_chroot_dir/${TMP_REMASTER_DIR}

    # iso_post
    REMASTER_STAGE=${ISO_POST_CMD_DIR}
    # Remove iso_pre commands!
    if [ -d $local_iso_dir/${TMP_REMASTER_DIR}/commands ]; then
        \rm -rf $local_iso_dir/${TMP_REMASTER_DIR}/commands
    fi
    local_src_dir=${local_remaster_cmds_dir}/${REMASTER_STAGE}
    sudo \cp -af ${local_src_dir}/. $local_iso_dir/${TMP_REMASTER_DIR}/.
    \cp -f ${PROG_DIR}/__remaster_toplevel.sh $local_iso_dir/${TMP_REMASTER_DIR}/${TOP_CMD}
    REMASTER_STAGE=$REMASTER_STAGE $local_iso_dir/${TMP_REMASTER_DIR}/${TOP_CMD} 2>&1 | tee -a $local_remaster_log
    \rm -rf $local_iso_dir/${TMP_REMASTER_DIR}

    # copy log to /root/remaster
    mkdir -p $local_chroot_dir/root/remaster
    \cp -f $local_remaster_log $local_chroot_dir/root/remaster/
    \cp -f $local_remaster_log /tmp/

    echo "(run_remaster_commands): Completed"
    return 0
}

function update_squashfs {
    # $1: ISO_EXTRACT_DIR: Dir containing extracted ISO
    # $2: SQUASHFS_PATH:   RELATIVE PATH of squashfs file within ISO
    # $3: MANIFEST_PATH:   RELATIVE PATH of manifest file within ISO
    # $4: SIZE_FILE:       RELATIVE_PATH of filesystem.size within ISO
    # For ubuntu flavours:
    #   SQUASHFS_PATH=casper/filesystem.squashfs
    #   MANIFEST_PATH=casper/filesystem.manifest
    #   SIZE_FILE=casper/filesystem.size

    local local_extract_dir=$(readlink -e "$1")
    local local_iso_dir=${local_extract_dir}/"${ISO_EXTRACT_SUBDIR}"
    local local_chroot_dir=${local_extract_dir}/"${SQUASHFS_EXTRACT_SUBDIR}"
    local local_squash_file="$local_iso_dir/$2"
    local local_manifest_path="$local_iso_dir/$3"
    local local_size_file="$local_iso_dir/$4"

    local old_dir=$(pwd)
    cd "$local_extract_dir"

    # create the manifest
    sudo chmod +w $local_manifest_path
    sudo chroot "${local_chroot_dir}" dpkg-query -W --showformat='${Package} ${Version}\n' | sudo tee $local_manifest_path > /dev/null

    # create the filesystem
    echo "(update_squashfs): Creating squashfs --> $(basename $local_squash_file)"
    sudo mksquashfs $local_chroot_dir $local_squash_file -noappend 1>/dev/null 2>&1
    printf $(sudo du -sx --block-size=1 iso-chroot | cut -f1) | sudo tee $local_size_file > /dev/null
    cd $local_iso_dir

    sudo rm -f md5sum.txt
    find -type f -print0 | sudo xargs -0 md5sum | grep -v isolinux/boot.cat | sudo tee md5sum.txt > /dev/null

    sudo rm -rf $local_chroot_dir
    cd $old_dir

    echo "(update_squashfs): Completed"
    return 0
}


function update_iso {
    # $1: ISO_EXTRACT_DIR: Dir containing extracted ISO
    # $2: OUTPUT_ISO:      Full path to output ISO - will be created / overwritten
    # $3: OLD_ISO_PATH:    Full path to ORIGINAL ISO to extract isohdpfx.bin and VOLID
    # $4: EFI_IMG_FILE:    Relative path to efi.img under ISO_EXTRACT_SUBDIR
    #
    # See: https://askubuntu.com/q/1289400
    # See: https://wiki.debian.org/RepackBootableISO#What_to_do_if_no_file_.2F.disk.2Fmkisofs_exists

    [[ $# -lt 4 ]] && return 1
    local extract_dir=$(readlink -e "$1")
    local output_iso=$(readlink -f "$2")
    local input_iso=$(readlink -e "$3")
    local img_extract_dir=$(mktemp -d -p /tmp)
    local volid=$(get_vol_id "${input_iso}")

    extract_dir=${extract_dir}/"${ISO_EXTRACT_SUBDIR}"
    # check params here

    local mbr_image="${img_extract_dir}/mbr_image"
    local isohdpfx="${img_extract_dir}/isohdpfx.bin"
    local boot_image=""
    local catalog=""
    local efi_image="${img_extract_dir}/efi_image"

    sudo -n rm -f "$mbr_image" "$efi_image" "$boot_image" "$catalog" "$isohdpfx"

    # Update remaster.time
    sudo -n mkdir -p "${extract_dir}"/${REMASTER_DIR}
    sudo -n echo "$(date '+%Y-%m-%d-%H%M%S')" > "${extract_dir}"/${REMASTER_DIR}/remaster.time
    sudo -n echo "Remastered from $(basename $input_iso)" > "${extract_dir}"/${REMASTER_DIR}/remaster.txt


    # Groovy (onwards), Ubuntu has moved away from isolinux
    # and has EFI as a separate PARTITION on the ISO

    local EFI_ISO=no
    fdisk -l "$input_iso" | grep -q 'EFI System$' && EFI_ISO=yes

    if [[ "$EFI_ISO" = "yes" ]]; then
        # GPT ISO with EFI partition
        boot_image="/boot/grub/i386-pc/eltorito.img"
        catalog="/boot.catalog"
        # MBR image
        sudo -n dd if="$input_iso" bs=1 count=446 of="$mbr_image" 1>/dev/null 2>&1
        # EFI image
        # local skip=$(/sbin/fdisk -l "$input_iso" | fgrep '.iso2 ' | awk '{print $2}')
        # local size=$(/sbin/fdisk -l "$input_iso" | fgrep '.iso2 ' | awk '{print $4}')
        # sudo -n dd if="$input_iso" bs=512 skip="$skip" count="$size" of="$efi_image" 1>/dev/null 2>&1
        rm -f "$efi_image"
        mv "$extract_dir"/boot/grub/efi.img "$efi_image"
    else
        boot_image="/isolinux/isolinux.bin"
        catalog="/isolinux/boot.cat"
        # isohdpfx - first 432 bytes of input_iso
        sudo -n dd if="$input_iso" bs=1 count=432 of="$isohdpfx" 1>/dev/null 2>&1

        # EFI image
        cp "$extract_dir"/boot/grub/efi.img "$efi_image"
        # efi_image="/boot/grub/efi.img"
    fi

    # TRY ALWAYS creating ISO with separate EFI partition
    EFI_ISO=yes

    if [[ "$EFI_ISO" = "yes" ]]; then
        sudo -n xorriso -as mkisofs \
            -quiet \
            -r -J -joliet-long -l -iso-level 3 -full-iso9660-filenames \
            -partition_offset 16 \
            --grub2-mbr "$mbr_image" \
            --mbr-force-bootable \
            -append_partition 2 0xEF "$efi_image" \
            -appended_part_as_gpt \
            -c "$catalog" \
            -b "$boot_image" -no-emul-boot -boot-load-size 4 -boot-info-table --grub2-boot-info \
            -eltorito-alt-boot -e '--interval:appended_partition_2:all::' -no-emul-boot \
            -volid "${volid}" \
            -o "$output_iso" \
            "$extract_dir" 1>/dev/null 2>&1
    else
        sudo -n xorriso -as mkisofs \
            -quiet \
            -r -J -joliet-long -iso-level 3 -full-iso9660-filenames \
            -volid "${volid}" \
            -isohybrid-mbr "$isohdpfx" \
            -c "$catalog" \
            -b "$boot_image" -no-emul-boot -boot-load-size 4 -boot-info-table \
            -eltorito-alt-boot -e "$efi_image" -no-emul-boot \
            -isohybrid-gpt-basdat \
            -o "${output_iso}" \
            "$extract_dir"
    fi
    local xorriso_ret=$?
    sudo rm -rf "$img_extract_dir"
    sudo rm -rf "${extract_dir}"
    if [ $xorriso_ret -ne 0 ]; then
        echo "xorriso failed"
    fi
    if [ $xorriso_ret -eq 0 ]; then
        local out_volid=$(get_vol_id "${output_iso}")

        echo ""
        echo "--------------------------------------------------------------------------"
        echo "Source ISO=$input_iso"
        echo "Output ISO=$output_iso"
        echo "Source VolID=$volid"
        echo "Output VolID=$out_volid"
        echo ""
        echo "--------------------------------------------------------------------------"
        echo ""
    fi
    echo "(update_iso): Completed"
    return $xorriso_ret
}
