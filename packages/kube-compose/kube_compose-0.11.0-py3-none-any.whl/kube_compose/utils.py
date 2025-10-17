import click
import pathlib
import functools

__dir__ = pathlib.Path(__file__).parent

helm_chart = str(__dir__ / 'charts' / 'kube-compose')

def assert_defined(value, or_else):
  assert value, or_else
  return value

def pathlib_coalesce(*paths):
  for path in map(pathlib.Path, paths):
    if path.exists(): return path
  if not paths: raise RuntimeError('No paths to check')
  else: raise FileNotFoundError(paths[0])

def set_group_config(fn):
  @click.pass_context
  def wrapper(ctx, *args, **kwargs):
    ctx.ensure_object(dict)
    ctx.obj.update(**kwargs)
    return ctx.invoke(fn, *args, **kwargs)
  return functools.update_wrapper(wrapper, fn)

def require_group_config(fn):
  @click.pass_context
  def wrapper(ctx: click.Context, *args, **kwargs):
    return ctx.invoke(fn, *args, **dict(ctx.obj, **kwargs))
  return functools.update_wrapper(wrapper, fn)

@click.pass_context
def run(ctx: click.Context, *args, input=None, **kwargs):
  ''' Similar to subprocess.run but
  1. forward Ctrl+C
  2. exit click application with exitcode of the process
  '''
  import signal
  import subprocess
  if input: kwargs['stdin'] = subprocess.PIPE
  p = subprocess.Popen(*args, **kwargs)
  if input:
    p.stdin.write(input)
    p.stdin.close()
  while p.returncode is None:
    try:
      p.wait()
    except KeyboardInterrupt:
      p.send_signal(signal.SIGINT)
    except:
      p.kill()
      p.wait()
      raise
  if p.returncode != 0:
    ctx.exit(p.returncode)

@click.pass_context
def check_output(ctx: click.Context, *args, **kwargs):
  ''' Similar to subprocess.check_output but exit click application with exitcode of the process on error
  '''
  import subprocess
  try:
    return subprocess.check_output(*args, **kwargs)
  except subprocess.CalledProcessError as e:
    ctx.exit(e.returncode)

def require_binaries(**required_binaries):
  ''' Ensure binaries are present, and inject the paths to them in kwargs
  Usage:
  @require_binaries(curl_bin='curl -s')
  def whats_my_ip(*, curl_bin):
    return check_output([*curl_bin, 'https://ifconfig.me']).decode()
  '''
  def decorator(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
      from shutil import which
      binaries = {
        arg: [assert_defined(which(bin), f"{bin} command not found"), *args]
        for arg, binary in required_binaries.items()
        for bin, *args in (binary if type(binary) == list else binary.split(' '),)
      }
      return fn(*args, **dict(binaries, **kwargs))
    return wrapper
  return decorator

def echo_table_via_pager(records):
  import click
  colSize = {}
  for record in records:
    for i, cell in enumerate(record):
      colSize[i] = max(colSize[i], len(cell)) if i in colSize else len(cell)
  click.echo_via_pager([
    ' '.join(('{:^%d}' % (colSize[i])).format(cell) for i, cell in enumerate(record)) + '\n'
    for record in records
  ])

@require_group_config
def locate_docker_compose_path(*, file, **_):
  docker_compose_path = pathlib.Path(file) if file else pathlib_coalesce('docker-compose.yaml', 'docker-compose.yml')
  return docker_compose_path

def require_kube_compose_release(fn):
  @functools.wraps(fn)
  @require_binaries(docker_compose='docker compose')
  def wrapper(*, docker_compose, **kwargs):
    import yaml
    docker_compose_path = locate_docker_compose_path()
    docker_compose_config_raw = check_output([*docker_compose, '-f', str(docker_compose_path), 'config', '--no-path-resolution'])
    docker_compose_config = yaml.safe_load(docker_compose_config_raw)
    if 'x-kubernetes' not in docker_compose_config or not docker_compose_config.get('name'):
      raise click.ClickException('top-level `x-kubernetes` map with release `name` is required')
    release_config = docker_compose_config['x-kubernetes']
    name = release_config['name']
    context = release_config.get('context')
    namespace = release_config.get('namespace')
    deployments = {
      service_name: f"deploy/{service_name}" if service.get('deploy', {}).get('mode') != 'global' else f"daemonset/{service_name}"
      for service_name, service in docker_compose_config.get('services', {}).items()
      for x_kubernetes in (service.get('x-kubernetes', {}),)
      if not x_kubernetes.get('exclude') and x_kubernetes.get('cron') is None
    }
    return fn(**dict(kwargs,
      docker_compose=docker_compose,
      docker_compose_path=docker_compose_path,
      docker_compose_config_raw=docker_compose_config_raw,
      docker_compose_config=docker_compose_config,
      deployments=deployments,
      release_config=release_config,
      name=name,
      context=context,
      namespace=namespace,
    ))
  return wrapper
