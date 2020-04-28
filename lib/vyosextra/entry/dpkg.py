#!/usr/bin/env python3

import argparse

from vyosextra import log
from vyosextra import cmd
from vyosextra import config
from vyosextra import repository

HOME = '/home/vyos'
LOCATION = 'compiled'

def dpkg():
	parser = argparse.ArgumentParser(description='build and install a vyos debian package')
	parser.add_argument('-1', '--vyos', type=str, help='vyos-1x folder to build')
	parser.add_argument('-k', '--smoke', type=str, help="vyos-smoke folder to build")
	parser.add_argument('-c', '--cfg', type=str, help="vyatta-cfg-system folder to build")
	parser.add_argument('-o', '--op', type=str, help="vyatta-op folder to build")

	parser.add_argument('-7', '--setup', help='setup for use by this program', action='store_true')
	parser.add_argument('-s', '--show', help='only show what will be done', action='store_true')
	parser.add_argument('-v', '--verbose', help='show what is happening', action='store_true')
	parser.add_argument('-d', '--debug', help='provide debug information', action='store_true')

	args = parser.parse_args()
	cmd.DRY = args.show
	cmd.VERBOSE = args.verbose

	cmds = cmd.Command(HOME)

	todo = {
		('vyos-1x', args.vyos),
		('vyos-smoketest', args.smoke),
		('vyatta-cfg-system', args.cfg),
		('vyatta-op', args.op)
	}

	if args.setup:
		cmds.setup_router()

	cmds.update_build()
	for package, option in todo:
		if option:
			cmds.build(LOCATION, package, option)
			cmds.install(LOCATION, package, option)

	log.completed(args.debug, 'package(s) installed')


if __name__ == '__main__':
	dpkg()
