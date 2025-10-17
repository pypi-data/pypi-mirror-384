from kube_compose.cli.get import get
from kube_compose import utils

@get.command('all')
@utils.require_binaries(helm='helm')
@utils.require_kube_compose_release
def all(*, name, context, namespace, helm, **_):
  ''' download all information for a named release
  '''
  utils.run([
    *helm,
    *(['--kube-context', context] if context else []),
    *(['-n', namespace] if namespace else []),
    'get', 'all',
    name,
  ])
