import click
from kube_compose.cli import cli
from kube_compose import utils

@cli.command()
@utils.require_binaries(kubectl='kubectl')
@utils.require_kube_compose_release
@click.argument('service', type=str, required=True)
def kill(service, *, context, namespace, kubectl, docker_compose_config, **_):
  ''' Like `docker-compose kill` but effects the kubernetes deployed resources
  '''
  utils.run([
    *kubectl,
    *(['--context', context] if context else []),
    *(['-n', namespace] if namespace else []),
    'delete', 'pod',
    '-l', f"app.kubernetes.io/name={service}",
  ])
