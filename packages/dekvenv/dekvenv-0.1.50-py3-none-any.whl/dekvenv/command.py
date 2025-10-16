from .main.command import app
from .pdm import command as pdm_command
from .pipconf import command as pipconf_command
from .pypirc import command as pypirc_command
from .script import command as script_command
from .fix import command as fix_command

app.add_typer(pdm_command.app, name='pdm')
app.add_typer(pipconf_command.app, name='pipconf')
app.add_typer(pypirc_command.app, name='pypirc')
app.add_typer(script_command.app, name='script')
app.add_typer(fix_command.app, name='fix')
