import typer

config_app = typer.Typer()

@config_app.command("clear")
def clear():
    pass

@config_app.command("clear-cache")
def clear_cache():
    pass

@config_app.command("current")
def current():
    pass

@config_app.command("set")
def set():
    pass

if __name__ == "__main__":
    config_app()