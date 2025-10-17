import click
from kube_compose.cli import cli
from kube_compose import utils

@cli.command()
@utils.require_binaries(kubectl='kubectl')
@utils.require_kube_compose_release
@click.argument('service', type=str, required=False)
def stop(service, *, context, namespace, kubectl, deployments, **_):
  ''' Like `docker-compose stop` but effects the kubernetes deployed resources
  '''
  deploy = [deployments[service]] if service is not None else list(deployments.values())
  utils.run([
    *kubectl,
    *(['--context', context] if context else []),
    *(['-n', namespace] if namespace else []),
    'scale',
    '--replicas=0',
    *deploy,
  ])
