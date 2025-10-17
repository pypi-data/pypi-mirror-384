import yaml
import tempfile
import pathlib
from kube_compose.cli import cli
from kube_compose import utils

@cli.command()
@utils.require_binaries(helm='helm', diff='diff')
@utils.require_kube_compose_release
def diff(*, name, context, namespace, docker_compose_config, helm, diff, **_):
  ''' Compare the local docker-compose with the one deployed to kubernetes
  '''
  helm_release_yaml = yaml.safe_load(utils.check_output([
    *helm,
    *(['--kube-context', context] if context else []),
    *(['-n', namespace] if namespace else []),
    'get', 'values',
    name
  ]))
  del helm_release_yaml['USER-SUPPLIED VALUES']
  #
  with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = pathlib.Path(tmpdir)
    # write as canonical yaml
    with (tmpdir / 'local.docker-compose.yaml').open('w') as fw:
      yaml.dump(docker_compose_config, fw, sort_keys=True)
    with (tmpdir / 'remote.docker-compose.yaml').open('w') as fw:
      yaml.dump(helm_release_yaml, fw, sort_keys=True)
      utils.run([
        *diff, '-Naur', str(tmpdir / 'remote.docker-compose.yaml'), str(tmpdir / 'local.docker-compose.yaml')
      ])
