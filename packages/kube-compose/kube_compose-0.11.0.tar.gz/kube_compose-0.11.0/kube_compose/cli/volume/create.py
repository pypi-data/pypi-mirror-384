import click
import yaml
from kube_compose import utils
from kube_compose.cli.volume import volume

def create_volume_spec(*, volume, docker_compose_config, **_):
  volume_specs = []
  for volume, volume_config in ([(volume, docker_compose_config['volumes'][volume],)] if volume is not None else docker_compose_config.get('volumes', {}).items()):
    volume_ext_config = volume_config.get('x-kubernetes', {})
    volume_specs.append({
      'apiVersion': 'v1',
      'kind': 'PersistentVolumeClaim',
      'metadata': {
        'name': volume,
        'labels': dict({'app.kubernetes.io/managed-by': 'kube-compose'}, **volume_ext_config.get('labels', {})),
        'annotations': volume_ext_config.get('annotations', {}),
      },
      'spec': {
        'accessModes': [volume_ext_config.get('mode', 'ReadWriteOnce')],
        'resources': {
          'requests': {
            'storage': volume_ext_config.get('size', '1Gi'),
          },
        },
        'storageClassName': volume_ext_config.get('class', ''),
        'volumeMode': 'Filesystem',
      },
    })
  return volume_specs

@utils.require_binaries(kubectl='kubectl')
@utils.require_kube_compose_release
def create(*, volume, docker_compose_config, context, namespace, kubectl, **_):
  volume_specs = create_volume_spec(
    volume=volume,
    docker_compose_config=docker_compose_config,
    kubectl=kubectl,
  )
  if not volume_specs: return
  utils.run([
    *kubectl,
    *(['--context', context] if context else []),
    *(['-n', namespace] if namespace else []),
     'apply',
    '-f', '-',
  ], input=yaml.dump_all(volume_specs).encode())

@volume.command('create')
@click.argument('volume', type=str, required=False)
def _(**kwargs):
  ''' Ensure a kubernetes persistent volume is created
  '''
  create(**kwargs)
