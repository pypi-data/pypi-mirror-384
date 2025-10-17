import click
from kube_compose import utils
from kube_compose.cli.configmap import configmap

@configmap.command('rm')
@click.argument('configmap', type=str, required=False)
def _(**kwargs):
  ''' Remove a kubernetes configmap
  '''
  rm(**kwargs)

@utils.require_binaries(kubectl='kubectl')
@utils.require_kube_compose_release
def rm(*, configmap, docker_compose_config, context, namespace, kubectl, **_):
  for configmap in ([configmap] if configmap is not None else docker_compose_config.get('configs', {}).keys()):
    utils.run([
      *kubectl,
      *(['--context', context] if context else []),
      *(['-n', namespace] if namespace else []),
      'delete',
      f"configmap/{configmap}",
    ])
