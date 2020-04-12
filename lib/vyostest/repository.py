import os
import re
from datetime import datetime

from . import log
from . import cmd
from .cmd import run
from .cmd import chain
from .cmd import check

move = [
    ('python/vyos/*', '/usr/lib/python3/dist-packages/vyos/'),
    ('src/conf_mode/*', '/usr/libexec/vyos/conf_mode/'),
    ('src/op_mode/*', '/usr/libexec/vyos/op_mode/'),
]

class InRepo:
	def __init__(self, folder):
		self.folder = folder
		self.pwd = os.getcwd()

	def __enter__(self):
		try:
			os.chdir(self.folder)
			self.folder = os.path.basename(os.getcwd())
			return self
		except Exception as e:
			log.failed(f'could not get into the repositoy {self.folder}\n{str(e)}')

	def __exit__(self, rtype, rvalue, rtb):
		os.chdir(self.pwd)

	def package(self, repo):
		with open(os.path.join('debian', 'changelog')) as f:
			line = f.readline().strip()
		found = re.match('[^(]+\((.*)\).*', line)
		if found is None:
			return ''
		version = found.group(1)
		return f'{repo}_{version}_all.deb'


def update(conf, vyos_build):
	check(*run(
		conf.ssh('build', f'cd {vyos_build} && git pull'),
		'Already up to date.'
	))


def build(conf, vyos_build, location, repo, folder):
	check(*run(conf.ssh('build', f'mkdir -p {vyos_build}/{location}/{repo}')))

	with InRepo(folder) as debian:
		package = debian.package(repo)
		if not package:
			log.failed(f'could not find {repo} package version')
		elif not cmd.DRY:
			log.report(f'building package {package}')

		check(*run(conf.rsync('.', f'{vyos_build}/{location}/{repo}')))
		check(*run(conf.ssh('build', f'rm {vyos_build}/{location}/{package} || true')))
		check(*run(conf.ssh('build', conf.docker(f'{location}/{repo}', 'dpkg-buildpackage -uc -us -tc -b'))))

	return True


def install(conf, vyos_build, location, repo, folder):
	with InRepo(folder) as debian:
		package = debian.package(repo)
		if not package:
			log.failed(f'could not find {repo} package name')
		if not cmd.DRY:
			log.report(f'installing {package}')

	check(*chain(
		conf.ssh('build', f'cat {vyos_build}/{location}/{package}'),
		conf.ssh('router', f'cat - > {package}')
	))
	check(*run(conf.ssh('router', f'sudo dpkg -i --force-all {package}')))
	check(*run(conf.ssh('router', f'rm {package}')))
	return True


def setup(conf):
	# on my local VM which goes to sleep when I close my laptop
	# time can easily get out of sync, which prevent apt to work
	now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	check(*run(conf.ssh('router', f"sudo date -s '{now}'")))

	check(*run(conf.ssh('router', f'sudo chgrp vyattacfg /etc/apt/sources.list')))
	check(*run(conf.ssh('router', f'sudo chmod g+rw /etc/apt/sources.list')))

	data = ''.join(conf.readlines('source.list'))
	check(*chain(
		conf.printf(data),
		conf.ssh('router', f'cat - > /etc/apt/sources.list')
	))

	check(*run(conf.ssh('router', f'sudo apt-get --yes update')))
	check(*run(conf.ssh('router', f'sudo apt-get --yes upgrade')))
	check(*run(conf.ssh('router', f'sudo apt-get --yes install vim git')))

	check(*run(conf.ssh('router', f'ln -s /usr/lib/python3/dist-packages/vyos vyos')))
	check(*run(conf.ssh('router', f'ln -s /usr/libexec/vyos/conf_mode conf')))
	check(*run(conf.ssh('router', f'ln -s /usr/libexec/vyos/op_mode op')))

	for src, dst in move:
		check(*run(conf.ssh('router', f'sudo chgrp -R vyattacfg {dst}')))
		check(*run(conf.ssh('router', f'sudo chmod -R g+rxw {dst}')))

	return True


def copy(conf, vyos_build, location, repo, folder):
	with InRepo(folder) as debian:
		for src, dst in move:
			check(*run(conf.scp('router', src, dst)))

	return True

def backdoor(conf, vyos_build, password):
	lines = conf.readlines('vyos-iso-backdoor')
	location = lines.pop(0).lstrip().lstrip('#').strip()

	if not password:
		check(*run(conf.ssh("build", f"rm {vyos_build}/{location} || true")))
		return

	data = ''.join(lines).format(user='admin', password=password)
	check(*chain(
		conf.printf(data),
		conf.ssh('build', f'cat - > {vyos_build}/{location}')
	))


def configure(conf, vyos_build, location, email, extra, name):
	date = datetime.now().strftime('%Y%m%d%H%M')
	name = name if name else 'rolling'
	version = f'1.3-{name}-{date}'

	configure = f"--build-by {email}"
	configure += f" --debian-mirror http://ftp.de.debian.org/debian/"
	configure += f" --version {version}"
	configure += f" --build-type release"
	if extra:
		configure += f"  --custom-package '{extra}'"

	check(*run(conf.ssh('build', conf.docker('', 'pwd'))))
	check(*run(conf.ssh('build', conf.docker('', f'./configure {configure}'))))


def make(conf, target):
	check(*run(conf.ssh('build', conf.docker('', f'sudo make {target}'))))
