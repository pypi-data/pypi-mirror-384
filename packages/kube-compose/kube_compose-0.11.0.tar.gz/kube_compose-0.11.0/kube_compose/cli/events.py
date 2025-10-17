import click
from kube_compose.cli import cli
from kube_compose import utils

@cli.command()
@utils.require_binaries(kubectl='kubectl')
@utils.require_kube_compose_release
@click.argument('service', type=str, required=True)
def events(service, *, context, namespace, kubectl, deployments, **_):
  ''' Like `docker-compose events` but show events of the kubernetes deployed resource
  '''
  if service:
    utils.run([
      *kubectl,
      *(['--context', context] if context else []),
      *(['-n', namespace] if namespace else []),
      'events', 
      '--for', deployments[service],
      '--watch',
    ])
