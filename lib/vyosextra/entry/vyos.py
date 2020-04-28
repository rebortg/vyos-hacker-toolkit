#!/usr/bin/env python3
# encoding: utf-8

import sys

from vyosextra.entry.update import update
from vyosextra.entry.dpkg import dpkg
from vyosextra.entry.make import make
from vyosextra.entry.test import test

def help():
	print(f"""\
usage: vyos [-h] COMMAND [COMMAND options]

helper functions for vyos, OPTIONS are:
  update                update a VyOS router with vyos-1x
  dpkg                  build a VyOS package (vyos-1x, ...)
  iso                   build a VyOS iso image
  test                  test a VyOS router

optional arguments:
  -h, --help            show this help message and exit
""")
	sys.exit(0)


def vyos():
	usage = len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help', 'help')

	if usage:
		help()

	command = sys.argv[1]
	sys.argv = [f'{sys.argv[0]}-{command}'] + sys.argv[2:]

	if len(sys.argv) == 1:
		sys.argv.append('-h')

	if command == 'update':
		update()
		return

	if command == 'dpkg':
		dpkg()
		return

	if command in ('iso',):
		make(command)
		return

	if command == 'test':
		test()
		return

	help()


if __name__ == '__main__':
	vyos()
