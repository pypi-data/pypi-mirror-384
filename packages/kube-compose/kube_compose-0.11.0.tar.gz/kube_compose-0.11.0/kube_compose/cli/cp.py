import json
import click
import pathlib
import subprocess
from kube_compose import utils
from kube_compose.cli import cli

@cli.command(context_settings={"ignore_unknown_options": True})
@utils.require_binaries(kubectl='kubectl')
@utils.require_kube_compose_release
@click.option('-T', '--no-tar', type=bool, is_flag=True, default=False)
@click.argument('args', nargs=-1, type=str, metavar='[SERVICE:SRC_PATH|SRC_PATH|-] [DEST_PATH|-|SERVICE:DEST_PATH]')
def cp(*, no_tar, args, context, namespace, kubectl, **_):
  ''' Like `docker-compose cp` but for the kubernetes deployed resources
  Use `-T` as a fallback if tar is not available, cat can be used one-at-a-time instead
  '''
  args_ = []
  if no_tar:
    src, dst = args
    if ':' in src and ':' not in dst:
      dst_path = pathlib.Path(dst)
      service, _, path = src.partition(':')
      pod = json.loads(utils.check_output([
        *kubectl,
        *(['--context', context] if context else []),
        *(['-n', namespace] if namespace else []),
        'get', 'pod',
        '-l', f"app.kubernetes.io/name={service}", '-o', 'jsonpath="{.items[0][\'metadata.name\']}"'
      ]).decode())
      src_path = pathlib.PurePosixPath(path)
      ls_R = utils.check_output([
        *kubectl, 'exec',
        *(['--context', context] if context else []),
        *(['-n', namespace] if namespace else []),
        '-t',
        pod,
        '--', 'ls', '-R', path
      ])
      directory = src_path
      dirs = [directory]
      paths = []
      for line in ls_R.decode().splitlines():
        line = line.rstrip('\r\n')
        if not line:
          directory = None
          continue
        if directory is None or line.endswith(':'):
          dir, sep, end = line.rpartition(':')
          assert sep == ':' and end == ''
          directory = pathlib.PurePosixPath(dir)
          dirs.append(directory)
          continue
        else:
          paths.append(directory/line)
      files = set(paths) - set(dirs)
      for dir in dirs:
        click.echo(f"mkdir -p {str(dst_path/dir.relative_to(src_path))}")
        (dst_path/dir.relative_to(src_path)).mkdir(exist_ok=True)
      for file in files:
        click.echo(f"scp {service}:{file} {str(dst_path/(file.relative_to(src_path)))}")
        with (dst_path/(file.relative_to(src_path))).open('wb') as fw:
          subprocess.run([
            *kubectl,
            *(['--context', context] if context else []),
            *(['-n', namespace] if namespace else []),
            'exec',
            '-t',
            pod,
            '--', 'cat', str(file)
          ], stdout=fw, check=True)
    elif ':' in dst and ':' not in src:
      service, _, dst_root = dst.partition(':')
      src_path = pathlib.Path(src)
      for path in (src_path.rglob('*') if src_path.is_dir() else [src_path]):
        dst_path = pathlib.PurePosixPath(dst_root) / path.relative_to(src_path)
        if path.is_dir():
          click.echo(f"exec -- mkdir -p  {str(dst_path)}")
          subprocess.run([
            *kubectl,
            *(['--context', context] if context else []),
            *(['-n', namespace] if namespace else []),
            'exec',
            '-t',
            pod,
            '--', 'mkdir', '-p', str(dst_path)
          ], check=True)
        elif path.is_file():
          click.echo(f"exec -- 'cat > {str(dst_path)}' < {str(path)}")
          with path.open('rb') as fr:
            subprocess.run([
              *kubectl,
              *(['--context', context] if context else []),
              *(['-n', namespace] if namespace else []),
              'exec',
              '-i',
              pod,
              '--', '/bin/sh', '-c', f"cat > {str(dst_path)}"
            ], stdin=fr, check=True)
        else:
          click.echo(f"Ignoring special file {str(path)}")
    else:
      raise click.UsageError('Only supports host => container or container => host')
  else:
    for arg in args:
      if ':' in arg:
        service, _, path = arg.partition(':')
        # find the pod for the specified docker-compose service
        pod = json.loads(utils.check_output([
          *kubectl,
          *(['--context', context] if context else []),
          *(['-n', namespace] if namespace else []),
          'get', 'pod',
          '-l', f"app.kubernetes.io/name={service}", '-o', 'jsonpath="{.items[0][\'metadata.name\']}"'
        ]).decode())
        args_.append(
          (f"{namespace}/" if namespace else '')
          + f"{pod}:{path}"
        )
      else:
        args_.append(arg)
    utils.run([
      *kubectl,
      *(['--context', context] if context else []),
      'cp',
      *args_,
    ])
