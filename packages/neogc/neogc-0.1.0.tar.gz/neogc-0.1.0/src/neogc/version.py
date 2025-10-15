import typer

version_app = typer.Typer()

@version_app.command("info")
def info():
    pass

@version_app.command("list")
def list():
    pass

@version_app.command("upgrade")
def upgrade():
    pass

if __name__ == "__main__":
    version_app()