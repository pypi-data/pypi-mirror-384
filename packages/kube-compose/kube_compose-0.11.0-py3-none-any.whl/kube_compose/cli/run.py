import json
import uuid
import click
from kube_compose import utils
from kube_compose.cli import cli

@cli.command(context_settings={"ignore_unknown_options": True})
@utils.require_binaries(kubectl='kubectl')
@utils.require_kube_compose_release
@click.option('-i', '--stdin', type=bool, is_flag=True)
@click.option('-t', '--tty', type=bool, is_flag=True)
@click.argument('service', type=str)
@click.argument('args', nargs=-1, type=str)
def run(*, service, args, stdin, tty, context, namespace, docker_compose_config, kubectl, **_):
  ''' Like `docker-compose run` but for the kubernetes deployed resources
  '''
  service_config = docker_compose_config['services'][service]
  name = f"{service}-{uuid.uuid4()}"
  overrides = {
    'spec': {
      'containers': [{
        'name': name,
        'image': service_config['image'],
      }],
    },
  }
  #
  if service_config.get('environment'):
    overrides['spec']['containers'][0]['env'] = [
      {
        'name': key,
        'value': value,
      }
      for key, value in service_config.get('environment', {}).items()
    ]
  #
  if service_config.get('volumes'):
    overrides['spec']['containers'][0]['volumeMounts'] = []
    overrides['spec']['volumes'] = []
    for volume in service_config['volumes']:
      from kube_compose.cli.volume.create import create
      create(volume=volume['source'])
      overrides['spec']['containers'][0]['volumeMounts'].append(
        {
          'mountPath': volume['target'],
          'name': volume['source'],
        }
      )
      overrides['spec']['volumes'].append(
        {
          'name': volume['source'],
          'persistentVolumeClaim': {
            'claimName': volume['source'],
          },
        }
      )
  #
  utils.run([
    *kubectl,
      *(['--context', context] if context else []),
      *(['-n', namespace] if namespace else []),
      'run',
      name,
      '--attach',
      '--rm',
      *(('-i',) if stdin else tuple()),
      *(('-t',) if tty else tuple()),
      f"--image={service_config['image']}",
      '--overrides', json.dumps(overrides),
      *(('--command', '--', *args) if args else tuple()),
  ])
