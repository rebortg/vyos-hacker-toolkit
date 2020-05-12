import os
import sys
import fcntl

from subprocess import Popen
from subprocess import PIPE
from subprocess import DEVNULL

from vyosextra import log


def _unprefix(string, prefix='Welcome to VyOS'):
    return '\n'.join(_ for _ in string.split('\n') if _ and _ != prefix)


def _report(popen, verbose):
    def _non_blocking(output):
        fd = output.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def _read(output):
        try:
            return output.read().decode()
        except Exception:
            return ""

    _non_blocking(popen.stdout)
    _non_blocking(popen.stderr)

    result = {1: '', 2: ''}

    standards = (
        (1, popen.stdout, sys.stdout, lambda _: _),
        (2, popen.stderr, sys.stderr, _unprefix),
    )
    while popen.poll() is None:
        for fno, pipe, std, formater in standards:
            recv = _read(pipe)
            if not recv:
                continue

            short = formater(recv)
            if not short:
                continue

            log.answer(short)
            result[fno] += short
            if verbose:
                std.write(short)

    return result.values()


def _check(code, exitonfail=True, verbose=True):
    if code and exitonfail:
        log.answer(f'returned code {code}')
        log.failed('could not complete action requested', verbose=verbose)


def chain(cmd1, cmd2, dry, verbose, ignore=''):
    command = f'{cmd1} | {cmd2}'
    log.command(command)
    if dry or verbose:
        print(command)
    if dry:
        return ''

    popen1 = Popen(cmd1, stdout=PIPE, stderr=DEVNULL, shell=True)
    popen2 = Popen(cmd2, stdin=popen1.stdout, stdout=PIPE, stderr=PIPE, shell=True)
    # run copopen2.communicate() before popen1.communicate()
    # otherwise there will be no data on the pipe!
    # as popen1.communicate will have taken it.
    _report(popen2, verbose)
    com1 = popen1.communicate()  # noqa: F841
    _check(popen1.returncode, verbose=verbose)
    _check(popen2.returncode, verbose=verbose)


def run(cmd, dry, verbose, ignore='', hide='', exitonfail=True):
    command = f'{cmd}'
    secret = command.replace(hide, '********') if hide else command
    log.command(secret)

    if dry or verbose:
        print(secret)
    if dry:
        return '', '', 0

    popen = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    out, err = _report(popen, verbose)
    code = popen.returncode
    _check(code, exitonfail, verbose=verbose)
    return out, err, code


def communicate(self, cmd, dry, verbose, ignore='', hide='', exitonfail=True):
    out, err, code = run(cmd, dry, verbose, ignore=ignore, hide=hide, exitonfail=exitonfail)

    _check(code, exitonfail=exitonfail, verbose=verbose)
    return _report(out, err), code
