#!/usr/bin/env python3
# encoding: utf-8

import os
import sys
import argparse

from vyosextra import log
from vyosextra.entry import register


def make_sys(extract=0, help=True):
    prog = sys.argv[0]
    cmd = sys.argv[1]
    sys.argv = sys.argv[1:]

    if extract and len(sys.argv) >= extract:
        extracted = sys.argv[:extract]
        sys.argv = sys.argv[extract:]
    else:
        extracted = []

    sys.argv = [f'{prog} {cmd}'] + sys.argv[1:]

    if help and len(sys.argv) == 1:
        sys.argv.append('-h')

    return extracted


def main():
    if os.environ.get('VYOSEXTRA_DEBUG', None) is not None:
        def intercept(dtype, value, trace):
            try:
                log.failed('report:')
            except Exception:
                pass
            import traceback
            traceback.print_exception(dtype, value, trace)
            import pdb
            pdb.pm()
        sys.excepthook = intercept

    choices = register.registered()
    choices.sort()
    epilog = '\n'.join([f'   {c:<20} {register.doc(c)}' for c in choices])

    parser = argparse.ArgumentParser(
        description='vyos extra, the developer tool',
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'command options:\n{epilog}')
    parser.add_argument(
        '-h', '--help',
        help='show this help message and exit',
        action='store_true')
    parser.add_argument(
        'command',
        help='command to run',
        nargs='?',
        choices=choices)

    arg, _ = parser.parse_known_args()

    if not arg.command and arg.help:
        parser.print_help()
        return

    helping = {
        'build': False,
        'download': False,
    }

    if arg.command not in choices:
        parser.print_help()
        return

    make_sys(help=helping.get(arg.command, True))
    register.call(arg.command)


if __name__ == '__main__':
    main()
