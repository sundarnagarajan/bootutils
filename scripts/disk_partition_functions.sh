#!/bin/bash
#BASHDOC
# ------------------------------------------------------------------------
# Packages required: 
#   util-linux (lsblk, findmnt) - part of base
#   gawk (awk)
# ------------------------------------------------------------------------
#BASHDOC

# ------------------------------------------------------------------------
# Following functions use only lsblk - no root required
# ------------------------------------------------------------------------

function show_disks() {
    # Shows details of all disks
    lsblk -d -e 7,1 -o NAME,SIZE,MODEL,SERIAL,WWN  | sed -e '1s/^NAME/NAME     /' -e '2,$s/^/\/dev\//'
}

function show_disk_partitions() {
    # $1: disk device - can be /dev/dev_name (e.g. /dev/sda) or just dev_name (sda)
    [[ $# -lt 1 ]] && return 1
    local d=$1
    [[ $d =~ ^/dev/ ]] || d="/dev/$d"
    [[ ! -b "$d" ]] && {
        >&2 echo "Not a disk: $d"
        return 2
    }
    local d_short=$d
    [[ $d_short =~ ^/dev/ ]] && d_short=$(echo $d | sed -e 's/^\/dev\///')
    local p_list=$(cat /proc/partitions | grep -P " $d_short\S+\$" | awk '{print "/dev/"$4}')
    [[ -z "$p_list" ]] && {
        >&2 echo "Disk has no partitions: $d"
        return
    }
    lsblk -d -o NAME,SIZE,FSTYPE,LABEL,PARTLABEL,MOUNTPOINT $p_list | sed -e '1s/^NAME/NAME     /' -e '2,$s/^/\/dev\//'
}

function show_all_disk_partitions() {
    # Shows details of all disk partitions
    local p_list_all=""
    for d in $(show_disks | sed -e '1d' | awk '{print $1}')
    do
        local d_short=$d
        [[ $d_short =~ ^/dev/ ]] && d_short=$(echo $d | sed -e 's/^\/dev\///')
        local p_list=$(cat /proc/partitions | grep -P " $d_short\S+\$" | awk '{print "/dev/"$4}')
        [[ -n "$p_list" ]] && p_list_all="$p_list_all $p_list"
    done
    lsblk -d -o NAME,SIZE,FSTYPE,LABEL,PARTLABEL,MOUNTPOINT $p_list_all | sed -e '1s/^NAME/NAME     /' -e '2,$s/^/\/dev\//'
}

function valid_disk() {
    # $1: disk device - can be /dev/dev_name (e.g. /dev/sda) or just dev_name (sda)
    # Returns: 0: if it is a valid disk (returned by show_disks); 1 otherwise
    [[ $# -lt 1 ]] && return 1
    local d=$1
    [[ $d =~ ^/dev/ ]] || d="/dev/$d"
    [[ ! -b "$d" ]] && {
        return 1
    }
    show_disks | sed -e '1d' | grep -qP "^${d}\s+"
}

function valid_partition() {
    # $1: partition device - can be /dev/partition_name (e.g. /dev/sda1) or just partition_name (sda1)
    # Returns: 0: if it is a valid partition (returned by show_all_disk_partitions); 1 otherwise
    [[ $# -lt 1 ]] && return 1
    local d=$1
    [[ $d =~ ^/dev/ ]] || d="/dev/$d"
    [[ ! -b "$d" ]] && {
        return 1
    }
    show_all_disk_partitions | sed -e '1d' | grep -qP "^${d}\s+"
}

function choose_disk(){
    # Prints available disks, allows user to choose a disk, prints chosen
    # disk device to stdout
    # User can enter disk device as /dev/dev_name (e.g. /dev/sda) or just dev_name (sda)
    local ret=""
    show_disks
    echo""
    while [[ -z "$ret" ]];
    do
        read -p "Choose disk: " d
        [[ $d =~ ^/dev/ ]] || d="/dev/$d"
        valid_disk "$d" || continue
        ret=$d
        break
    done
    echo "$ret"
}

function choose_partition(){
    # Prints available partitions, allows user to choose a partition, prints chosen
    # partition device to stdout
    # User can enter partition device as /dev/dev_name (e.g. /dev/sda1) or just dev_name (sda1)
    local ret=""
    show_disks
    echo ""
    show_all_disk_partitions
    echo""
    while [[ -z "$ret" ]];
    do
        read -p "Choose partition: " d
        [[ $d =~ ^/dev/ ]] || d="/dev/$d"
        valid_partition "$d" || continue
        ret=$d
        break
    done
    echo "$ret"
}

function partition_devices() {
    # Like show_all_disk_partitions, but only outputs device name
    show_all_disk_partitions | sed -e '1d' | awk '{print $1}'
}

function vfat_partition_devices() {
    # Like partition_devices butonly shows VFAT partitions
    show_all_disk_partitions | sed -e '1d' | awk '$3=="vfat" {print $1}'
}

# ------------------------------------------------------------------------
# Following functions use findmnt and may need to mount - need root
# ------------------------------------------------------------------------

function valid_efi_partition() {
    # $1: partition device - can be /dev/partition_name (e.g. /dev/sda1) or just partition_name (sda1)
    # Returns:
    #   0: if it is a valid ESP (EFI System partition)
    #   1: not a valid ESP (EFI System Partition)
    #   2: not running as root
    [[ $# -lt 1 ]] && return 1
    local d=$1
    [[ $d =~ ^/dev/ ]] || d="/dev/$d"
    [[ ! -b "$d" ]] && {
        return 1
    }
    vfat_partition_devices | fgrep -qx $d || return 1

    # Rest needs root
    [[ $(id -u) -ne 0 ]] && return 2

    local mounted=no
    local mountpoint=$(findmnt -n -o TARGET $d || true)
    [[ -n "$mountpoint" ]] && mounted=yes
    if [[ "$mounted" = "no" ]]; then
        mountpoint=$(mktemp -d "/tmp/valid_efi_partition.XXXXXX")
        mount $d $mountpoint || { rmdir $mountpoint; return 1; }
    fi

    local ret=0
    [[ -d "$mountpoint"/EFI/BOOT ]] || ret=1
    if [[ "$mounted" = "no" ]]; then
        findmnt -n -o SOURCE --mountpoint "$mountpoint" 1>/dev/null 2>&1  && umount -l "$mountpoint" 2>/dev/null
        rmdir $mountpoint
        [[ -d "$mountpoint" ]] && >&2 echo "Removing failed: $mountpoint"
    fi
    return $ret
}

function show_efi_partitions(){
    # Outputs list of valid ESP (EFI System Partitions)
    # Returns 2: if not running as root
    [[ $(id -u) -ne 0 ]] && return 2
    local p_out=$(show_all_disk_partitions)
    local heading=$(echo "$p_out" | head -1)
    local list=$(echo "$p_out" | sed -e '1d')
    local efi_out=""

    while read line
    do
        local p=$(echo "$line" | awk '{print $1}')
        valid_efi_partition "$p" || continue
        [[ -n "$efi_out" ]] && {
            line="\n${line}"
        }
        efi_out="${efi_out}${line}"
    done <<< $list
    if [[ -n "$efi_out" ]]; then
        echo -e "$heading"
        echo -e "$efi_out"
    fi
}

function valid_grub_partition() {
    # $1: partition device - can be /dev/partition_name (e.g. /dev/sda1) or just partition_name (sda1)
    # Returns:
    #   0: if it is a partition containing /boot/grub/grub.cfg
    #   1: not a partition containing /boot/grub/grub.cfg
    #   2: not running as root
    [[ $# -lt 1 ]] && return 1
    local d=$1
    [[ $d =~ ^/dev/ ]] || d="/dev/$d"
    [[ ! -b "$d" ]] && {
        return 1
    }
    valid_partition $d || return 1
    local fstype=$(lsblk -d -n -s FSTYPE-o value $d 2>/dev/null || true)
    [[ -z "$fstype" ]] && return 1
    [[ "$fstype" = "LVM2_member" ]] && return 1

    # Rest needs root
    [[ $(id -u) -ne 0 ]] && return 2

    local mounted=no
    local mountpoint=$(findmnt -n -o TARGET $d || true)
    [[ -n "$mountpoint" ]] && mounted=yes
    if [[ "$mounted" = "no" ]]; then
        mountpoint=$(mktemp -d "/tmp/valid_grub_partition.XXXXXX")
        mount $d $mountpoint 2>/dev/null || { rmdir $mountpoint; return 1; }
    fi

    local ret=0
    [[ -f "$mountpoint"/boot/grub/grub.cfg ]] || ret=1
    if [[ "$mounted" = "no" ]]; then
        findmnt -n -o SOURCE --mountpoint "$mountpoint" 1>/dev/null 2>&1  && umount -l "$mountpoint" 2>/dev/null
        rmdir $mountpoint
        [[ -d "$mountpoint" ]] && >&2 echo "Removing failed: $mountpoint"
    fi
    return $ret
}

function show_grub_partitions(){
    # Outputs list of partitions containing /boot/grub/grub.cfg
    # Returns 2: if not running as root
    [[ $(id -u) -ne 0 ]] && return 2
    local p_out=$(show_all_disk_partitions)
    local heading=$(echo "$p_out" | head -1)
    local list=$(echo "$p_out" | sed -e '1d')
    local grub_out=""

    while read line
    do
        local p=$(echo "$line" | awk '{print $1}')
        valid_grub_partition "$p" || continue
        [[ -n "$grub_out" ]] && {
            line="\n${line}"
        }
        grub_out="${grub_out}${line}"
    done <<< $list
    if [[ -n "$grub_out" ]]; then
        echo -e "$heading"
        echo -e "$grub_out"
    fi
}

function choose_efi_partition(){
    # Prints available ESP partitions, allows user to choose a partition, prints chosen
    # partition device to stdout
    # User can enter partition device as /dev/dev_name (e.g. /dev/sda1) or just dev_name (sda1)
    # If there is only one ESP partition it is automatically output to stdout
    # Returns:
    #   0: If ESP partition was chosen
    #   1: If user exited without choosing
    #   2: If no ESP partitions are available
    #   3: If not running as root
    [[ $(id -u) -ne 0 ]] && return 3

    local ret=""
    local chosen=no
    local available=""
    function choose_efi_return(){
        [[ -z "$available" ]] && return 1
        [[ "$available" = "no" ]] && return 2
        [[ "$chosen" = "no" ]] && return 1
    }
    trap choose_efi_return RETURN

    local p_out=$(show_efi_partitions)
    local list=$(echo -e "$p_out" | sed -e '1d')
    local list_len=$(echo "$list" | wc -l)
    if [[ $list_len -eq 0 ]]; then
        return 2
    elif [[ $list_len -eq 1 ]]; then
        local efi_part=$(echo "$list" | awk '{print $1}')
        >&2 echo "Found exactly one EFI System Partition: $efi_part"
        echo "$efi_part"
        return 0
    fi

    available=yes
    >&2 echo "$(show_disks)"
    >&2 echo ""
    >&2 echo ""
    >&2 echo -e "$p_out"
    >&2 echo ""

    while [[ -z "$ret" ]];
    do
        read -p "Choose EFI partition: " d
        [[ $d =~ ^/dev/ ]] || d="/dev/$d"
        valid_efi_partition "$d" || continue
        ret=$d
        chosen=yes
        break
    done
    echo "$ret"
}

function choose_grub_partition(){
    # Prints available grub partitions, allows user to choose a partition, prints chosen
    # partition device to stdout
    # User can enter partition device as /dev/dev_name (e.g. /dev/sda1) or just dev_name (sda1)
    # If there is only one grub partition it is automatically output to stdout
    # Returns:
    #   0: If grub partition was chosen
    #   1: If user exited without choosing
    #   2: If no grub partitions are available
    #   3: If not running as root
    [[ $(id -u) -ne 0 ]] && return 3

    local ret=""
    local chosen=no
    local available=""
    function choose_grub_return(){
        [[ -z "$available" ]] && return 1
        [[ "$available" = "no" ]] && return 2
        [[ "$chosen" = "no" ]] && return 1
    }
    trap choose_grub_return RETURN

    local p_out=$(show_grub_partitions)
    local list=$(echo -e "$p_out" | sed -e '1d')
    local list_len=$(echo "$list" | wc -l)
    if [[ $list_len -eq 0 ]]; then
        return 2
    elif [[ $list_len -eq 1 ]]; then
        local grub_part=$(echo "$list" | awk '{print $1}')
        >&2 echo "Found exactly one grub partition: $grub_part"
        echo "$grub_part"
        return 0
    fi

    available=yes
    >&2 echo "$(show_disks)"
    >&2 echo ""
    >&2 echo ""
    >&2 echo -e "$p_out"
    >&2 echo ""

    while [[ -z "$ret" ]];
    do
        read -p "Choose grub partition: " d
        [[ $d =~ ^/dev/ ]] || d="/dev/$d"
        valid_grub_partition "$d" || continue
        ret=$d
        chosen=yes
        break
    done
    echo "$ret"
}
