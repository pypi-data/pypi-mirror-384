from kube_compose.cli.get import get
from kube_compose import utils

@get.command('values')
@utils.require_binaries(helm='helm')
@utils.require_kube_compose_release
def values(*, name, context, namespace, helm, **_):
  ''' download the values file for a named release
  '''
  utils.run([
    *helm,
    *(['--kube-context', context] if context else []),
    *(['-n', namespace] if namespace else []),
    'get', 'values',
    name,
  ])
