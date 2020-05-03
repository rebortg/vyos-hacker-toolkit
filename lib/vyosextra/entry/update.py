#!/usr/bin/env python3
# encoding: utf-8

import sys

from vyosextra import log
from vyosextra import control
from vyosextra import arguments

from vyosextra.repository import InRepo
from vyosextra.config import config


class Control(control.Control):
	def copy(self, where, repo, folder):
		with InRepo(folder) as debian:
			for src, dst in self.move:
				self.ssh(where, f'sudo chgrp -R vyattacfg {dst}')
				self.ssh(where, f'sudo chmod -R g+rxw {dst}')
				self.scp(where, src, dst)


def main():
	'update a VyOS router filesystem with newer vyos-1x code'
	arg = arguments.setup(
		__doc__,
		['router', 'package', 'presentation']
	)
	control = Control(arg.show, arg.verbose)

	if not config.exists(arg.router):
		sys.stderr.write(f'machine "{arg.router}" is not configured\n')
		sys.exit(1)

	role = config.get(arg.router, 'role')
	if role != 'router':
		sys.stderr.write(f'target "{arg.router}" is not a VyOS router\n')
		sys.exit(1)

	control.copy(arg.router, arg.package, option)
	log.completed('router updated')
	

if __name__ == '__main__':
	main()
