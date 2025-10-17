import click
from kube_compose.cli import cli
from kube_compose import utils

@cli.command()
@utils.require_binaries(helm='helm')
@utils.require_kube_compose_release
@click.argument('revision', type=int, required=False)
def rollback(revision, *, helm, name, context, namespace, **_):
  ''' Alias for `helm rollback [revision]`
  '''
  utils.run([
    *helm,
    *(['--kube-context', context] if context else []),
    *(['-n', namespace] if namespace else []),
    'rollback',
     name,
     *([revision] if revision else []),
  ])
