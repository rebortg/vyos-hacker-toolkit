#!/usr/bin/env python3

import os
import sys
import subprocess

from vyosextra import log
from vyosextra import cmd
from vyosextra import arguments


LOCATION = 'packages'


class Command(cmd.Command):
	pass


def ssh():
	args = arguments.setup(
		'ssh to a machine',
		['machine', 'presentation']
	)
	cmds = Command(args.show, args.verbose)

	if not cmds.config.exists(args.machine):
		sys.stderr.write(f'machine "{args.machine}" is not configured\n')
		sys.exit(1)

	connect = cmds.config.ssh(args.machine, '')

	if args.show or args.verbose:
		print(connect)
	
	if args.show:
		return

	print(f'connecting to {args.machine}')
	fullssh = subprocess.check_output(['which','ssh']).decode().strip()
	os.execvp(fullssh,connect.split())
	log.completed(args.debug, 'session terminated')


if __name__ == '__main__':
	ssh()
