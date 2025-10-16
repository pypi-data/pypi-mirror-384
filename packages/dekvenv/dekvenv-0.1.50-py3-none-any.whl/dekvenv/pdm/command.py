import os
import typer
from typing_extensions import Annotated
from dektools.shell import shell_wrapper
from dektools.file import remove_path
from dektools.typer import command_mixin
from dektools.web.url import Url

app = typer.Typer(add_completion=False)


@app.command()
def config(
        update: Annotated[bool, typer.Option("--update/--no-update")] = False,
        cache: Annotated[bool, typer.Option("--cache/--no-cache")] = True,
):
    shell_wrapper(f"pdm config check_update {'true' if update else 'false'}")
    shell_wrapper(f"pdm config install.cache {'on' if cache else 'off'}")


@command_mixin(app)
def install(args):
    os.environ['PDM_IGNORE_ACTIVE_VENV'] = 'true'
    shell_wrapper(f'pdm install {args}')


@command_mixin(app)
def global_install_dir(args, path):
    os.environ['PDM_IGNORE_ACTIVE_VENV'] = 'true'
    shell_wrapper(f'pdm install --project {path} -G :all --no-editable --global {args}')


@command_mixin(app)
def global_add(args):
    shell_wrapper(f'pdm add -G :all --no-editable --global {args}')


@app.command()
def clear():
    from .core import get_pdm_cache_dir
    shell_wrapper(f'pdm cache clear')
    remove_path(get_pdm_cache_dir())


@app.command()
def clear_hash():
    from .core import get_pdm_cache_dir_hash
    remove_path(get_pdm_cache_dir_hash())


default_pypi_name = 'private'


@app.command()
def login(url, name: Annotated[str, typer.Argument()] = default_pypi_name):
    url_ = Url.new(url)
    shell_wrapper(f'pdm config pypi.{name}.url {url_.uncertified}')
    if url.startswith('https:'):
        shell_wrapper(f'pdm config pypi.{name}.verify_ssl true')
    shell_wrapper(f'pdm config pypi.{name}.username "{url_.username}"')
    shell_wrapper(f'pdm config pypi.{name}.password "{url_.password}"')


@app.command()
def logout(name: Annotated[str, typer.Argument()] = default_pypi_name):
    shell_wrapper(f'pdm config pypi.{name} --delete')
