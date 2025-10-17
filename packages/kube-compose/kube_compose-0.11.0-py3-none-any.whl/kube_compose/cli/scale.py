import click
import itertools
from kube_compose.cli import cli
from kube_compose import utils

@cli.command()
@utils.require_binaries(kubectl='kubectl')
@utils.require_kube_compose_release
@click.argument('args', nargs=-1, type=str)
def scale(args, *, context, namespace, kubectl, deployments, **_):
  ''' Like `docker-compose scale` but effects the kubernetes deployed resources
  Arguments are expected to be like: `service-name=replicas`
  '''
  deploy_replicas = []
  for arg in args:
    service_name, _, replicas = arg.partition('=')
    deploy_replicas.append((int(replicas), deployments[service_name]))
  #
  for replicas, deploy in itertools.groupby(sorted(deploy_replicas), lambda key: key[0]):
    utils.run([
      *kubectl,
      *(['--context', context] if context else []),
      *(['-n', namespace] if namespace else []),
      'scale',
      f"--replicas={replicas}",
      *[d for _, d in deploy],
    ])
