import sys
import typer
from .core import PyPiRC

app = typer.Typer(add_completion=False)


@app.command()
def add(username: str = '', password: str = '', repo: str = '', server: str = '', rc: str = ''):
    ppr = PyPiRC(rc or None)
    assert server
    if ppr.servers:
        entry = ppr.servers.get(server, {})
    else:
        entry = {}
    entry['repository'] = repo
    if username:
        entry['username'] = username
    if password:
        entry['password'] = password

    ppr.servers[server] = entry
    ppr.save()


@app.command()
def remove(server: str = '', rc: str = ''):
    ppr = PyPiRC(rc or None)
    if server:
        entry = ppr.servers.pop(server, None)
        if entry:
            ppr.save()
            sys.stdout.write('removed: %s' % entry)
            return 0
        else:
            sys.stderr.write(f'No server named {server}')
            return 1
    else:
        ppr.servers.clear()
        return 0
