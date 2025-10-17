import click
from kube_compose.cli import cli
from kube_compose import utils

@cli.command()
@utils.require_binaries(kubectl='kubectl')
@utils.require_kube_compose_release
@click.argument('service', type=str, required=False)
def stats(service, *, context, namespace, docker_compose_config, kubectl, **_):
  ''' Like `docker-compose stats` but show status of the kubernetes deployed resource
  '''
  services = [service] if service is not None else docker_compose_config.get('services', {}).keys()
  utils.run([
    *kubectl,
    *(['--context', context] if context else []),
    *(['-n', namespace] if namespace else []),
    'top', 'pod',
    *[arg for svc in services for arg in ('-l', f"app.kubernetes.io/name={svc}",)],
  ])
