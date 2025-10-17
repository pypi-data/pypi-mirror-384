from kube_compose.cli import cli

@cli.group()
def volume():
  ''' Manipulate kubernetes persistent volume claims like docker volumes
  '''
  pass
