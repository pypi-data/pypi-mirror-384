import os
import sys
import typer
import virtualenv
from typing import Optional, List
from typing_extensions import Annotated
from dektools.file import remove_path, write_file
from dektools.shell import shell_wrapper
from dektools.sys import sys_paths_relative
from dektools.output import print_data_or_value
from dektools.typer import command_version
from dektools.venvx.active import activate_venv
from dektools.venvx.constants import venv_main
from dektools.typer import command_mixin, annotation
from .core import get_pkg_path

app = typer.Typer(add_completion=False)
command_version(app, __name__)


@app.command()
def create(name=venv_main, path='.', parent='', empty: Annotated[bool, typer.Option("--empty/--no-empty")] = False):
    path = os.path.normpath(os.path.abspath(path))
    path_venv = os.path.join(path, name)
    if not os.path.exists(path_venv):
        args = [path_venv]
        if empty:
            args.extend(['--no-pip', '--no-setuptools', '--no-wheel'])
        virtualenv.cli_run(args)
    if parent:
        path_parent = os.path.normpath(os.path.abspath(parent))
        path_var = sys_paths_relative('', True)
        path_lib = path_var['platlib']
        pth = f"import site;site.addsitedir(r'{path_parent}{path_lib}')"
        write_file(os.path.join(path_venv + path_lib, 'aaa__parent.pth'), s=pth)


@app.command()
def active(
        path: Annotated[str, typer.Argument()] = "",
        ignore: Annotated[bool, typer.Option("--ignore/--no-ignore")] = True):
    activate_venv(path, ignore)


@app.command()
def build(path='.'):
    from ..pdm.core import is_pdm_project
    remove_path(os.path.join(path, '.pdm-build'))
    remove_path(os.path.join(path, 'build'))
    remove_path(os.path.join(path, 'dist'))
    if os.path.isdir(path):
        for fn in os.listdir(path):
            if fn.endswith('.egg-info'):
                remove_path(os.path.join(path, fn))

    if is_pdm_project(path):
        shell_wrapper(f'pdm build -p {path}')
    else:
        shell_wrapper(f'{sys.executable} -m build -s -w {path}')


@app.command()
def update(path_dir):
    from ..pdm.core import pdm_update_cache_pkg
    from ..utils.common import get_py_pkg_info
    path_dir = os.path.normpath(os.path.abspath(path_dir))
    pdm_update_cache_pkg(path_dir, get_py_pkg_info(path_dir))


@app.command()
def push(server: str = '', path: str = '.', se: bool = True):
    from ..utils.common import get_py_pkg_name
    from ..pdm.core import pdm_clear_cache_hash_pkg, pdm_clear_cache_pkg, pdm_clear_cache_metadata
    assert server
    build(path)
    path_pkg = get_pkg_path(path)
    pdm_clear_cache_hash_pkg(server, os.path.basename(path_pkg))
    pdm_clear_cache_pkg(get_py_pkg_name(path), path_pkg)
    pdm_clear_cache_metadata(path_pkg)
    shell_wrapper(f'twine upload {"--skip-existing" if se else ""} --repository {server} {path_pkg}')


@app.command()
def sys_paths(key: Annotated[str, typer.Argument()] = ""):
    print_data_or_value(sys_paths_relative('', True), key)


@app.command()
def meta(path, key: Annotated[str, typer.Argument()] = ""):
    from ..utils.common import get_py_pkg_info
    print_data_or_value(get_py_pkg_info(path), key)


@command_mixin(app)
def retry(
        args,
        retry_times: Annotated[Optional[int], annotation.Option('--times')] = -1,
        cmd: Annotated[Optional[List[str]], annotation.Option()] = None
):
    from dektools.shell import shell_retry
    if cmd:
        commands = cmd
    else:
        commands = args
    shell_retry(commands, retry_times if retry_times >= 0 else None)
