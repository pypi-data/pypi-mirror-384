import sys
import yaml
import click
from kube_compose import utils
from kube_compose.cli.configmap import configmap
from kube_compose.cli.configmap.create import create_configmap_spec

@utils.require_binaries(kubectl='kubectl')
@utils.require_kube_compose_release
def template(*, configmap, docker_compose_path, docker_compose_config, context, namespace, kubectl, **_):
  configmap_specs = create_configmap_spec(
    configmap=configmap,
    docker_compose_path=docker_compose_path,
    docker_compose_config=docker_compose_config,
    kubectl=kubectl,
  )
  if not configmap_specs: return []
  # use kubectl to fill-in defaults/validate
  templ = yaml.safe_load(utils.check_output([
    *kubectl,
    *(['--context', context] if context else []),
    *(['-n', namespace] if namespace else []),
     'apply',
    '--dry-run=client',
    '-oyaml',
    '-f', '-',
  ], input=yaml.dump_all(create_configmap_spec(
    configmap=configmap,
    docker_compose_path=docker_compose_path,
    docker_compose_config=docker_compose_config,
    kubectl=kubectl,
  )).encode()))
  # write items in flat yaml format
  if templ['kind'] == 'List':
    return templ['items']
  else:
    return [templ]

@configmap.command('template')
@click.argument('configmap', type=str, required=False)
def _(**kwargs):
  ''' Template a kubernetes configmap
  '''
  yaml.dump_all(template(**kwargs), sys.stdout)
