#!/usr/bin/env python3
"""Reject new commits and pushes that do not use the configured Vapor identity."""
import re
import subprocess
import sys


def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()


def guard():
    remote = git('config', '--local', '--get', 'letsolo.remote')
    if not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git', remote):
        raise ValueError('Unexpected repository')
    name = git('config', '--local', '--get', 'letsolo.botName')
    email = git('config', '--local', '--get', 'letsolo.botEmail')
    if name != 'letsolo-vapor[bot]' or not re.fullmatch(r'[0-9]+\+letsolo-vapor\[bot\]@users\.noreply\.github\.com', email):
        raise ValueError('Expected Vapor identity')
    expected = f'{name} <{email}>'
    for variable in ('GIT_AUTHOR_IDENT', 'GIT_COMMITTER_IDENT'):
        if not git('var', variable).startswith(expected + ' '):
            raise ValueError('Wrong author or committer')
    if len(sys.argv) > 1:
        if len(sys.argv) != 3 or sys.argv[1] != 'origin' or sys.argv[2] != remote:
            raise ValueError('Wrong push destination')
        for line in sys.stdin:
            _local_ref, local_sha, _remote_ref, remote_sha = line.split()
            if not local_sha.strip('0'):
                continue
            revisions = [f'{remote_sha}..{local_sha}'] if remote_sha.strip('0') else [local_sha, '--not', '--remotes=origin']
            for sha in git('rev-list', *revisions).splitlines():
                if git('show', '-s', '--format=%an <%ae>%n%cn <%ce>', sha).splitlines() != [expected, expected]:
                    raise ValueError('A new commit is not authored and committed by Vapor')


if __name__ == '__main__':
    try:
        guard()
    except (OSError, ValueError, subprocess.SubprocessError):
        print('Blocked: new commits, author, committer, and destination must match the configured Vapor identity.', file=sys.stderr)
        raise SystemExit(1)
