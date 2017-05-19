#!/usr/bin/env python
import sys
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
    if len(sys.argv) < 2:
        exit(0)

    iso_path = sys.argv[1]
    if not os.path.isfile(iso_path):
        sys.stderr.write('Not found: %s\n' % (sys.argv[1],))
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
