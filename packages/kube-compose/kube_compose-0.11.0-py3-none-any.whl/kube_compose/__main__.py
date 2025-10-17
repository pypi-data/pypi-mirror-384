import importlib
from kube_compose.cli import cli
from kube_compose import utils

for f in (utils.__dir__ / 'cli').rglob('[!_]*.py'):
  importlib.import_module('.'.join([
    utils.__dir__.stem, *f.relative_to(utils.__dir__).parts[:-1], f.stem
  ]))

if __name__ == '__main__':
  cli()
