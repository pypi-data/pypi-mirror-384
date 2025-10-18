import typer

from gwupload.stubs.client import client_cli
from gwupload.stubs.ingester import ingester_cli

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode="rich",
    help="Stubs for testing Gridworks Uploader",
)

app.add_typer(ingester_cli.app, name="ingester", help="Use stub ingester")
app.add_typer(client_cli.app, name="client", help="Use stub client")


@app.callback()
def main_app_callback() -> None: ...


# For sphinx:
typer_click_object = typer.main.get_command(app)

if __name__ == "__main__":
    app()
