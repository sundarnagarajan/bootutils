#!/usr/bin/env python

import sys
import subprocess
import os
import re
import tempfile
import shutil
import time

if sys.version_info[0] == 2:
    input = raw_input           # noqa F821


class MountedDir(object):
    def __init__(self, src, dest, opts='', ignore_umount_err=True):
        '''
        src-->str: Path to device to mount
        dest-->str: Mount point (dir)
        opts-->str: Mount options
        ignore_umount_err-->bool: Ignore exceptions while unmounting
        '''
        if os.geteuid() != 0:
            raise RuntimeError('Must be root to mount, umount')
        '''
        if not os.path.exists(src):
            raise ValueError('Device does not exist: %s' % (src,))
        '''
        if not os.path.isdir(dest):
            raise ValueError('Mountpoint is not a directory: %s' % (dest,))

        (self.src, self.dest, self.opts) = (src, dest, opts)
        self.ignore_umount_err = ignore_umount_err

    def __enter__(self):
        if self.opts:
            cmd = 'mount %s %s %s' % (self.opts, self.src, self.dest)
        else:
            cmd = 'mount %s %s' % (self.src, self.dest)
        sys.stderr.write('MountedDir: Executing: %s\n' % (cmd,))
        subprocess.check_call(cmd, shell=True)
        time.sleep(1)
        return self.dest

    def __exit__(self, *args):
        cmd = 'umount %s' % (self.dest,)
        sys.stderr.write('MountedDir: Executing: %s\n' % (cmd,))
        try:
            subprocess.check_call(cmd, shell=True)
            time.sleep(1)
        except:
            if not self.ignore_umount_err:
                raise


class MountedDirTemp(MountedDir):
    def __init__(self, src, parent_dir, opts='', ignore_umount_err=True):
        '''
        src-->str: Path to device to mount
        parent_dir-->str: Dir to create temp mount dir in
        opts-->str: Mount options
        ignore_umount_err-->bool: Ignore exceptions while unmounting
        '''
        dest = tempfile.mkdtemp(dir=parent_dir, prefix='tmp_MountedDir_')
        MountedDir.__init__(
            self,
            src=src,
            dest=dest,
            opts=opts,
            ignore_umount_err=ignore_umount_err
        )

    def __enter__(self):
        try:
            return MountedDir.__enter__(self)
        except:
            shutil.rmtree(self.dest, ignore_errors=True)
            raise

    def __exit__(self, *args):
        MountedDir.__exit__(self, *args)
        shutil.rmtree(self.dest, ignore_errors=True)


class TempDir(object):
    def __init__(self, parent_dir):
        '''
        parent_dir-->str: Dir to create temp dir in
        '''
        self.parent_dir = os.path.realpath(parent_dir)

    def __enter__(self):
        self.dest = tempfile.mkdtemp(
            dir=self.parent_dir, prefix='tmp_TempDir_')
        return self.dest

    def __exit__(self, *args):
        shutil.rmtree(self.dest, ignore_errors=True)


def require_root_or_exit():
    if os.geteuid() != 0:
        sys.stderr.write('This program needs to be run as root\n')
        exit(1)


def highlight_str(s):
    '''
    s-->str
    Returns-->str: s highlighed in inverse video
    '''
    reset = '\033[0m'
    inv = '\033[7m'
    fmt = inv + '%s' + reset
    return fmt % (s,)


class LineWithComments(object):
    def __init__(self, l='', comment_char='#'):
        '''
        l-->str
        '''
        if len(comment_char) > 0:
            comment_char = comment_char[0]
        else:
            comment_char = '#'
        self.comment_char = comment_char
        self.parse(l)

    def parse(self, l):
        '''
        l-->str
        Returns-->Nothing. Sets lspace, nc, rspace, comm
        '''
        self.ls = ''
        self.nc = ''
        self.rs = ''
        self.comm = ''

        # Only white space
        spat = '^\s*$'
        m = re.search(spat, l)
        if m:
            self.ls = l
            return
        # Something more than leading white space
        lspat = '^(?P<LSPACE>\s*)(?P<REST>\S.*)$'
        m = re.search(lspat, l)
        if not m:
            return
        (self.ls, rest) = (m.groupdict()['LSPACE'], m.groupdict()['REST'])
        if self.comment_char in rest:
            tcpat = '(?P<NC>[^%s]*?)(?P<RSPACE>\s*)(?P<COMM>%s.*)$'
            tcpat = tcpat % (self.comment_char, self.comment_char)
            m = re.search(tcpat, rest)
            if m:
                (self.nc, self.rs, self.comm) = (
                    m.groupdict()['NC'],
                    m.groupdict()['RSPACE'],
                    m.groupdict()['COMM'],
                )
        else:   # No comment
            self.nc = rest

    @property
    def line(self):
        return ''.join([self.ls, self.nc, self.rs, self.comm])

    def __str__(self):
        return self.line

    @classmethod
    def test(self):
        '''
        Only a self-test method, can be safely deleted
        '''
        comment_char = '#'
        ls_list = ['', '    ']
        nc_list = ['', 'VAR1=value']
        rs_list = ['', '    ']
        comm_list = ['', '# This is a comment']

        fmt = '%-8s %-8s %-8s %-8s %-8s'
        print(fmt % ('LS', 'NC', 'RS', 'COMM', 'Result'))

        for ls in ls_list:
            for nc in nc_list:
                for rs in rs_list:
                    for comm in comm_list:

                        l = ''.join([ls, nc, rs, comm])
                        c = LineWithComments(l, comment_char=comment_char)
                        l1 = c.line
                        print(fmt % (
                            str(bool(ls)),
                            str(bool(nc)),
                            str(bool(rs)),
                            str(bool(comm)),
                            str(l1 == l),
                        ))
