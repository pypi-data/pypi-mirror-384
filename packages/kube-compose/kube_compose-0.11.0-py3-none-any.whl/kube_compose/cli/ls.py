import click
import json
from kube_compose.cli import cli
from kube_compose import utils

@cli.command()
@click.option('-c', '--context', help='The kubernetes context to restrict ls to')
@click.option('-n', '--namespace', help='The namespace to restrict ls to')
@click.option('-A', '--all-namespaces', help='All namespaces?')
@utils.require_binaries(helm='helm')
def ls(*, context, namespace, all_namespaces, helm, **_):
  ''' Like `docker-compose ls` but shows the docker-compose releases
  '''
  utils.echo_table_via_pager(
    [('NAME', 'NAMESPACE', 'REVISION', 'UPDATED', 'STATUS')] + [
    (release['name'], release['namespace'], release['revision'], release['updated'], release['status'])
    for release in json.loads(
      utils.check_output([
        *helm,
        *(['--kube-context', context] if context else []),
        *(['-A'] if all_namespaces else (['-n', namespace] if namespace else [])),
        'list',
        '-o', 'json',
      ])
    )
    if release['chart'].startswith('kube-compose-')
  ])
