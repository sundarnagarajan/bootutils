#!/usr/bin/env python
'''
Uses the following commands, which _SHOULD_ normally be present in all
(newer) Linux systems:
    Command            Ubuntu package  Version tested
    -------------------------------------------------------------------
    lsblk              util-linux      2.27.1-6ubuntu3.2
    parted             parted          3.2-15
    sgdisk             gdisk           1.0.1-1build1
    blkid              util-linux      2.27.1-6ubuntu3.2
    umount             mount           2.27.1-6ubuntu3.2
    mkfs.vfat          dosfstools      3.0.28-2ubuntu0.1
    grub-install       grub2-common    2.02~beta2-36ubuntu3.9
    grub-mkdevicemap   grub-common     2.02~beta2-36ubuntu3.9
    grub-mkconfig      grub-common     2.02~beta2-36ubuntu3.9
    grub-mkstandalone  grub-common     2.02~beta2-36ubuntu3.9
'''

import sys
sys.dont_write_bytecode = True
import subprocess  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
from collections import namedtuple  # noqa: E402
from itertools import count  # noqa: E402
from multiboot import GrubMenu  # noqa: E402
from common_utils import (
    MountedDirTemp,
    TempDir,
    LineWithComments,
    highlight_str,
)  # noqa: E402

if sys.version_info[0] == 2:
    input = raw_input           # noqa F821

Partition = namedtuple(
    'Partition',
    ['num', 'start', 'end', 'size', 'code', 'name', 'path', 'fs']
)
DECODE_LANG = 'utf8'
TMP_MOUNT_DIR = '/media'
EMBEDDED_GRUB_CFG_FILE = 'grub_embedded.cfg'
CHROOT_GRUB_MKCONFIG_SCRIPT = "__chroot_grub_mkconfig.sh"
BOOTDISK_MKCONFIG_SCRIPT = "__boot_grub_mkconfig.sh"
GRUB_FS_UUID_FILE = 'grub_fs_uuid.cfg'
def_mode = int('755', 8)
owner_mode = int('700', 8)


def get_valid_disk_paths():
    '''
    Returns-->list of str: each a device path - e.g. /dev/sda
    '''
    cmd = 'lsblk -nd -o NAME'
    out = subprocess.check_output(cmd, shell=True)
    return [os.path.join(
        '/dev', x.decode(DECODE_LANG)) for x in out.splitlines()]


def erase_partition_table(dev_path):
    '''
    dev_path-->str: path to disk (e.g. /dev/sda)
    Destroys partition table by using dd.
    This is for cases where parted cannot read the partition table -
    e.g. when disk is an ISO (!!)
    '''
    l = get_valid_disk_paths()
    if dev_path not in l:
        raise ValueError('Invalid disk device: ' + dev_path)
    msg = ('Confirm erase of ALL data and partitions on device %s'
           '\nEnter YES to continue') % (dev_path,)
    print(highlight_str(msg))
    a = input()
    if a != 'YES':
        return False
    cmd = 'dd if=/dev/zero of=%s bs=128k count=80 1>/dev/null 2>&1' % (
        dev_path
    )
    subprocess.call(cmd, shell=True)
    return True


def get_disk_model(dev_path):
    '''
    dev_path-->str: path to disk (e.g. /dev/sda)
    Returns-->str
    '''
    dev_base = os.path.basename(dev_path)
    model_file = os.path.join('/sys/block/', dev_base, 'device/model')
    rev_file = os.path.join('/sys/block/', dev_base, 'device/rev')
    ser_file = os.path.join('/sys/block/', dev_base, 'device/serial')
    (m, s, r) = ('', '', '')
    if os.path.isfile(model_file):
        m = open(model_file, 'r').read().splitlines()[0]
    if os.path.isfile(ser_file):
        s = open(ser_file, 'r').read().splitlines()[0]
    if os.path.isfile(rev_file):
        r = open(rev_file, 'r').read().splitlines()[0]
    else:
        rev_file = os.path.join(
            '/sys/block/', dev_base, 'device/firmware_rev')
        if os.path.isfile(rev_file):
            r = open(rev_file, 'r').read().splitlines()[0]
    # Special hack for MMC
    if not m.strip() and dev_base.startswith('mmc'):
        model_file = os.path.join('/sys/block/', dev_base, 'device/name')
        rev_file = os.path.join('/sys/block/', dev_base, 'device/fwrev')
        if os.path.isfile(model_file):
            m = open(model_file, 'r').read().splitlines()[0]
        if os.path.isfile(rev_file):
            r = open(rev_file, 'r').read().splitlines()[0]

    (m, s, r) = (m.strip(), s.strip(), r.strip())
    m = m.replace(' ', '_')
    return ' '.join([m, s, r])


def is_disk_removable(dev_path):
    '''
    dev_path-->str: path to disk (e.g. /dev/sda)
    Returns-->bool
    '''
    ret = False
    dev_base = os.path.basename(dev_path)
    rem_file = os.path.join(
        '/sys/block/%s/removable' % (dev_base,)
    )
    if os.path.isfile(rem_file):
        try:
            x = open(rem_file, 'r').read().rstrip('\n')
            if x == '1':
                ret = True
        except:
            pass
    return ret


def show_available_disks():
    disks = get_valid_disk_paths()
    fmt = '%-20s  %-5s %s'
    print(fmt % ('Disk path', 'RM', 'Model-Serial-Rev'))
    dl = []
    for p in disks:
        dl += [fmt % (
            p,
            is_disk_removable(p) and 'Y' or 'N',
            get_disk_model(p)
        )]
    dl.sort()
    print('\n'.join(dl))


def get_partition_uuid(part_path):
    '''
    part_path-->str: full path to root partition (e.g. /dev/sda3)
    Returns-->str: UUID or ''
    '''
    cmd = 'blkid -o value -s UUID ' + part_path
    ret = ''
    try:
        ret = subprocess.check_output(cmd, shell=True).splitlines()[0]
    except:
        pass
    return ret


def is_valid_partition(part_path):
    '''
    part_path-->str: full path to partition (e.g. /dev/sda3)
    Returns-->bool
    '''
    (p, b) = (os.path.dirname(part_path),
              os.path.basename(part_path))
    if p != '/dev':
        return False
    l = open('/proc/partitions', 'r').read().splitlines()[2:]
    part_list = [x.split(None, 3)[3] for x in l]
    if b not in part_list:
        return False
    return True


def update_fstab_boot_efi(boot_disk, root_partition):
    '''
    boot_disk-->str: disk device path (e.g. /dev/sda)
    root_partition-->str: full path to root partition (e.g. /dev/sda3)
    '''
    if boot_disk not in get_valid_disk_paths():
        raise ValueError('Invalid disk path: ' + boot_disk)
    if not is_valid_partition(root_partition):
        raise ValueError('Invalid partition ' + root_partition)

    d = DiskDetails(boot_disk)
    efi_partition = d.get_efi_partition()
    if not efi_partition:
        raise ValueError('%s does not have an EFI partition' % (boot_disk,))
    efi_uuid = get_partition_uuid(efi_partition)
    if not efi_uuid:
        print('No UUID found, cannot update fstab')
        return
    with MountedDirTemp(
        src=root_partition,
        parent_dir=TMP_MOUNT_DIR,
        opts=''
    ) as temp_dir:
        fstab_path = os.path.join(temp_dir, 'etc/fstab')
        if not os.path.exists(fstab_path):
            sys.stderr.write(
                'fstab not found: %s\n' % (fstab_path,))
            print(os.listdir(os.path.dirname(fstab_path)))
            return
        fstab = FSTab(fstab_path=fstab_path)
        l = fstab.find_first(mountpoint='/boot/efi')
        if l is None:
            sys.stderr.write(
                '/boot/efi not mounted in %s\n' % (fstab_path,))
            return
        fstab.update_line(l[0], src='UUID=%s' % (efi_uuid,))
        with open(fstab_path, 'w') as f:
            f.write(str(fstab).encode(DECODE_LANG))
            f.flush()


class FSTabLine(object):
    '''
    A single uncommented line in /etc/fstab

    Structure of /etc/fstab: six whitespace-separated fields
        <file_system> <mount_point> <type> <options> <dump> <pass>
    '''
    def __init__(self, l):
        '''
        l-->str: uncommented line text
        '''
        parts = l.split()
        (parts[4], parts[5]) = (int(parts[4]), int(parts[5]))
        (self.src, self.mountpoint, self.fs,
         self.options, self.dump, self.pas) = parts

    @property
    def line(self):
        '''
        Returns-->str: reconstructed line
        '''
        fmt = '%s  %s  %s  %s  %d %d'
        return fmt % (
            self.src, self.mountpoint, self.fs,
            self.options, self.dump, self.pas
        )

    def __str__(self):
        return self.line


class FSTab(object):
    '''
    Class that supports:
        - Searching for lines matching attributes in /etc/fstab
        - Modifying lines
        - Writing back modified fstab
    '''
    def __init__(self, fstab_path='/etc/fstab'):
        self.fstab = open(fstab_path, 'r').read()
        self._parse()

    def _parse(self):
        self.parsed_lines = [
            LineWithComments(x) for x in self.fstab.splitlines()
        ]
        self.code_lines = []
        for (n, l) in zip(count(0), self.parsed_lines):
            if not l.nc:
                self.code_lines.append((n, None))
                continue
            try:
                fl = FSTabLine(l.nc)
            except:
                sys.stderr.write('Commenting invalid line: %s \n' % (l.line,))
                l.comm = '## ' + l.nc + l.comm
                l.nc = ''
                self.code_lines.append((n, None))
                continue
            self.code_lines.append([n, fl])

    def show_valid_lines(self):
        fmt = '%-50s %-20s %-11s %-20s %-2s %-2s'
        for (n, fl) in self.code_lines:
            if fl is None:
                continue
            print(fmt % (
                fl.src, fl.mountpoint, fl.fs, fl.options, fl.dump, fl.pas
            ))

    def find_first(self, **kwargs):
        '''
        kwargs: any or all of FSTabLine attributes
        Returns-->tuple: (n-->line_num, l-->FSTabLine) or None
        Returns ONLY FIRST matching line NOT ALL matching lines
        '''
        def check_fl(fl1, kw):
            ret1 = True
            for (k, v) in kw.items():
                if getattr(fl1, k, None) != v:
                    ret1 = False
                    break
            return ret1

        ret = None
        for (n, fl) in self.code_lines:
            if fl is None:
                continue
            if not check_fl(fl, kwargs):
                continue
            ret = (n, fl)
            break
        return ret

    def update_line(self, n, **kwargs):
        '''
        n-->int: line number (zero-based)
        kwargs: any or all of FSTabLine attributes
        '''
        fl = self.code_lines[n][1]
        for (k, v) in kwargs.items():
            setattr(fl, k, v)
        l = self.parsed_lines[n]
        l.nc = str(fl)
        self.fstab = str(self)

    def __str__(self):
        ret = '\n'.join([str(x) for x in self.parsed_lines])
        if not ret.endswith('\n'):
            ret += '\n'
        return ret


class DiskDetails(object):
    efi_part_code = 'EF00'
    bios_part_code = 'EF02'
    linux_part_code = '8300'

    def __init__(self, d):
        '''
        d-->str: device path (e.g. /dev/sda)
        '''
        if d not in get_valid_disk_paths():
            raise ValueError('Invalid disk path')
        self.devpath = d
        self.scan()

    def scan(self):
        '''
        Scans (or rescans) disk and partition details
        '''
        sys.stderr.write('Scanning partitions on %s\n' % (self.devpath))
        self._run_commands()
        self._parse_cmd_output()

    def _run_commands(self):
        devnull = open(os.devnull, 'w')
        head_pat = b'(?P<HEAD>.*?)\n\n'
        list_pat = b'\n\n(?P<PARTLIST>Number.*)$'

        # First parted
        out = None
        cmd = 'parted -s %s print' % (self.devpath,)
        try:
            # out = subprocess.check_output(cmd, shell=True, stderr=devnull)
            out = subprocess.Popen(
                cmd, shell=True, stderr=devnull,
                stdout=subprocess.PIPE).communicate()[0]
        except:
            pass
        if not out:
            raise ValueError('Invalid device path: %s' % (self.devpath))
        m = re.search(head_pat, out, re.MULTILINE + re.DOTALL)
        if m:
            self.parted_head = m.groupdict()['HEAD'].strip()
        else:
            self.parted_head = ''
        m = re.search(list_pat, out, re.MULTILINE + re.DOTALL)
        if m:
            self.parted_list = m.groupdict()['PARTLIST'].strip()
        else:
            self.parted_list = ''

        # next sgdisk
        out = None
        cmd = 'sgdisk --print %s' % (self.devpath,)
        try:
            # out = subprocess.check_output(cmd, shell=True, stderr=devnull)
            out = subprocess.Popen(
                cmd, shell=True, stderr=devnull,
                stdout=subprocess.PIPE).communicate()[0]
        except:
            pass
        if not out:
            raise ValueError('Invalid device path: %s' % (self.devpath))
        m = re.search(head_pat, out, re.MULTILINE + re.DOTALL)
        if m:
            self.sgdisk_head = m.groupdict()['HEAD'].strip()
        else:
            self.sgdisk_head = ''
        m = re.search(list_pat, out, re.MULTILINE + re.DOTALL)
        if m:
            self.sgdisk_list = m.groupdict()['PARTLIST'].strip()
        else:
            self.sgdisk_list = ''

    def _parse_cmd_output(self):
        self.diskinfo = self.parted_head + self.sgdisk_head
        self.diskinfo = self.diskinfo.decode(DECODE_LANG)
        self.partitions = []

        pl1 = self.parted_list.splitlines()[1:]
        pl2 = self.sgdisk_list.splitlines()[1:]
        pl1.sort()
        pl2.sort()
        for n in range(len(pl1)):
            try:
                l1 = pl1[n].split(None, 4)
                if len(l1) < 7:
                    l1.append('')
            except:
                l1 = []
            try:
                l2 = pl2[n].split(None, 6)
                if len(l2) < 7:
                    l2.append('')
            except:
                l2 = []

            part_path = self.get_part_path(n + 1)
            part_fs = self.get_part_fs(part_path)

            num = 0
            start = 0
            end = 0
            size = ''
            code = ''
            name = ''
            if l1:
                size = l1[3].decode(DECODE_LANG)
            if l2:
                num = int(l2[0])
                start = l2[1].decode(DECODE_LANG)
                end = l2[2].decode(DECODE_LANG)
                code = l2[5].decode(DECODE_LANG)
                name = l2[6].decode(DECODE_LANG)
            elif l1:
                num = int(l1[0])
                start = l1[1].decode(DECODE_LANG)
                end = l1[2].decode(DECODE_LANG)

            self.partitions.append(
                Partition(
                    num=num,
                    start=start,
                    end=end,
                    size=size,
                    code=code,
                    name=name,
                    path=part_path,
                    fs=part_fs,
                )
            )

        h = self.parted_head.splitlines()
        self.is_gpt = False
        for l in h:
            if not l:
                break
            if l.startswith(b'Partition Table:'):
                pt_type = l.split(b':', 1)[1].strip()
                self.is_gpt = (pt_type == b'gpt')

        # removable
        self.removable = is_disk_removable(self.devpath)
        self.diskinfo += '\nRemovable: %s' % (str(self.removable))
        self.diskinfo += '\nDisk Model-Rev: %s' % (
            get_disk_model(self.devpath))

    def get_part_path(self, n):
        '''
        n-->int: partition number
        Returns-->str: device path of partition
        Raises ValueError if (d, n) is invalid
        '''
        KNOWN_P_PREFIXES = [
            'mmcblk', 'nvme'
        ]
        ret = None
        d = self.devpath
        dev_base = os.path.basename(d)
        dev_dir = os.path.dirname(d)
        candidate_p = '%sp%d' % (dev_base, n)
        candidate_no_p = '%s%d' % (dev_base, n)

        for p in KNOWN_P_PREFIXES:
            if dev_base.startswith(p):
                ret = os.path.join(dev_dir, candidate_p)
                break
        if not ret:
            if os.path.isdir(
                os.path.join('/sys/block/', dev_base, candidate_p)
            ):
                ret = os.path.join(dev_dir, candidate_p)
            elif os.path.isdir(
                os.path.join('/sys/block/', dev_base, candidate_no_p)
            ):
                ret = os.path.join(dev_dir, candidate_no_p)

        if not ret or not os.path.exists(ret):
            raise ValueError(
                'Invalid device or partition number: %s, %d' % (d, n))

        return ret

    def partnum_by_path(self, p):
        '''
        p-->str: Partition path
        Returns-->int: Partition number (or None if not found)
        '''
        ret = None
        for x in range(len(self.partitions)):
            if self.partitions[x].path == p:
                ret = x + 1
                break
        return ret

    def get_part_fs(self, part_path):
        '''
        part_path-->str: device path (e.g. /dev/sda1)
        Returns-->str or '': filesystem type
        '''
        cmd = 'blkid -o value -s TYPE ' + part_path
        ret = ''
        try:
            ret = subprocess.check_output(cmd, shell=True)
        except:
            pass
        ret = ret.rstrip(b'\n')
        return ret.decode(DECODE_LANG)

    def get_efi_partition(self):
        '''
        Returns-->str or None: partition path of EFI partition
        '''
        ret = None
        ret = None
        for p in self.partitions:
            if p.code == self.efi_part_code:
                return p.path
        return ret

    def has_efi_partition(self):
        '''
        Returns-->boolean
        '''
        return self.get_efi_partition() is not None

    def get_bios_partition(self):
        '''
        Returns-->str or None: partition path of BIOS partition
        '''
        ret = None
        ret = None
        for p in self.partitions:
            if p.code == self.bios_part_code:
                return p.path
        return ret

    def has_bios_partition(self):
        '''
        Returns-->boolean
        '''
        return self.get_bios_partition() is not None

    def __repr__(self):
        return 'DiskDetails(%s)' % (self.devpath,)

    def __str__(self):
        ret = '\n' + self.diskinfo + '\n'

        hfmt = '\n%3s %-12s %-12s %-7s %-4s %-16s %-11s %s'
        rfmt = '\n%3d %-12s %-12s %-7s %-4s %-16s %-11s %s'
        ret += hfmt % (
            'Num', 'Start', 'End', 'Size', 'Code', 'Name', 'FS', 'Path'
        )
        for p in self.partitions:
            ret += rfmt % (
                p.num, p.start, p.end, p.size, p.code, p.name, p.fs, p.path
            )
        return ret

    def highlight_partition(self, n):
        '''
        n-->int: partition number (1-based)
        Prints str representation, highlighting partition n in inverse video
        '''
        if n > len(self.partitions):
            raise ValueError('Invalid partition number: %d' % (n,))

        ret = '\n' + self.diskinfo + '\n'

        hfmt = '\n%3s %-12s %-12s %-7s %-4s %-16s %-11s %s'
        rfmt = '\n%3d %-12s %-12s %-7s %-4s %-16s %-11s %s'
        ret += hfmt % (
            'Num', 'Start', 'End', 'Size', 'Code', 'Name', 'FS', 'Path'
        )
        for i in range(len(self.partitions)):
            p = self.partitions[i]
            x = rfmt % (
                p.num, p.start, p.end, p.size, p.code, p.name, p.fs, p.path
            )
            if i == (n - 1):
                x = highlight_str(x)
            ret += x
        print(ret)

    def confirm_action(self, msg, n=None):
        '''
        msg-->str: Action to be confirmed
        n-->int partition number (or None)
        Returns-->boolean
        '''
        print(highlight_str(msg))
        print('')
        if n is not None:
            self.highlight_partition(n)
        else:
            print(self)
        print('')
        try:
            prompt = highlight_str('Enter "YES" to confirm:') + '\n'
            resp = input(prompt)
            return resp == 'YES'
        except KeyboardInterrupt:
            return False

    def erase_disk(self):
        '''
        ***** DESTRUCTIVE OPERATION *****
        Deletes ALL partitions and removes partition table
        Creates new empty GPT partition table
        '''
        # Unmount any partitions that are mounted
        cmd = 'umount %s'
        for p in self.partitions:
            subprocess.call(cmd % (p.path,), shell=True)

        dd_cmd = 'dd if=/dev/zero of=%s bs=128k count=80' % (self.devpath,)
        zap_cmd = 'sgdisk -Z ' + self.devpath
        empty_cmd = 'sgdisk -o ' + self.devpath
        subprocess.call(dd_cmd, shell=True)
        subprocess.call(zap_cmd, shell=True)
        subprocess.call(empty_cmd, shell=True)
        subprocess.call('partprobe', shell=True)
        self.scan()

    def _create_efi_or_bios_partition(self, code, name, size, label, fetcher):
        '''
        code-->str
        name-->str
        size-->str
        label-->str
        fetcher-->callable: should return partition path
        '''
        existing_part = fetcher()
        if existing_part:
            print(highlight_str('Disk already has %s partition' % (name,)))
            print(self.highlight_partition(
                self.partnum_by_path(existing_part)
            ))
            return False
        part_create_cmd = 'sgdisk --new=0:0:%s -t 0:%s -c 0:%s %s' % (
            size, code, label, self.devpath
        )

        subprocess.call(part_create_cmd, shell=True)
        subprocess.call('partprobe', shell=True)
        self.scan()
        existing_part = fetcher()
        if not existing_part:
            raise RuntimeError('Could not create %s partition' % (name,))
        print(highlight_str('Created %s partition' % (name,)))
        print(self.highlight_partition(
            self.partnum_by_path(existing_part)
        ))
        return True

    def create_efi_partition(self, bios_partition=True,
                             bios_size='+20M', efi_size='+80M'
                             ):
        '''
        bios_partition-->bool: Whether to ALSO create partition of type
            BIOS (EF02) to support non-EFI grub
        bios_size-->str: size of BIOS partition in sgdisk dialect
            Examples:
                +80M : 80 MB starting at default start sector
                -0   : Use all available space
        efi_size-->str: size of EFI partition in sgdisk dialect
            See bios_part_size for examples
        Creates a NEW partition of type EFI (EF00) and creates a VFAT
        filesystem on it
        '''
        # BIOS partition for non-EFI grub
        if bios_partition:
            self._create_efi_or_bios_partition(
                code=self.bios_part_code, name='BIOS', size=bios_size,
                label='BIOSGRUB', fetcher=self.get_bios_partition
            )
            # No filesystem required for BIOS partition
        # EFI Partition
        if self._create_efi_or_bios_partition(
            code=self.efi_part_code, name='EFI', size=efi_size,
            label='EFI', fetcher=self.get_efi_partition
        ):
            # Create FS only if new EFI partition was created
            self.scan()
            p = self.get_efi_partition()
            fs_create_cmd = 'mkfs.vfat -F 32 -n EFI ' + p
            subprocess.call(fs_create_cmd, shell=True)
            print(highlight_str('Created VFAT FS on %s' % (p,)))
            self.highlight_partition(self.partnum_by_path(p))

    def write_efi_files(self, cfg_dir, efi_boot_dir, embed_uuid):
        '''
        cfg_dir-->str: Dir with grub_embedded.cfg
        efi_boot_dir-->str: Directory to write files
        embed_uuid-->str: FS UUID to embed in grub-efi
        '''
        cfg = os.path.join(cfg_dir, EMBEDDED_GRUB_CFG_FILE)
        if not os.path.isfile(cfg):
            raise ValueError(
                'Embedded grub config file not found: %s' % (cfg,))
        if not os.path.isdir(efi_boot_dir):
            raise ValueError('Not a directory: %s' % (efi_boot_dir,))
        with TempDir(parent_dir=TMP_MOUNT_DIR) as temp_dir:
            temp_cfg = os.path.join(temp_dir, 'current.cfg')
            with open(temp_cfg, 'w') as f:
                f.write('set efi_fs_uuid=%s\n' % (embed_uuid,))
                f.write(open(cfg, 'r').read())
                f.flush()
            fmt = ('grub-mkstandalone --format=%s --output=%s/%s'
                   ' "boot/grub/grub.cfg=%s"')

            grub_fmt = 'i386-efi'
            out_file = 'bootia32.efi'
            cmd = fmt % (grub_fmt, efi_boot_dir, out_file, temp_cfg)
            subprocess.call(cmd, shell=True)

            grub_fmt = 'x86_64-efi'
            out_file = 'bootx64.efi'
            cmd = fmt % (grub_fmt, efi_boot_dir, out_file, temp_cfg)
            subprocess.call(cmd, shell=True)

    def install_grub_mbr(self, root_partition):
        '''
        root_partition-->str: root partition device path
        Installs grub-mbr to MBR
        Does not destroy partitions or other data
        '''
        if self.get_bios_partition():
            with MountedDirTemp(
                src=root_partition,
                parent_dir=TMP_MOUNT_DIR,
                opts=''
            ) as temp_dir:
                boot_dir = os.path.join(temp_dir, 'boot')
                if not os.path.isdir(boot_dir):
                    os.makedirs(boot_dir, mode=def_mode)
                cmd = ('grub-install --target=i386-pc '
                       ' --boot-directory=%s %s' % (
                           boot_dir, self.devpath
                       ))
                subprocess.call(cmd, shell=True)

    def install_grub_efi(self, embed_uuid):
        '''
        embed_uuid-->str: FS UUID to embed in grub-efi
        Installs grub-efi under /EFI/BOOT on EFI partition
        Does not destroy partitions or other data
        '''
        efi_partition = self.get_efi_partition()
        if not efi_partition:
            raise ValueError('Disk does not have EFI partition')

        cfg_dir = os.path.realpath(os.path.dirname(__file__))
        with MountedDirTemp(
            src=self.get_efi_partition(),
            parent_dir=TMP_MOUNT_DIR,
            opts=''
        ) as temp_dir:

            efi_boot_dir = os.path.join(temp_dir, 'EFI/BOOT')
            if not os.path.isdir(efi_boot_dir):
                os.makedirs(efi_boot_dir, mode=def_mode)
            self.write_efi_files(
                cfg_dir=cfg_dir,
                efi_boot_dir=efi_boot_dir,
                embed_uuid=embed_uuid
            )

    def create_ext4_part_and_fs(self, ext4_size='-0', label='BOOT'):
        '''
        ext4_size-->str: size of EXT4 partition in sgdisk dialect
            Examples:
                +1G : 1 GB starting at default start sector
                -0   : Use all available space
        '''
        part_create_cmd = 'sgdisk --new=0:0:%s -t 0:%s -c 0:%s %s' % (
            ext4_size, self.linux_part_code, label, self.devpath
        )
        subprocess.call(part_create_cmd, shell=True)
        subprocess.call('partprobe', shell=True)
        self.scan()
        p = self.partitions[-1].path
        fs_create_cmd = 'mkfs.ext4 -F -m 1 -L %s %s' % (label, p)
        subprocess.call(fs_create_cmd, shell=True)
        subprocess.call('partprobe', shell=True)
        self.scan()
        print(highlight_str('Created EXT4 FS on %s' % (p,)))
        self.highlight_partition(self.partnum_by_path(p))
        # Create required dirs on boot partition
        with MountedDirTemp(src=p, parent_dir=TMP_MOUNT_DIR) as temp_dir:
            os.makedirs(os.path.join(temp_dir, 'boot/grub'), mode=def_mode)
            os.makedirs(os.path.join(temp_dir, 'boot/efi'), mode=owner_mode)

    def bootdisk_erase_create(self, bios_size='+20M', efi_size='+80M'):
        '''
        Will erase all partitions and data (DESTRUCTIVE)
        bios_size-->str: size of BIOS partition in sgdisk dialect
            Examples:
                +80M : 80 MB starting at default start sector
                -0   : Use all available space
        efi_size-->str: size of EFI partition in sgdisk dialect
            See bios_part_size for examples
        Will create a BIOS partition (for grub-mbr) of size bios_size
        Will create an EFI partition of size efi_size
            -0 means use all remaining space
        '''
        need_bios_partition = True
        self.erase_disk()
        self.create_efi_partition(
            bios_partition=need_bios_partition,
            bios_size=bios_size,
            efi_size=efi_size)
        print(self)
        self.install_grub_efi(get_partition_uuid(self.get_efi_partition()))

        efi_partition = self.get_efi_partition()
        with MountedDirTemp(
            src=efi_partition,
            parent_dir=TMP_MOUNT_DIR,
            opts=''
        ) as temp_dir:
            efi_boot_dir = os.path.join(temp_dir, 'EFI/BOOT')
            if not os.path.isdir(efi_boot_dir):
                os.makedirs(efi_boot_dir)
            self.create_ext4_part_and_fs()
            bootfs_uuid = get_partition_uuid(self.partitions[-1].path)
            with open(os.path.join(temp_dir, GRUB_FS_UUID_FILE), 'w') as f:
                f.write('set grub_fs_uuid="%s"\n' % bootfs_uuid)
                f.flush()

    def bootdisk_populate_update_cfg(self, boot_partition, boot_dir=None):
        '''
        boot_partition-->str: EXT4 partition on boot_disk
        boot_dir--.str: Path to dir with boot files (vmlinuz, initrd etc.)
            If set, these files will be copied
        '''
        with MountedDirTemp(
            src=boot_partition,
            parent_dir=TMP_MOUNT_DIR,
        ) as boot:
            if not os.path.isdir(os.path.join(boot, 'boot/grub')):
                os.makedirs(os.path.join(boot, 'boot/grub'), mode=def_mode)
            if not os.path.isdir(os.path.join(boot, 'boot/efi')):
                os.makedirs(
                    os.path.join(boot, 'boot/efi'), mode=owner_mode)
            if boot_dir:
                if os.path.isdir(boot_dir):
                    cmd = 'cp -rPxv %s/. %s/.' % (
                        boot_dir,
                        os.path.join(boot, 'boot')
                    )
                    subprocess.call(cmd, shell=True)

        # Update grub.cfg by calling external script
        script_dir = os.path.realpath(os.path.dirname(__file__))
        chroot_script = os.path.join(
            script_dir, BOOTDISK_MKCONFIG_SCRIPT)
        cmd = ' '.join([chroot_script, boot_partition])
        sys.stderr.write('Executing: %s\n' % (cmd,))
        subprocess.call(cmd, shell=True)

    def multiboot_erase_create(self, bios_size='+20M', efi_size='-0'):
        '''
        Will erase all partitions and data (DESTRUCTIVE)
        bios_size-->str: size of BIOS partition in sgdisk dialect
            Examples:
                +80M : 80 MB starting at default start sector
                -0   : Use all available space
        efi_size-->str: size of EFI partition in sgdisk dialect
            See bios_part_size for examples
        Will create a BIOS partition (for grub-mbr) of size bios_size
        Will create an EFI partition of size efi_size
            -0 means use all remaining space
        '''
        need_bios_partition = True
        self.erase_disk()
        self.create_efi_partition(
            bios_partition=need_bios_partition,
            bios_size=bios_size,
            efi_size=efi_size)
        print(self)

        efi_partition = self.get_efi_partition()
        with MountedDirTemp(
            src=efi_partition,
            parent_dir=TMP_MOUNT_DIR,
            opts=''
        ) as temp_dir:
            iso_dir = os.path.join(temp_dir, 'iso')
            efi_boot_dir = os.path.join(temp_dir, 'EFI/BOOT')
            os.mkdir(iso_dir)
            os.makedirs(efi_boot_dir)

        self.multiboot_instal_grub()

    def multiboot_instal_grub(self):
        '''
        Installs grub-efi under /EFI/BOOT on EFI partition
        Installs grub-mbr in MBR
        Does not destroy partitions or other data
        '''
        self.install_grub_efi(get_partition_uuid(self.get_efi_partition()))
        self.install_grub_mbr(self.get_efi_partition())

    def multiboot_update_config(self):
        '''
        Updates /boot/grub/grub.cfg on EFI partition
        Does not destroy partitions or other data
        '''
        with MountedDirTemp(
            src=self.get_efi_partition(),
            parent_dir=TMP_MOUNT_DIR,
            opts=''
        ) as temp_dir:
            cfg_file = os.path.join(temp_dir, 'boot/grub/grub.cfg')
            iso_dir = os.path.join(temp_dir, 'iso')
            g = GrubMenu(cfg_file=cfg_file, iso_dir=iso_dir)
            g.write()

    def rootfs_update_grub_config(self, root_partition):
        '''
        root_partition-->str: root partition device path
        /boot/grub/grub.cfg on root partition is updated using
            grub-mkconfig after chrooting into root_partition
        '''
        script_dir = os.path.realpath(os.path.dirname(__file__))
        chroot_script = os.path.join(
            script_dir, CHROOT_GRUB_MKCONFIG_SCRIPT)
        cmd = ' '.join([chroot_script, self.devpath, root_partition])
        sys.stderr.write('Executing: %s\n' % (cmd,))
        subprocess.call(cmd, shell=True)

    def make_bootable(self, root_partition, update_mbr=True):
        '''
        root_partition-->str: Path to root partition
        update_mbr-->bool: If False, grub-mbr is not installed to MBR
            EVEN if a BIOS partition is present

        Does not destroy partitions or other data
        Disk MUST have EFI partition. grub-efi files are installed to
            /EFI/BOOT on EFI partition
        IF disk has BIOS partition, grub-mbr is installed to MBR
        /boot/grub/grub.cfg on roto partition is updated using
            grub-mkconfig after chrooting into root_partition
        '''
        if not is_valid_partition(root_partition):
            raise ValueError('Not a partition: ' + root_partition)
        self.install_grub_efi(get_partition_uuid(root_partition))
        self.install_grub_mbr(root_partition)
        subprocess.call('partprobe', shell=True)
        self.rootfs_update_grub_config(root_partition)
