import click
import pathlib
from ruamel.yaml import YAML
from kube_compose.cli import cli
from kube_compose import utils

@cli.command()
def init():
  ''' Initialize a kube-compose configuration
  '''
  yaml = YAML()
  try:
    docker_compose_path = utils.locate_docker_compose_path()
  except FileNotFoundError:
    docker_compose_path = pathlib.Path('docker-compose.yaml')
  try:
    with docker_compose_path.open('r') as fr:
      docker_compose_config = yaml.load(fr)
  except FileNotFoundError:
    docker_compose_config = {
      'services': {},
    }
  #
  if 'x-kubernetes' not in docker_compose_config:
    docker_compose_config['x-kubernetes'] = {}
  release_config = docker_compose_config['x-kubernetes']
  if 'name' not in release_config:
    release_config['name'] = click.prompt('Release Name', type=str, default=docker_compose_path.absolute().parent.name)
  if 'namespace' not in release_config:
    release_config['namespace'] = click.prompt('Release Namespace', type=str, default='default')
  #
  with docker_compose_path.open('w') as fw:
    yaml.dump(docker_compose_config, fw)
