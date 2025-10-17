import click
import subprocess
from kube_compose.cli import cli
from kube_compose import utils

@cli.command()
@utils.require_binaries(helm='helm', kubectl='kubectl')
@utils.require_kube_compose_release
@click.option('--create-namespace', type=bool, is_flag=True, help='Create the release namespace if not present')
def up(*, helm, kubectl, name, context, namespace, docker_compose_config_raw, deployments, create_namespace, **_):
  ''' Like `docker-compose up` but runs in the kubernetes cluster
  '''
  from kube_compose.cli.volume.create import create as volume_create
  from kube_compose.cli.configmap.create import create as configmap_create
  volume_create(volume=None)
  configmap_create(configmap=None)
  if subprocess.call([
    *helm,
    *(['--kube-context', context] if context else []),
    *(['-n', namespace] if namespace else []),
    'status',
    name
  ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
    utils.run([
      *helm,
      *(['--kube-context', context] if context else []),
      *(['-n', namespace] if namespace else []),
      'upgrade',
      name,
      utils.helm_chart,
      '-f', '-'
    ], input=docker_compose_config_raw)
  else:
    utils.run([
      *helm,
      *(['--kube-context', context] if context else []),
      *(['-n', namespace] if namespace else []),
      'install',
      name,
      utils.helm_chart,
      *(['--create-namespace'] if create_namespace else []),
      '-f', '-',
    ], input=docker_compose_config_raw)
  #
  utils.run([
    *kubectl,
    *(['--context', context] if context else []),
    *(['-n', namespace] if namespace else []),
    'rollout', 'status',
    *deployments.values(),
  ])
