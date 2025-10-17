import click
from kube_compose import utils

@click.group()
@click.version_option()
@click.option('-f', '--file', help='Compose configuration files')
@utils.set_group_config
def cli(**kwargs): pass
