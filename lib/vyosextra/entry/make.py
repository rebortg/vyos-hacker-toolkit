#!/usr/bin/env python3

import sys
from datetime import datetime

from vyosextra import log
from vyosextra import cmd
from vyosextra import arguments
from vyosextra.config import config


LOCATION = 'packages'


class Command(cmd.Command):
	def make(self, where, target):
		self.ssh(where, config.docker(where, '', f'sudo make {target}'))

	def backdoor(self, where, password):
		build_repo = config.get(where,'repo')

		lines = config.read('vyos-iso-backdoor').split('\n')
		location = lines.pop(0).lstrip().lstrip('#').strip()

		if not password:
			self.ssh("build", f"rm {build_repo}/{location} || true")
			return

		data = ''.join(lines).format(user='admin', password=password)
		self.chain(
			config.printf(data),
			config.ssh(where, f'cat - > {build_repo}/{location}')
		)

	def configure(self, where, location,  extra, name):
		email = config.get('global','email')

		date = datetime.now().strftime('%Y%m%d%H%M')
		name = name if name else 'rolling'
		version = f'1.3-{name}-{date}'

		configure = f"--build-by {email}"
		configure += f" --debian-mirror http://ftp.de.debian.org/debian/"
		configure += f" --version {version}"
		configure += f" --build-type release"
		if extra:
			configure += f"  --custom-package '{extra}'"

		self.ssh(where, config.docker(where, '', 'pwd'))
		self.ssh(where, config.docker(where, '', f'./configure {configure}'))


def main(target=''):
	'call vyos-build make within docker'

	options = ['server', 'package', 'make', 'presentation']
	if not target:
		options = ['target'] + options

	args = arguments.setup(
		__doc__,
		options
	)

	if not target:
		target = args.target

	cmds = Command(args.show, args.verbose)

	if not config.exists(args.server):
		sys.exit(f'machine "{args.server}" is not configured')

	role = config.get(args.server, 'role')
	if role != 'build':
		sys.exit(f'target "{args.server}" is not a build machine')

	cmds.update_build(args.server)

	done = False
	for package in args.packages:
		done = cmds.build(args.server, LOCATION, package, args.location)

	if done or args.force:
		cmds.configure(args.server, LOCATION, args.extra, args.name)
		cmds.backdoor(args.server, args.backdoor)
		cmds.make(args.server, target)

	if target == 'iso' and args.test:
		cmds.make(args.server, 'test')

	log.completed(args.debug,'iso built and tested')


if __name__ == '__main__':
	main('iso')
