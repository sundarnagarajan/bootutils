#!/bin/bash
PROG_DIR=$(dirname "$BASH_SOURCE")
PROG_DIR=$(readlink -e "$PROG_DIR")
PROG_NAME=$(basename "$BASH_SOURCE")

source "$PROG_DIR"/disk_partition_functions.sh || {
    >&2 echo "Could not source: $PROG_DIR/disk_partition_functions.sh"
    exit 1
}

function create_update_efi(){
    # Creates exactly 3 files:
    #   bootia32.efi
    #   bootx64.efi
    #   grub.cfg
    #
    # Usage: -o|--output_dir <existing_dir> [-f|--force] [-n|--dry-run] [-k|--keep] [-h|--help]
    #   -o|--output <existing_dir> : Directory to copy generated files - must exist
    #   -f|--force : Overwrite files in <existing_dir> if they exist
    #   -n|--dry-run : Do not copy files - ignores -o|--output and -f|--force
    #   -k|--keep : do not delete tmp dir where files are generated - output tmp dir location on stderr
    #   -g|--no-grub : Do not add grub partition UUID to generated grub.cfg
    #   -h|--help : Show usage and exit
    #
    # Returns:
    #   0: If -h|--help or if successful
    #   1: <existing_dir> does not exist
    #   2: Cannot write to existing dir
    #   3: Cannot overwrite file although -f|--force was used
    #   4: Not running as root
    #   5: output directory not specified
    #
    local help_only=no
    local use_grub_part=yes
    local out_dir=
    local force_overwrite=no
    local dry_run=no
    local keep_tmp=no
    local grub_part=
    local grub_part_uuid=
    local efi_mounted=no
    local efi_mount_dir=
    local tmp_dir=

    function create_update_efi_help(){
        echo "
Usage:
${PROG_NAME} -o|--output_dir <existing_dir> [-f|--force] [-n|--dry-run] [-k|--keep] [-h|--help]
   -o|--output <existing_dir> : Directory to copy generated filesi - must exist
   -f|--force : Overwrite files in <existing_dir> if they exist
   -n|--dry-run : Do not copy files - ignores -o|--output and -f|--force
   -k|--keep : do not delete tmp dir where files are generated - output tmp dir location on stderr
   -g|--no-grub : Do not add grub partition UUID to generated grub.cfg
   -h|--help : Show usage and exit
"
    }

    while [[ $# -gt 0 ]];
    do
        case "$1" in
            -f|--force)
                force_overwrite=yes
                shift
                ;;
            -n|--dry-run)
                dry_run=yes
                shift
                ;;
            -k|--keep)
                keep_tmp=yes
                shift
                ;;
            -h|--help)
                help_only=yes
                shift
                ;;
            -g|--no-grub)
                use_grub_part=no
                shift
                ;;
            -o|--output)
                shift
                [[ $# -gt 0 ]] && {
                    out_dir="$1"
                    shift
                } || {
                    >&2 echo "Output directory not specified"
                    return 5
                }
                ;;
        esac
    done
    [[ "$help_only" = "yes" ]] && {
        create_update_efi_help
        return 0
    }
    
    out_dir=$(readlink -m "$out_dir" || true)
    if [[ -n "$out_dir" && ! -d "$out_dir" ]]; then
        >&2 echo "Output directory does not exist: $out_dir"
        create_update_efi_help
        return 1
    fi
    if [[ "$use_grub_part" = "yes" ]]; then
        [[ $(id -u) -ne 0 ]] && {
            >&2 echo "Need to run as sudo"
            create_update_efi_help
            return 4
        }
        grub_part=$(choose_grub_partition || true)
        grub_part_uuid=$(blkid -s UUID -o value $grub_part)
    fi

    tmp_dir=$(mktemp -d "/tmp/create_update_efi.XXXXXX")
    echo '
sundar@smaug:~/rdp/rdp-thinbook-linux/remaster/iso_post/grub$ cat grub_embedded.cfg 
insmod memdisk
insmod normal
insmod configfile
insmod part_gpt
insmod search_fs_uuid
insmod search_fs_file
insmod search_label
insmod search

# $cmdpath does NOT return (always) the correct root/path
# E.g.: returns (hd0)/EFI/BOOT instead of (hd0,gpt2)/efi/boot
# search --file for anon-existent file path HANGS!
# search --fs-uuid for a non-existent uuid HANGS!

cfgpath=efi/boot/grub.cfg
set found=0
set max=0
for p in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16
do
    set max=$p
    if [ -f (hd0,gpt$p)/$cfgpath ]; then
        set found=$p
        break
    fi
done

if [ $found -ne 0 ]; then
    echo "Using (hd0,gpt$found)"
    configfile (hd0,gpt$found)/$cfgpath
fi

echo "$cfgpath not found in first $max partitions of hd0"
echo "Press RETURN to continue"
read
' > ${tmp_dir}/grub_embedded.cfg

    echo '
set GRUB_FS_UUID=
if [ -n "$GRUB_FS_UUID" ]; then
    echo "Using GRUB_FS_UUID : $GRUB_FS_UUID"
    search --fs-uuid --set=root $GRUB_FS_UUID
    set cfgpath=/boot/grub/grub.cfg
    if [ -f $cfgpath ]; then
        configfile $cfgpath
    else
        echo "cfgpath not found: $cfgpath"
    fi
fi

# Otherwise use (hd0) automatically

set root=(hd0)
set cfgpath=($root)/boot/grub/grub.cfg
echo "Using hd0 : $cfgpath"
if [ -f $cfgpath ]; then
    configfile $cfgpath
else
    echo "config file not found : $cfgpath"
fi

echo "Press RETURN to continue"
read
' > ${tmp_dir}/grub.cfg

    if [[ -n "$grub_part_uuid" ]]; then
        sed -i -e "s/set GRUB_FS_UUID=.*\$/set GRUB_FS_UUID=${grub_part_uuid}/" ${tmp_dir}/grub.cfg
        >&2 echo "Updated GRUB_FS_UUID=${grub_part_uuid} in grub.cfg"
    fi

    grub-mkstandalone --format=i386-efi --compress=gz --output=${tmp_dir}/bootia32.efi "boot/grub/grub.cfg=${tmp_dir}/grub_embedded.cfg"
    grub-mkstandalone --format=x86_64-efi --compress=gz --output=${tmp_dir}/bootx64.efi "boot/grub/grub.cfg=${tmp_dir}/grub_embedded.cfg"
    \rm -f ${tmp_dir}/grub_embedded.cfg

    local target_dir=$tmp_dir
    if [[ -n "$out_dir" ]]; then
        if [[ "$dry_run" = "no" ]]; then
            for f in bootia32.efi bootx64.efi grub.cfg
            do
                if [[ -f "$out_dir"/$f ]]; then
                    if [[ "$force_overwrite" = "yes" ]]; then
                        >&2 echo "Overwriting $out_dir/$f"
                        \cp -f ${tmp_dir}/${f} "$out_dir"/$f
                    else
                        >&2 echo "Not overwriting $out_dir/${f}. Use -f|--force to override"
                    fi
                else
                    >&2 echo "Creating $out_dir/$f"
                    cp -n -v ${tmp_dir}/${f} "$out_dir"/$f
                fi
            done
            target_dir=$out_dir
        else
            if [[ "$keep_tmp" = "no" ]]; then
                >&2 echo "Not copying any files because of -n|--dry-run"
                >&2 echo "Use -k|--keep to preserve files in tmp dir"
            fi
        fi
    else
        if [[ "$keep_tmp" = "no" ]]; then
            >&2 echo "Not copying any files because output dir not set"
            create_update_efi_help
        fi
    fi

    if [[ "$efi_mounted" = "yes" ]]; then
        if [[ -n "$efi_mount_dir" ]]; then
            findmnt -n -o SOURCE --mountpoint "$efi_mount_dir" 1>/dev/null 2>&1  && umount $efi_mount_dir 2>/dev/null
            rmdir $efi_mount_dir
            [[ -d "$efi_mount_dir" ]] && >&2 echo "Removing failed: $efi_mount_dir"
        fi
    fi
    if [[ "$keep_tmp" = "no" ]]; then
        if [[ -d "$tmp_dir" ]]; then
            \rm -rf "$tmp_dir"
        fi
    else
        >&2 echo "Generated files are in $tmp_dir"
    fi
}
