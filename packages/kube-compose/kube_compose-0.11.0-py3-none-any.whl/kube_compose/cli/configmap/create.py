import os
import yaml
import click
from kube_compose import utils
from kube_compose.cli.configmap import configmap

def create_configmap_spec(*, configmap, docker_compose_path, docker_compose_config, **_):
  configmap_specs = []
  for config, config_config in ([(config, docker_compose_config['configs'][configmap],)] if configmap is not None else docker_compose_config.get('configs', {}).items()):
    config_ext_config = config_config.get('x-kubernetes', {})
    configmap_spec = {
      'apiVersion': 'v1',
      'kind': 'ConfigMap',
      'metadata': {
        'name': config,
        'labels': dict({'app.kubernetes.io/managed-by': 'kube-compose'}, **config_ext_config.get('labels', {})),
        'annotations': config_ext_config.get('annotations', {}),
      },
      'data': {}
    }
    if 'content' in config_config:
      configmap_spec['data']['content'] = config_config['content']
    elif 'file' in config_config:
      configmap_spec['data']['content'] = (docker_compose_path.parent / config_config['file']).read_text()
    elif 'environment' in config_config:
      configmap_spec['data']['content'] = os.environ[config_config['environment']]
    elif 'external' in config_config:
      pass
    else:
      raise NotImplementedError('config could not be located')
    configmap_specs.append(configmap_spec)
  return configmap_specs

@utils.require_binaries(kubectl='kubectl')
@utils.require_kube_compose_release
def create(*, configmap, docker_compose_path, docker_compose_config, context, namespace, kubectl, **_):
  configmap_specs = create_configmap_spec(
    configmap=configmap,
    docker_compose_path=docker_compose_path,
    docker_compose_config=docker_compose_config,
    kubectl=kubectl,
  )
  if not configmap_specs: return
  utils.run([
    *kubectl,
    *(['--context', context] if context else []),
    *(['-n', namespace] if namespace else []),
    'apply',
    '-f', '-',
  ], input=yaml.dump_all(configmap_specs).encode())

@configmap.command('create')
@click.argument('configmap', type=str, required=False)
def _(**kwargs):
  ''' Ensure a kubernetes configmap is created
  '''
  create(**kwargs)
