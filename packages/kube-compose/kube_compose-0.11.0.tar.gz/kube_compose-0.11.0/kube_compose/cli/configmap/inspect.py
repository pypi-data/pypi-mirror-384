import click
from kube_compose import utils
from kube_compose.cli.configmap import configmap

@configmap.command('inspect')
@click.argument('configmap', type=str, required=True)
def _(**kwargs):
  ''' Inspect a kubernetes configmap
  '''
  inspect(**kwargs)

@utils.require_binaries(kubectl='kubectl')
@utils.require_kube_compose_release
def inspect(*, configmap, context, namespace, kubectl, **_):
  utils.run([
    *kubectl,
    *(['--context', context] if context else []),
    *(['-n', namespace] if namespace else []),
    'get',
    f"configmap/{configmap}",
    '-o', 'yaml',
  ])
