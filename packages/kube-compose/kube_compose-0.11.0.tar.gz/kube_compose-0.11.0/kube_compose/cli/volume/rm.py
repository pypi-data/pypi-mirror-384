import click
from kube_compose import utils
from kube_compose.cli.volume import volume

@volume.command('rm')
@click.argument('volume', type=str, required=False)
def _(**kwargs):
  ''' Remove a kubernetes persistent volume
  '''
  rm(**kwargs)

@utils.require_binaries(kubectl='kubectl')
@utils.require_kube_compose_release
def rm(*, volume, docker_compose_config, context, namespace, kubectl, **_):
  for volume in ([volume] if volume is not None else docker_compose_config.get('volumes', {}).keys()):
    utils.run([
      *kubectl,
      *(['--context', context] if context else []),
      *(['-n', namespace] if namespace else []),
      'delete',
      f"pvc/{volume}",
    ])
