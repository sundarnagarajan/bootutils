#!/usr/bin/env python
'''
1. Identify distro type

2. Based on distro:
    a. Identify kern_dir (containing kernel, initrd) LIST
    b. kernel regex
    c. initrd regex
    d. Identify squashfs_dir LIST
    e. squashfs_file regex

    c. Create LIST of ENTRIES. Each ENTRY has following attributes:
        entry_name
        variation - short text differentiating entry
        bit_size - indicates 32-bit or 64-bit if known
        efi - EFI or Non_EFI if known
        notes - whether it is known to (not) work etc
        remaster_info - from /remaster.txt if present
        kernel_ver
        kern_dir
        kern_file
        initrd_file
        kern_path
        initrd_path
        squashfs_file - can be used to remaster ISO
        distro_specific --> dict
            e.g. bootid for GRML


Identifying distro from an ISO:
    Ubuntu:
        Identified by /ubuntu dir in ISO
        vmlinuz, initrd under /casper
        info in /.disk/info
        Note: Ubuntu server ISOs are NOT live media - cannot be booted
        Grub_config: http://git.marmotte.net/git/glim/tree/grub2/inc-ubuntu.cfg
        menu entry:
            menuentry "Ubuntu 14.04 (LTS) Live Desktop amd64" --class ubuntu {
              # Variables set from outside
              set iso_dir="/iso"
              set isoname="ubuntu-14.04-desktop-amd64.iso"
              set kernel=vmlinuz.efi or vmlinuz

              echo "Using ${isoname}..."

              set isofile="${iso_dir}/${isoname}"
              loopback loop $isofile
              set kern_dir=(loop)/casper
              set vmlinuz=${kern_dir}/${kernel}
              set bootargs="boot=casper iso-scan/filename=${isofile}"
              set distargs=""
              set extra=""
              set optargs="quiet splash"
              linux "${vmlinuz} ${bootargs} ${distargs} ${extra} ${optargs}"
              initrd ${kern_dir}/initrd.lz
            }

    GRML:
        Identified by /GRML dir in ISO
            /conf/bootid.txt present (and required)
        vmlinuz, initrd under:
            grml32full: /boot/grml32full
            grml64full: /boot/grml64full
            grml96full: /boot/grml32full AND /boot/grml64full
            grml32small: /boot/grml32small
            grml64small: /boot/grml64small
            grml96small: /boot/grml32small AND /boot/grml64small
        No distro info available
        Grub_config: http://git.marmotte.net/git/glim/tree/grub2/inc-grml.cfg
        menu entry:
            menuentry "Grml 2014.03 64bit" --class grml {
              # Variables set from outside
              set iso_dir="/iso"
              set isoname="grml96-full_2014.03.iso"
              set bootid="XXXX" from /conf/bootid.txt
              set g_bits={32|64}
              set g_size={small|full}

              echo "Using ${isoname}..."

              set isofile="${iso_dir}/${isoname}"
              loopback loop $isofile
              set media_path=live-media-path=/live/grml${g_bits}-${g_size}
              set kern_dir=(loop)/boot/grml${g_bits}${g_size}
              set kernel=vmlinuz
              set vmlinuz=${kern_dir}/$kernel}
              set bootargs="boot=live findiso=${isofile}"
              set distargs="${media_path} bootid=${bootid}"
              set extra="apm=power-off nomce"
              set optargs=""
              linux ${vmlinuz} ${bootargs} ${distargs} ${extra} ${optargs}
              initrd ${kern_dir}/initrd.img
            }

    Knoppix:
        Identified by /KNOPPIX dir in ISO
        vmlinuz, initrd under /boot/isolinux
            32-bit kernel: /boot/isolinux/linux
            64-bit kernel: /boot/isolinux/linux64
            initrd: /boot/isolinux/minirt.gz
        info in /KNOPPIX/index_en.html - parse TITLE (top 10 lines)
        info in /boot/isolinux/boot.msg: line 4, field 1
            Returns something like 'KNOPPIX V7.6.1'
        Extract with : ' '.join(l[3].split(None)[:2])
        Reviewed v6.7 2011-09 CD and DVD
        Grub_config:
            http://git.marmotte.net/git/glim/tree/grub2/inc-knoppix.cfg
        menu entry:
            menuentry "Knoppix 7.2.0 CD" --class knoppix {
              # Variables set from outside
              set iso_dir="/iso"
              set isoname="KNOPPIX_V7.2.0CD-2013-06-16-EN.iso"

              echo "Using ${isoname}..."

              set isofile="${iso_dir}/${isoname}"
              loopback loop $isofile
              set kern_dir=(loop)/boot/isolinux
              set vmlinuz=${kern_dir}/linux
              set bootargs="bootfrom=/dev/sda1${isofile} ramdisk_size=100000"
              set distargs="libata.force=noncq hpsa.hpsa_allow_any=1"
              set extra="lang=en apm=power-off nomce loglevel=1 tz=localtime"
              set optargs=""
              linux "${vmlinuz} ${bootargs} ${distargs} ${extra} ${optargs}"
              initrd ${kern_dir}/minirt.gz
            }

    Debian
        Identified by /debian dir in ISO
        info in /.disk/info
        vmlinuz, initrd under /live
            vmlinuz=vmlinuz
            initrd=initrd.img
            extra_args="config"
            optargs="quiet splash"
        menu entry:
            menuentry "Debian Live 7.4 amd64 XFCE Desktop" --class debian {
              # Variables set from outside
              set iso_dir="/iso"
              set isoname="debian-live-7.4-amd64-xfce-desktop+nonfree.iso"

              echo "Using ${isoname}..."

              set isofile="${iso_dir}/${isoname}"
              loopback loop $isofile
              set kern_dir=(loop)/live
              set vmlinuz=${kern_dir}/vmlinuz
              set bootargs="boot=live findiso=${isofile} config"
              set distargs=""
              set extra=""
              set optargs="quiet splash"
              linux "${vmlinuz} ${bootargs} ${distargs} ${extra} ${optargs}"
              initrd ${kern_dir}/initrd.img
            }

    LinuxMint
        Identification:
            Ubuntu-derivative, but does NOT have /ubuntu dir
            /README.diskdefines file contains line looking like:
                #define DISKNAME  Linux Mint 18.1 "Serena" - Release amd64
            info in /.disk/info contains
                Linux Mint 18.1 "Serena" - Release amd64 20161213
            Look for info starting with 'Linux Mint'
        vmlinuz, initrd under /casper
        Rest like Ubuntu

    TinyCoreLinux
        Identification
            Debian-derivative, but does not have explicit dir /file
            Could look for /boot/tinycore.gz or /boot/microcore.gz
        vmlinuz, initrd under /boot
            vmlinuz=/boot/bzImage
            initrd=/boot/tinycore.gz or microcore.gz
            extra_args="quiet max_loop=256"
        menu entry:
            menuentry "TinyCoreLinux" --class debian {
              # Variables set from outside
              set iso_dir="/iso"
              set isoname="tinycore-current.iso"
              set initrd_gz={tiny|micro}core.gz

              echo "Using ${isoname}..."

              set isofile="${iso_dir}/${isoname}"
              loopback loop $isofile
              set kern_dir=(loop)/boot
              set vmlinuz=${kern_dir}/bzImage
              set bootargs=""
              set distargs=""
              set extra="quiet max_loop=256"
              set optargs=""
              linux "${vmlinuz} ${bootargs} ${distargs} ${extra} ${optargs}"
              initrd ${kern_dir}/${initrd_gz}
            }
    PuppyLinux
        Identification
            Debian-derivative, does not have dir /file to identify it
            Not even in /boot.msg / /help.msg / /README.HTM
            Look for /puppy_*.sfs
        vmlinuz, initrd under /
            vmlinuz=/vmlinuz
            initrd=/boot/initrd.gz
            extra_args="pmedia=cd"
        menu entry:
            menuentry "PuppyLinux" --class debian {
              # Variables set from outside
              set iso_dir="/iso"
              set isoname="tahr64-6.0.5.iso"

              echo "Using ${isoname}..."

              set isofile="${iso_dir}/${isoname}"
              loopback loop $isofile
              set kern_dir=(loop)/
              set vmlinuz=${kern_dir}/vmlinuz
              set bootargs=""
              set distargs=""
              set extra="pmedia=cd"
              set optargs=""
              linux "${vmlinuz} ${bootargs} ${distargs} ${extra} ${optargs}"
              initrd ${kern_dir}/initrd.gz
            }
'''
import os
import re
import subprocess
import isoparser


class ISOParserExt(object):
    '''
    uses and extends isoparser
    Encapsulates all usage of isoparser
    '''
    def __init__(self, iso_path):
        self.iso_path = iso_path
        self._iso = isoparser.parse(iso_path)

    @property
    def root(self):
        return self._iso.root

    @property
    def record(self):
        return self._iso.record

    def has_dirpath(self, p):
        '''
        p-->str: path
        Returns-->bool
        '''
        ret = False
        try:
            pl = [x for x in p.split('/') if x]
            r = self._iso.record(*pl)
            if r.is_directory:
                return True
        except:
            pass
        return ret

    def has_filepath(self, p):
        '''
        p-->str: path
        Returns-->bool
        '''
        ret = False
        try:
            pl = [x for x in p.split('/') if x]
            r = self._iso.record(*pl)
            if not r.is_directory:
                return True
        except:
            pass
        return ret

    def has_toplevel_dir(self, d):
        '''
        d-->str: name of dir to search for
        Returns-->bool
        '''
        l = self._iso.root.children
        l1 = [x for x in l if x.name == d and x.is_directory is True]
        if l1:
            return True
        return False

    def match_regex(self, d, r, is_dir=False):
        '''
        d-->str: directory path to search
        r-->str: regex
        is_dir-->bool
        Returns--list of str: filenames
        '''
        ret = []
        try:
            pl = [x for x in d.split('/') if x]
            fl = self._iso.record(*pl).children
            for n in [x.name for x in fl if x.is_directory is is_dir]:
                if re.match(r, n):
                    ret += [n]
        except:
            pass
        return ret


def get_distro(iso_path):
    '''
    iso_path-->str: path to ISO file
    Returns-->str: distro
    '''
    iso = ISOParserExt(iso_path)
    # First distros that have SPECIFIC identifiers
    # Distros identified by top-level dir

    # Ubuntu - symlink appears as file in isoparser
    if iso.has_filepath('/ubuntu'):
        return('ubuntu')
    # Debian - symlink appears as file in isoparser
    if iso.has_filepath('/debian'):
        return('debian')
    # GRML
    if iso.has_toplevel_dir('GRML'):
        return('grml')
    if iso.has_toplevel_dir('grml'):
        return('grml')
    # Knoppix
    if iso.has_toplevel_dir('KNOPPIX'):
        return('knoppix')

    # LinuxMint
    '''
    info in /.disk/info contains
        Linux Mint 18.1 "Serena" - Release amd64 20161213
    Look for info starting with 'Linux Mint'
    '''
    try:
        s = iso.record('.disk', 'info').content
        if s.startswith('Linux Mint'):
            return('linuxmint')
    except:
        pass

    # TinyCoreLinux
    '''
    Debian-derivative, but does not have identifying dir /file
    Look for /boot/tinycore.gz or /boot/microcore.gz
    '''
    r = '^(tinycore|microcore|corepure64).gz$'
    l = iso.match_regex('/boot', r, is_dir=False)
    if l:
        return('tinycore')

    # PuppyLinux
    '''
    Debian-derivative, does not have dir /file to identify it
    Not even in /boot.msg / /help.msg / /README.HTM
    Look for /puppy_*.sfs
    '''
    for x in iso.root.children:
        if x.is_directory:
            continue
        if x.name.startswith('puppy_') and x.name.endswith('.sfs'):
            return('puppy')

    # Generic
    return('generic')


def get_instance(iso_path):
    '''
    iso_path-->str: path to ISO file
    Returns-->Instance of LinuxISO
    '''
    cls_map = {
        'ubuntu': UbuntuISO,
        'debian': DebianISO,
        'grml': GRMLISO,
        'knoppix': KnoppixISO,
        'linuxmint': LinuxMintISO,
        'tinycore': TinyCoreISO,
        'puppy': PuppyISO,
        'generic': GenericLinuxISO
    }
    distro = get_distro(iso_path)
    if distro not in cls_map:
        distro = 'generic'
    return cls_map[distro](iso_path=iso_path, distro=distro)


class LinuxISO(object):
    '''
    Uses isoparser to identify the distro of a Linux ISO
    a. Identify kern_dir (containing kernel, initrd) LIST
    b. kernel regex
    c. initrd regex
    d. Identify squashfs_dir LIST
    e. squashfs_file regex

    c. Create LIST of ENTRIES. Each ENTRY has following attributes:
        entry_name
        variation - short text differentiating entry
        bit_size - indicates 32-bit or 64-bit if known
        efi - EFI or Non_EFI if known
        notes - whether it is known to (not) work etc
        remaster_info - from /remaster.txt if present
        kernel_ver
        kern_dir
        kern_file
        initrd_file
        kern_path
        initrd_path
        squashfs_file - can be used to remaster ISO
        distro_specific --> dict
            e.g. bootid for GRML
    Also identifies additional values from this ISO, like
        friendly name
        kernel, initrd lines
        dir containing kernel, initrd
        path (inside ISO) to squashfs
        warnings - known limitations for distro / distro variant
        distro-specific attributes:
            GRML:
                Additional kernel, initrd lines (for grml96)

    For each distribution I hope to support:
        Booting 32-bit or 64-bit ISO on 64-bit hardware
        Booting 32-bit ISO on 32-bit hardware
        Boot ISO whether or not ISO is intrinsically EFI-aware
        Boot on EFI and non-EFI machines
        Boot on EFI machines with 64-bit hardware and 32-bit EFI loader

    Distributions supported:
        - Ubuntu, official flavours
        - Unofficial Ubuntu flavours:
            - LinuxMint
        - Standard Debian - Jessie 8.0 stable tested
        - GRML - including combined 32-bit and 64-bit:
            - Daily builds work
            - Older builds work also

    Distros to be eventually targeted:
        Knoppix :
            Currently only tested OLD Knoppix
            Only works on non-EFI older machines
        Arch
        Fedora
        Gentoo
        Centos
        Red Hat
        Open Suse

        Manjaro (Arch-derivative)
        Antergos (Arch-derivative)
        Sabayon (Arch-derivative)
        KaliLinux (Debian-derivative)
        TailsOS (Debian-derivative)
        BackBox (Ubuntu-derivative)
        Parrot (Debian-derivative)
        Tinycore - only works on non-EFI older machines
        PuppyLinux
    '''
    KNOWN_DISTROS = [
        'ubuntu', 'debian', 'knoppix', 'grml', 'linuxmint',
        'tinycore', 'puppy', 'generic'
    ]

    def __init__(self, iso_path, distro='generic'):
        '''
        iso-->str: full path to ISO
        '''
        self.iso_path = iso_path
        self.distro = distro
        self._set_default_details()
        self.set_details()

    def _set_default_details(self):
        self.iso_dir = os.path.dirname(self.iso_path)
        self.iso_file = os.path.basename(self.iso_path)
        self._iso = ISOParserExt(self.iso_path)

        # Default values for attributes
        self.distro_type = 'unknown'
        self.distro_subtype = 'unknown'
        self.friendly_name = self.iso_file
        self.remaster_info = ''
        self.remaster_time = ''
        try:
            self.remaster_info = self._iso.record(
                'remaster', 'remaster.txt').content.splitlines()[0]
        except:
            pass
        try:
            self.remaster_time = self._iso.record(
                'remaster', 'remaster.time').content.splitlines()[0]
        except:
            pass
        self.volid = ''
        try:
            cmd = 'isoinfo -d -i "%s"' % (self.iso_path,)
            l = subprocess.check_output(cmd, shell=True).splitlines()
            l = [x for x in l if x.startswith('Volume id: ')]
            if l:
                l = l[0]
                self.volid = l.split(':')[1].strip()
        except:
            pass
        if self.remaster_time and self.volid:
            self.friendly_name = 'Remastered [%s] %s' % (
                self.remaster_time, self.volid)
        elif self.volid:
            self.friendly_name = self.volid
        self.bootid = ''
        try:
            self.grub_cfg = self._iso.record(
                'boot', 'grub', 'grub.cfg').content
        except:
            self.grub_cfg = ''

    def set_details(self):
        pass


class DebianISO(LinuxISO):
    def set_details(self):
        self.distro_type = 'Debian'
        self.distro_subtype = ''
        self.distinfo = self.get_distinfo()

    def get_distinfo(self):
        '''
        Returns-->str: distribution info
        '''
        ret = ''
        try:
            ret += self._iso.record(
                '.disk', 'info').content.splitlines()[0]
        except:
            pass
        return ret


class UbuntuISO(DebianISO):
    def set_details(self):
        DebianISO.set_details(self)
        self.distro_subtype = 'Ubuntu'


class GRMLISO(DebianISO):
    def get_distinfo(self):
        '''
        Returns-->str: distribution info
        '''
        pat = '^grml(?P<BITS>\d{2})(?P<SIZE>.*)$'
        l = self._iso.record('boot').children
        ret = 'GRML '
        for f in l:
            m = re.match(pat, f.name)
            if not m:
                continue
            ret += ', %s-bit %s' % (
                m.groupdict()['BITS'],
                m.groupdict()['SIZE']
            )
        return ret

    def set_details(self):
        DebianISO.set_details(self)
        self.distro_subtype = 'GRML'
        try:
            self.bootid = self._iso.record(
                'conf', 'bootid.txt').content.splitlines()[0]
        except:
            self.bootid = ''


class KnoppixISO(DebianISO):
    def get_distinfo(self):
        '''
        Returns-->str: distribution info
        '''
        ret = ''
        l = []
        try:
            l = self._iso.record(
                'boot', 'isolinux', 'boot.msg').content.splitlines()
        except:
            pass
        try:
            kl = [x for x in l if x.strip().startswith('KNOPPIX')]
            kl = [x.strip() for x in kl]
            if kl:
                kl = kl[0]
            kl_fields = kl.split(None, 4)
            add_fn = ' '.join([
                kl_fields[0], kl_fields[1],
                kl_fields[3], kl_fields[4]])
            ret += add_fn
            return ret
        except:
            pass
        try:
            ret += ' '.join(l[3].split(None)[:2])
            return ret
        except:
            pass
        return ret


class LinuxMintISO(UbuntuISO):
    pass


class TinyCoreISO(DebianISO):
    def get_distinfo(self):
        '''
        Returns-->str: distribution info
        '''
        ver_map = {
            'tinycore.gz': 'Regular',
            'microcore.gz': 'Micro',
            'corepure64.gz': '64-bit'
        }
        r = '^(tinycore|microcore|corepure64).gz$'
        fn = ''
        try:
            fn = self._iso.match_regex('/boot', r, is_dir=False)[0]
        except:
            pass
        return ver_map.get(fn, 'Unknown')


class PuppyISO(DebianISO):
    def get_distinfo(self):
        '''
        Returns-->str: distribution info
        '''
        ret = ''
        '''
        Debian-derivative, does not have dir /file to identify it
        Not even in /boot.msg / /help.msg / /README.HTM
        No info available
        '''
        return ret


class GenericLinuxISO(LinuxISO):
    pass


if __name__ == '__main__':
    iso_base = '/mnt/auto/iso'
    l = [
        'linuxmint/linuxmint-18.1-cinnamon-64bit.iso',
        'tinycorelinux/CorePure64-8.0.iso',
        'tinycorelinux/microcore-current.iso',
        'grml/grml32-full_2014.03.iso',
        'grml/grml32-small_2014.11.iso',
        'grml/grml96-full_2014.11.iso',
        'grml/grml96-small_2014.11.iso',
        'grml/grml64-full_2014.03.iso',
        'grml/grml64-small_2014.11.iso',
        'ubuntu/xenial-16.04/ubuntu-mate-16.04.1-desktop-i386.iso',
        'ubuntu/xenial-16.04/lubuntu-16.04.1-desktop-i386.iso',
        'ubuntu/xenial-16.04/ubuntu-mate-16.04.1-desktop-amd64.iso',
        'ubuntu/xenial-16.04/ubuntu-16.04.1-server-i386.iso',
        'ubuntu/xenial-16.04/ubuntu-16.04.1-server-amd64.iso',
        'ubuntu/trusty-14.04/ubuntu-14.04.1-desktop-amd64.iso',
        'ubuntu/trusty-14.04/ubuntu-14.04.1-server-amd64.iso',
        'ubuntu/trusty-14.04/ubuntu-14.04-server-amd64+mac.iso',
        'ubuntu/trusty-14.04/ubuntu-14.04.3-server-i386.iso',
        'debian/debian-live-8.7.1-amd64-xfce-desktop.iso',
        'puppylinux/tahr64-6.0.5.iso',
        'knoppix/KNOPPIX_V6.7.1CD-2011-09-14-EN.iso',
        'knoppix/KNOPPIX_V7.6.1DVD-2016-01-16-EN.iso',
    ]
    for fp in l:
        iso_path = os.path.join(iso_base, fp)
        if not os.path.isfile(iso_path):
            continue
        c = get_instance(iso_path)
        print('%s:' % (os.path.basename(iso_path), ))
        print('    Distro: %s' % (c.distro,))
        print('    Friendly name: %s' % (c.friendly_name,))
        print('    Remaster info: %s' % (c.remaster_info,))
        print('    VolID: %s' % (c.volid,))
        try:
            print('    BootID: %s' % (c.bootid,))
        except:
            pass
