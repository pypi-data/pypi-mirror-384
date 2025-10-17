from kube_compose import utils
from kube_compose.cli.configmap import configmap

@configmap.command('ls')
def _(**kwargs):
  ''' List kubernetes configmaps
  '''
  ls(**kwargs)

@utils.require_binaries(kubectl='kubectl')
@utils.require_kube_compose_release
def ls(*, context, namespace, kubectl, **_):
  utils.run([
    *kubectl,
    *(['--context', context] if context else []),
    *(['-n', namespace] if namespace else []),
    'get',
    'configmap',
  ])
