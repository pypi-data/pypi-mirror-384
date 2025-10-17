import json
import click
from kube_compose import utils
from kube_compose.cli.volume import volume

@volume.command('ls')
def _(**kwargs):
  ''' List kubernetes persistent volume claims
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
    'pvc',
  ])
