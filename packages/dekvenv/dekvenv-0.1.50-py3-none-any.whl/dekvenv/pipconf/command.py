import sys
import typer
from .core import PipConf

app = typer.Typer(add_completion=False)


@app.command()
def add(extra: bool = False, username: str = '', password: str = '', repo: str = '', conf: str = ''):
    pc = PipConf(conf or None)
    assert repo
    if extra:
        pc.add_extra_url(repo, username, password)
    else:
        pc.set_index_url(repo, username, password)
    pc.save()


@app.command()
def remove(repo: str = '', conf: str = ''):
    pc = PipConf(conf or None)
    if repo:
        ret = pc.remove_extra_url(repo)
        if ret:
            sys.stdout.write('removed: %s' % repo)
            return 0
        else:
            sys.stderr.write(f'No repo named {repo}')
            return 1
    else:
        pc.clear_extra_url()
        return 0
