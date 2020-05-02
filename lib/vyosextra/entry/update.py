#!/usr/bin/env python3

import sys

from vyosextra import log
from vyosextra import cmd
from vyosextra import arguments

from vyosextra.repository import InRepo


LOCATION = 'compiled'


class Command(cmd.Command):
	def copy(self, where, location, repo, folder):
		with InRepo(folder) as debian:
			for src, dst in self.move:
				self.ssh(where, f'sudo chgrp -R vyattacfg {dst}')
				self.ssh(where, f'sudo chmod -R g+rxw {dst}')
				self.scp(where, src, dst)


def update():
	args = arguments.setup(
		'build and install a vyos debian package',
		['router', 'package', 'presentation']
	)
	cmds = Command(args.show, args.verbose)

	if not cmds.config.exists(args.router):
		sys.stderr.write(f'machine "{args.router}" is not configured\n')
		sys.exit(1)

	role = cmds.config.get(args.router, 'role')
	if role != 'router':
		sys.stderr.write(f'target "{args.router}" is not a VyOS router\n')
		sys.exit(1)

	cmds.copy(args.router, LOCATION, args.package, option)

	log.completed(args.debug, 'router updated')
	

if __name__ == '__main__':
	update()
