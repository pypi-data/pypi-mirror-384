import sys
import yaml
import click
from kube_compose import utils
from kube_compose.cli.volume import volume
from kube_compose.cli.volume.create import create_volume_spec

@utils.require_binaries(kubectl='kubectl')
@utils.require_kube_compose_release
def template(*, volume, docker_compose_config, context, namespace, kubectl, **_):
  volume_specs = create_volume_spec(
    volume=volume,
    docker_compose_config=docker_compose_config,
    kubectl=kubectl,
  )
  if not volume_specs: return []
  # use kubectl to fill-in defaults/validate
  templ = yaml.safe_load(utils.check_output([
    *kubectl,
    *(['--context', context] if context else []),
    *(['-n', namespace] if namespace else []),
    'apply',
    '--dry-run=client',
    '-oyaml',
    '-f', '-',
  ], input=yaml.dump_all(create_volume_spec(
    volume=volume,
    docker_compose_config=docker_compose_config,
    kubectl=kubectl,
  )).encode()))
  # write items in flat yaml format
  if templ['kind'] == 'List':
    return templ['items']
  else:
    return [templ]

@volume.command('template')
@click.argument('volume', type=str, required=False)
def _(**kwargs):
  ''' Ensure a kubernetes persistent volume is templated
  '''
  yaml.dump_all(template(**kwargs), sys.stdout)
