import click
from kube_compose.cli import cli
from kube_compose import utils

@cli.command(context_settings={"ignore_unknown_options": True})
@utils.require_binaries(kubectl='kubectl')
@utils.require_kube_compose_release
@click.option('-i', '--stdin', type=bool, is_flag=True)
@click.option('-t', '--tty', type=bool, is_flag=True)
@click.argument('service', type=str)
@click.argument('args', nargs=-1, type=str)
def exec(service, args, *, stdin, tty, context, namespace, kubectl, deployments, **_):
  ''' Like `docker-compose exec` but for the kubernetes deployed resources
  '''
  utils.run([
    *kubectl,
    *(['--context', context] if context else []),
    *(['-n', namespace] if namespace else []),
    'exec',
    *(('-i',) if stdin else tuple()),
    *(('-t',) if tty else tuple()),
    deployments[service],
    *(('--', *args,) if args else tuple()),
  ])
