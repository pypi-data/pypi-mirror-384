from kube_compose.cli import cli

@cli.group()
def configmap():
  ''' Manipulate kubernetes configmaps like docker configs
  '''
  pass
