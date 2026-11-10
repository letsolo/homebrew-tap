#!/usr/bin/env python3
"""Use a repository-scoped Vapor installation token; never use personal credentials."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OWNER = 'letsolo'
REPOSITORIES = ('lbv', 'homebrew-tap', 'github-workflows', 'windows', 'android')


def api(path, token, data=None):
    request = Request('https://api.github.com' + path,
                      data=None if data is None else json.dumps(data).encode(),
                      headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                               'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'letsolo-vapor',
                               'Content-Type': 'application/json'})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def b64(value):
    return base64.urlsafe_b64encode(value).rstrip(b'=')


def app_jwt(config):
    now = int(time.time())
    claims = {'iat': now - 60, 'exp': now + 540, 'iss': str(config['app_id'])}
    message = b64(b'{"alg":"RS256","typ":"JWT"}') + b'.' + b64(json.dumps(claims).encode())
    signed = subprocess.run(['openssl', 'dgst', '-sha256', '-sign', config['private_key']],
                            input=message, capture_output=True, check=True)
    return (message + b'.' + b64(signed.stdout)).decode()


def repository_name(config):
    owner, name = config['owner'], config['repository']
    if not all(re.fullmatch(r'[A-Za-z0-9_.-]+', value) for value in (owner, name)):
        raise ValueError('Invalid repository')
    allowed = config.get('allowed_repositories')
    if allowed is not None:
        if owner + '/' + name not in allowed:
            raise ValueError('Repository not in private allowlist')
    elif owner != OWNER or name not in REPOSITORIES or name not in config.get('repositories', [name]):
        raise ValueError('Repository not in private allowlist')
    return name


def remote_url(repository, owner=OWNER):
    return f'https://github.com/{owner}/{repository}.git'


def git(*arguments):
    return subprocess.check_output(['git', *arguments], text=True).strip()


def origin_identity():
    match = re.fullmatch(r'https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)\.git',
                         git('remote', 'get-url', 'origin'))
    if not match:
        raise ValueError('An HTTPS origin without embedded credentials is required')
    return match.groups()


def origin_repository():
    return origin_identity()[1]


def installation_token(config, permissions=None):
    name = repository_name(config)
    jwt = app_jwt(config)
    installation = api(f'/repos/{config["owner"]}/{name}/installation', jwt)
    if installation['account']['login'].lower() != config['owner'].lower():
        raise ValueError('Unexpected installation owner')
    if installation['app_id'] != int(config['app_id']):
        raise ValueError('Unexpected installed App')
    result = api(f'/app/installations/{installation["id"]}/access_tokens', jwt,
                 {'repositories': [name], 'permissions': permissions or {'contents': 'write', 'workflows': 'write'}})
    return result['token']


def identity(config, token):
    name = config['slug'] + '[bot]'
    user = api('/users/' + name.replace('[', '%5B').replace(']', '%5D'), token)
    if user['type'] != 'Bot' or user['login'] != name or config['slug'] != 'letsolo-vapor':
        raise ValueError('Expected Vapor bot identity')
    return name, f'{user["id"]}+{name}@users.noreply.github.com'


def configure(config, config_path):
    name = repository_name(config)
    expected = remote_url(name, config['owner'])
    if git('remote', 'get-url', 'origin') != expected or git('remote', 'get-url', '--push', 'origin') != expected:
        raise ValueError('Unexpected origin or push destination')
    bot, email = identity(config, installation_token(config))
    hooks = Path(git('rev-parse', '--absolute-git-dir')) / 'letsolo-hooks'
    hooks.mkdir(mode=0o700, exist_ok=True)
    for hook in ('pre-commit', 'pre-push'):
        destination = hooks / hook
        destination.write_bytes(Path(__file__).with_name('check-bot-identity.py').read_bytes())
        destination.chmod(0o700)
    values = {'user.name': bot, 'user.email': email, 'user.useConfigOnly': 'true',
              'commit.gpgSign': 'false', 'tag.gpgSign': 'false', 'letsolo.botName': bot,
              'letsolo.botEmail': email, 'letsolo.repository': name, 'letsolo.owner': config['owner'],
              'letsolo.remote': expected, 'letsolo.appConfig': str(config_path),
              'core.hooksPath': str(hooks), 'credential.useHttpPath': 'true',
              'http.extraHeader': '', 'http.https://github.com/.extraHeader': ''}
    for key, value in values.items():
        git('config', '--local', key, value)
    helper = [sys.executable, '-I', str(Path(__file__).resolve()), '--config', str(config_path),
              '--owner', config['owner'], '--repository', name]
    git('config', '--local', 'alias.bot-gh', '!' + shlex.join([*helper, 'gh']))
    for key in ('credential.helper', 'credential.https://github.com.helper'):
        git('config', '--local', '--replace-all', key, '')
        git('config', '--local', '--add', key, '!' + shlex.join([*helper, 'credential']))
    print(json.dumps({'bot': bot, 'configured': True}))


def credential(config, operation):
    if operation != 'get':
        return
    fields = {}
    for line in sys.stdin:
        if not line.strip():
            break
        key, _, value = line.rstrip('\n').partition('=')
        fields[key] = value
    expected = config['owner'] + '/' + repository_name(config)
    if fields.get('protocol') != 'https' or fields.get('host') != 'github.com' or fields.get('path', '').removesuffix('.git') != expected:
        raise ValueError('Unexpected credential destination')
    token = installation_token(config)
    sys.stdout.write(f'username=x-access-token\npassword={token}\n\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default=os.environ.get('LETSOLO_APP_CREDENTIALS'))
    parser.add_argument('--owner')
    parser.add_argument('--repository')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('configure')
    commands.add_parser('verify')
    helper = commands.add_parser('credential')
    helper.add_argument('operation', choices=('get', 'store', 'erase'))
    cli = commands.add_parser('gh')
    cli.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        path = Path(args.config or git('config', '--local', '--get', 'letsolo.appConfig')).resolve()
        config = json.loads(path.read_text())
        if args.owner and args.repository:
            config.update(owner=args.owner, repository=args.repository)
        else:
            owner, name = origin_identity()
            config.update(owner=owner, repository=args.repository or name)
        repository_name(config)
        if args.command == 'credential':
            credential(config, args.operation)
        elif args.command == 'configure':
            configure(config, path)
        else:
            permissions = {'contents': 'read'}
            if args.command == 'gh':
                first = args.arguments[0] if args.arguments else ''
                permissions = {'contents': 'write'}
                if first == 'pr':
                    permissions['pull_requests'] = 'write'
                elif first in ('workflow', 'run'):
                    permissions['actions'] = 'write'
            token = installation_token(config, permissions)
            bot, _ = identity(config, token)
            if args.command == 'gh':
                environment = os.environ.copy()
                environment['GH_TOKEN'] = token
                environment.pop('GITHUB_TOKEN', None)
                return subprocess.call(['gh', *args.arguments], env=environment)
            commit = api(f'/repos/{config["owner"]}/{config["repository"]}/commits/HEAD', token)
            if any((commit.get(field) or {}).get('login') != bot for field in ('author', 'committer')):
                raise ValueError('Remote author or committer is not Vapor')
            print(json.dumps({'sha': commit['sha'], 'author': bot, 'committer': bot}))
    except (OSError, ValueError, KeyError, HTTPError, URLError, subprocess.SubprocessError):
        if args.command == 'credential':
            sys.stdout.write('quit=true\n\n')
        print('Bot authentication or identity verification failed; personal fallback is disabled.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
