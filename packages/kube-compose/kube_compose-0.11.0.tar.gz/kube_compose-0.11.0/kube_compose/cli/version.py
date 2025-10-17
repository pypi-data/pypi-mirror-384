import re
import click
from ruamel.yaml import YAML
from kube_compose.cli import cli
from kube_compose import utils

@cli.command()
@click.argument('service', type=str, default=None)
@click.argument('newversion', type=str, default=None, metavar='[<newversion> | major | minor | patch]', required=False)
def version(service, newversion):
  ''' Get or set the version of a service in docker-compose.yaml
  '''
  yaml = YAML()
  docker_compose_path = utils.locate_docker_compose_path()
  with docker_compose_path.open('r') as fr:
    docker_compose_config = yaml.load(fr)
  #
  service = docker_compose_config['services'][service]
  container, sep, version = service['image'].partition(':')
  if not sep:
    sep = ':'
    version = 'latest'
  if not newversion:
    click.echo(version)
    return
  elif newversion in ('major', 'minor', 'patch'):
    semver = re.match(r'^(.*?)(\d+)\.(\d+)(\.(\d+))?(.*?)$', version)
    if not semver: raise RuntimeError(f"Failed to parse {version}")
    prefix, major, minor, _, patch, postfix = semver.groups()
    if newversion == 'major':
      major = str(int(major)+1)
      minor = '0'
      patch = '0'
    elif newversion == 'minor':
      minor = str(int(minor)+1)
      patch = '0'
    elif newversion == 'patch':
      patch = str(int(patch or -1)+1)
    newversion = ''.join([prefix, '.'.join(filter(None, [major, minor, patch])), postfix])
    service['image'] = f"{container}{sep}{newversion}"
  elif newversion:
    service['image'] = f"{container}{sep}{newversion}"
  with docker_compose_path.open('w') as fw:
    yaml.dump(docker_compose_config, fw)
