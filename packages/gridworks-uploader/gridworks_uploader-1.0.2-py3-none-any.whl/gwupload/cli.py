from pathlib import Path

import rich
import typer
from gwproactor_test.certs import generate_dummy_certs

from gwupload import UploaderApp, service_cli
from gwupload.stubs import stubs_cli

cli_app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode="rich",
    help="Commands for interacting with the Gridworks Uploader",
)

cli_app.add_typer(stubs_cli.app, name="stubs", help="Use stub applications for testing")
cli_app.add_typer(
    service_cli.app, name="service", help="Interact with systemd service for Uploader."
)


@cli_app.command()
def run(
    env_file: str = "",
    *,
    dry_run: bool = False,
    verbose: bool = False,
    message_summary: bool = False,
    aiohttp_verbose: bool = False,
) -> None:
    """Run the uploader."""
    UploaderApp.main(
        env_file=env_file,
        dry_run=dry_run,
        verbose=verbose,
        message_summary=message_summary,
        aiohttp_logging=aiohttp_verbose,
    )


@cli_app.command()
def envfile() -> None:
    """Print the default path to the environment file."""
    rich.print(UploaderApp.default_env_path())


@cli_app.command()
def config(
    env_file: str = "",
) -> None:
    """Show uploader configuration"""
    UploaderApp.print_settings(env_file=env_file)


@cli_app.command()
def gen_test_certs(*, dry_run: bool = False, env_file: str = "") -> None:
    """Generate test certs for the uploader."""
    generate_dummy_certs(
        UploaderApp.get_settings(
            env_file=UploaderApp.default_env_path() if not env_file else Path(env_file)
        ),
        dry_run=dry_run,
    )


@cli_app.callback()
def _main() -> None: ...


# For sphinx:
typer_click_object = typer.main.get_command(cli_app)


if __name__ == "__main__":
    cli_app()
