import typer

import neogc.config as config
import neogc.version as version

app = typer.Typer()
app.add_typer(config.config_app, name="config")
app.add_typer(version.version_app, name="version")

if __name__ == "__main__":
    app()