import typer

app = typer.Typer(add_completion=False)


@app.command()
def pdm(reverse: bool = typer.Option(False, "--reverse", "-r")):
    from ..pdm.core import fix_pdm
    fix_pdm(reverse)
