#!/usr/bin/env python
'''
Utility classes and methods related to building a multiboot
drive that can boot different ISOs

These methods and classes do not make the drive bootable - neither
in EFI nor MBR mode. They only help in creating the grub config

Features that are NOT and probably will not be supported:
    - Create menu entries for 'Try without installing' and 'Install'
        for each ISO. The menu entry created is similar to 'Try without
        installing'. All Live CDs I have seen have a way to enter the
        installer from within the 'Try without installing' environment

    - Create other menu entries that the original ISO had - e.g.
        'Recovery mode', 'memtest' etc

    - Recreate ALL the menu entries that the original ISO had.
        So far it doesn't seem easy, since some use ISOLINUX and not
        grub. Some use legacy grub etc.

    - Extensibility API for creating booot entry based on distro
        The code could be extended, but there is no 'plugin' mechanism

    - Support for themes, icons etc

References:
    http://git.marmotte.net/git/glim/tree/grub2

'''
import os
import re
from linuxiso import get_instance


class ISOBootEntry(object):
    '''
    References: http://git.marmotte.net/git/glim/tree/grub2
    '''
    def __init__(self, iso_file, iso_dir):
        '''
        iso_file-->str: full path to ISO file
        iso_dir-->str: full path of dir containing ISO ON BOOT DRIVE
            e.g. /iso
        '''
        self.iso_file = iso_file
        self.iso_dir = iso_dir
        self.iso = get_instance(self.iso_file)
        self.iso_path_in_drive = os.path.join(
            self.iso_dir, os.path.basename(self.iso_file))
        self.common = '''
    set isofile="%s"
    export isofile
    loopback loop $isofile
    set root=(loop)
''' % (self.iso_path_in_drive,)
        self.menuentry_template = '''
menuentry "%s" {
    %s
    %s
}
'''

    @property
    def ubuntu_menu(self):
        menu_pat = '^menuentry .*?{$.*?^}'
        grubcfg = self.iso.grub_cfg
        submenu_entries = []
        offset = 0
        match = re.search(menu_pat, grubcfg[offset:], re.MULTILINE + re.DOTALL)
        while match:
            menu1 = grubcfg[(offset + match.start()):(offset + match.end())]
            menu_lines = []

            for l in menu1.splitlines():
                if not l.strip().startswith('linux'):
                    menu_lines.append(l)
                    continue
                # linux line
                l_comps = l.strip().split()
                l_comps.insert(-1, "iso-scan/filename=${isofile}")
                new_l = ' '.join(l_comps)
                menu_lines.append(new_l)

            submenu_entries.append('\n        '.join(menu_lines))
            offset += match.end()
            match = re.search(
                menu_pat, grubcfg[offset:], re.MULTILINE + re.DOTALL)

        submenu_template = '''
submenu "%s" {
    %s
    %s
}
'''
        return submenu_template % (
            self.iso.friendly_name,
            self.common,
            '\n'.join(submenu_entries)
        )

    @property
    def grml_menu(self):
        ending = '''
    set bootid="%s"
    export bootid
    set kernelopts="findiso=${isofile}"
    export kernelopts
    source /boot/grub/grub.cfg
''' % (self.iso.bootid)

        submenu_template = '''
submenu "%s" {
    %s
    %s
}
'''
        return submenu_template % (
            self.iso.friendly_name,
            self.common,
            ending
        )

    @property
    def debian_menu(self):
        ending = '''
    set gfxpayload=keep
    linux /live/vmlinuz boot=live components findiso=$isofile noeject quiet splash
    initrd /live/initrd.img
'''
        return self.menuentry_template % (
            self.iso.friendly_name,
            self.common,
            ending
        )

    @property
    def unknown_distro_menu(self):
        ending = '''
echo "Do not know how to handle this type of distribution"
echo "Distro: %s"
read a
''' % (self.iso.distro,)
        return self.menuentry_template % (
            self.iso.friendly_name,
            self.common,
            ending
        )

    @property
    def menuentry(self):
        if self.iso.distro == 'ubuntu':
            return self.ubuntu_menu
        elif self.iso.distro == 'linuxmint':
            return self.ubuntu_menu
        elif self.iso.distro == 'grml':
            return self.grml_menu
        elif self.iso.distro == 'debian':
            return self.debian_menu
        else:    # distros we don't know how to handle
            return self.unknown_distro_menu


class GrubMenu(object):
    '''
    Notes:
    grub menuentry --class option:
        See https://www.gnu.org/software/grub/manual/html_node/menuentry.html

        From http://unix.stackexchange.com/a/163989
            The boot menu where GRUB displays the menu entries from the
            grub.cfg file. It is a list of items, where each item has a
            title and an optional icon. The icon is selected based on the
            classes specified for the menu entry. If there is a PNG file
            named myclass.png in the grub/themes/icons directory, it will
            be displayed for items which have the class myclass. The boot
            menu can be customized in several ways, such as the font and
            color used for the menu entry title, and by specifying styled
            boxes for the menu itself and for the selected item highlight.

        Not really usual in the usage context of this module
        We try to generate the right --class line, but it (probably) will not
        have any effect, since we do not generate or include themes

    '''

    def __init__(self, cfg_file=None, iso_dir='.'):
        '''
        cfg_file-->str: If set, write() will write to this file
            If not set write() will output on STDOUT
        iso_dir-->str: Path to directory with ISO files
            filenames MUST end in .iso or .ISO
        '''
        (self.cfg_file, self.iso_dir) = (cfg_file, iso_dir)

    def get_iso_files(self):
        l = []
        try:
            l = os.listdir(self.iso_dir)
        except:
            return l
        l = [os.path.join(self.iso_dir, x) for x in l]
        l = [x for x in l if os.path.isfile(x)]
        l = [x for x in l if x.endswith('iso') or x.endswith('ISO')]
        l.sort()
        return l

    @property
    def menu(self):
        ml = []
        # Modules we need
        ml += ['''
# ------------------------------------------------------------------------
# grub.cfg generated by multiboot.GrubMenu
# ------------------------------------------------------------------------

insmod part_gpt

function load_video {
  # To avoid errors that look like:
  # no suitable video mode found; booting in blind mode
  terminal_input console
  terminal_output console

  if [ x$feature_all_video_module = xy ]; then
    insmod all_video
  else
    insmod efi_gop
    insmod efi_uga
    insmod ieee1275_fb
    insmod vbe
    insmod vga
    insmod video_bochs
    insmod video_cirrus
  fi
}

load_video
''']

        for iso in self.get_iso_files():
            be = ISOBootEntry(iso, '/iso')
            ml += [be.menuentry]
        ml += ['''

menuentry 'System setup - EFI only' {
    fwsetup
}

menuentry "Power down - may not always work" {
    halt
}
''']

        return ''.join(ml)

    def write(self):
        m = self.menu
        print(m)
        if self.cfg_file:
            with open(self.cfg_file, 'w') as f:
                f.write(m)
                f.flush()
        else:
            print(m)
