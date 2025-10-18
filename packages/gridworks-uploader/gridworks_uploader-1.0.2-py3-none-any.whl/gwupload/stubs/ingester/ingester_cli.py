import logging
from pathlib import Path

import rich
import typer
from gwproactor_test.certs import generate_dummy_certs

from gwupload.stubs.ingester.ingester import StubIngesterApp

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode="rich",
    help="GridWorks Dummy Ingester",
)


@app.command()
def run(
    *,
    env_file: str = "",
    dry_run: bool = False,
    verbose: bool = False,
    message_summary: bool = False,
    log_events: bool = False,
) -> None:
    """Run the stub ingester"""
    app_settings = StubIngesterApp.get_settings(
        env_file=StubIngesterApp.default_env_path() if not env_file else Path(env_file),
    )
    if log_events:
        app_settings.event_logger_level = logging.INFO
    StubIngesterApp.main(
        app_settings=app_settings,
        dry_run=dry_run,
        verbose=verbose,
        message_summary=message_summary,
    )


@app.command()
def gen_test_certs(*, dry_run: bool = False, env_file: str = "") -> None:
    """Generate test certs for the stub ingester."""
    generate_dummy_certs(
        StubIngesterApp(
            env_file=StubIngesterApp.default_env_path()
            if not env_file
            else Path(env_file)
        ).settings,
        dry_run=dry_run,
    )


@app.command()
def config(
    env_file: str = "",
) -> None:
    """Show stub ingester configuration"""
    StubIngesterApp.print_settings(
        env_file=StubIngesterApp.default_env_path() if not env_file else Path(env_file)
    )


@app.command()
def envfile() -> None:
    """Print the default path to the environment file."""
    rich.print(StubIngesterApp.default_env_path())


@app.callback()
def _main() -> None: ...


if __name__ == "__main__":
    app()
