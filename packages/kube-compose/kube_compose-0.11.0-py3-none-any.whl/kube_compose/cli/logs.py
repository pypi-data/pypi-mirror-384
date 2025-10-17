import click
from kube_compose.cli import cli
from kube_compose import utils

@cli.command()
@utils.require_binaries(kubectl='kubectl')
@utils.require_kube_compose_release
@click.option('-p', '--previous', type=bool, is_flag=True, help='Print the logs for the previous instance of the container')
@click.option('-f', '--follow', type=bool, is_flag=True, help='Follow log output')
@click.option('-n', '--tail', type=int, default=-1, help='Number of lines to show from the end of the logs (-1 all lines)')
@click.option('-t', '--timestamps', type=bool, is_flag=True, help='Show timestamps')
@click.argument('service', type=str)
@click.argument('args', nargs=-1, type=str)
def logs(service, args, *, previous, follow, tail, timestamps, kubectl, context, namespace, **_):
  ''' Like `docker-compose logs` but for the kubernetes deployed resources
  '''
  utils.run([
    *kubectl,
    *(['--context', context] if context else []),
    *(['-n', namespace] if namespace else []),
    'logs',
    *(('-p',) if previous else tuple()),
    *(('-f',) if follow else tuple()),
    *((f"--tail={tail}",) if tail != -1 else tuple()),
    *((f"--timestamps",) if timestamps else tuple()),
    '-l', f"app.kubernetes.io/name={service}",
    *args,
  ])
