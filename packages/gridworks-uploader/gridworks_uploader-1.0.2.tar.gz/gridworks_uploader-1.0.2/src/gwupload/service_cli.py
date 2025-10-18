import logging
import subprocess
import sys
import textwrap
from collections.abc import Sequence
from logging import Logger
from pathlib import Path
from typing import Optional, Self

import rich
import typer
from gwproactor import AppSettings
from pydantic import BaseModel, model_validator

from gwupload import UploaderApp

service_file_format = """
[Unit]
Description={description}
After=multi-user.target

[Service]
Type=simple
Restart=always
User={user}
Environment=VIRTUAL_ENV={virtual_env_path}
Environment={service_env_var}=1
ExecStart={run_command}
RestartSec={restart_sec}
WatchdogSec={watchdog_sec}
NotifyAccess=all

[Install]
WantedBy=multi-user.target
"""

DEFAULT_WATCHDOG_SEC = 20
DEFAULT_RESTART_SEC = 1
UPLODER_RUNNING_AS_SERVICE_ENV_VAR = "UPLOADER_RUNNING_AS_SERVICE"
DEFAULT_UPLOADER_USER = "pi"
UNIT_NAME: str = "gridworks-uploader.service"

logger: Logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


class ServiceConfig(BaseModel):
    description: str = ""
    user: str = ""
    virtual_env_path: str = ""
    service_env_var: str = ""
    run_command: str = ""
    restart_sec: int = DEFAULT_RESTART_SEC
    watchdog_sec: int = DEFAULT_WATCHDOG_SEC

    def service_file_text(self) -> str:
        return service_file_format.format(**self.model_dump())


class UploaderServiceConfig(ServiceConfig):
    description: str = "Gridworks Uploader service"
    user: str = DEFAULT_UPLOADER_USER
    service_env_var: str = UPLODER_RUNNING_AS_SERVICE_ENV_VAR
    env_path: str = ""

    @model_validator(mode="after")
    def construct_run_command(self) -> Self:
        if not self.run_command:
            self.run_command = sys.argv[0] + " run"
            if self.env_path:
                self.run_command += f" \\\n\t--env-file {self.env_path}"
        return self


app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode="rich",
    help="Systemd service for Gridworks Uploader",
)


class SubprocessCommand:
    command: list[str]

    def __init__(self, command: list[str]) -> None:
        self.command = command

    def __str__(self) -> str:
        return " ".join(self.command)

    def run(
        self,
        *,
        dry_run: bool = False,
        raise_on_error: bool = True,
    ) -> int:
        """Run a command"""
        logger.info(str(self))
        if dry_run:
            return 0
        completed = subprocess.run(  # noqa: S603
            self.command,
            check=False,
            capture_output=True,
        )
        prefix = "  "
        if len(completed.stdout):
            logger.info(
                textwrap.indent(text=completed.stdout.decode().strip(), prefix=prefix)
            )
        if len(completed.stderr):
            logger.info(
                textwrap.indent(text=completed.stderr.decode().strip(), prefix=prefix)
            )
        if completed.returncode != 0 and raise_on_error:
            raise ValueError(
                f"ERROR. Command {self!s} "
                f"returned non-zero exit code: {completed.returncode}"
            )
        return completed.returncode


class SystemCtlCommand(SubprocessCommand):
    def __init__(
        self,
        command: str,
        args: Optional[Sequence[str]] = None,
        unit_name: str = UNIT_NAME,
        *,
        sudo_required: bool = True,
    ) -> None:
        self.unit_name = unit_name
        command_list = ["sudo"] if sudo_required else []
        command_list.extend(["systemctl", command])
        if args:
            command_list.extend(args)
        if unit_name:
            command_list.append(self.unit_name)
        super().__init__(command_list)


class UnitFilePaths:
    src_unit_file: Path
    dst_unit_file: Path

    def __init__(
        self, env_file: str = "", settings: Optional[AppSettings] = None
    ) -> None:
        if settings is None:
            settings = UploaderApp.get_settings(
                env_file=env_file or UploaderApp.default_env_path()
            )
        self.src_unit_file = Path(settings.paths.config_dir).absolute() / UNIT_NAME
        self.dst_unit_file = Path("/lib/systemd/system") / UNIT_NAME

    def add_sym_link_command(self) -> SubprocessCommand:
        return SubprocessCommand(
            command=[
                "sudo",
                "ln",
                "-s",
                str(self.src_unit_file),
                str(self.dst_unit_file),
            ]
        )

    def remove_sym_link_command(self) -> SubprocessCommand:
        return SubprocessCommand(
            command=[
                "sudo",
                "rm",
                str(self.dst_unit_file),
            ]
        )


@app.command()
def file(
    env_file: str = "",
) -> str:
    """Print services file path"""
    service_file_path = UnitFilePaths(env_file=env_file).src_unit_file
    rich.print(service_file_path)
    return str(service_file_path)


@app.command()
def generate(
    *,
    user: str = DEFAULT_UPLOADER_USER,
    env_file: str = "",
    force: bool = False,
) -> Path:
    """Create systemd services file for the 'gwup run' command."""
    env_file = env_file or str(UploaderApp.default_env_path())
    settings = UploaderApp.get_settings(env_file=env_file)
    service_file_path = UnitFilePaths(settings=settings).src_unit_file
    rich.print()
    if service_file_path.exists() and not force:
        rich.print(
            f":warning-emoji:    [orange_red1]Services file [/]{service_file_path} [orange_red1]already exists."
        )
        rich.print(":warning-emoji:    [orange_red1][bold]Doing nothing.")
        rich.print()
        rich.print("Use [bold] --force [/bold] to overwrite existing services file.")
    else:
        if service_file_path.exists():
            rich.print(
                f":warning-emoji:    [orange_red1][bold]Overwriting services file [/][/]{service_file_path}."
            )
        else:
            rich.print(f"Creating Uploader service file at {service_file_path}")
        settings.paths.mkdirs()
        service_config = UploaderServiceConfig(
            user=user,
            virtual_env_path=str(Path(sys.executable).parent.absolute()),
            env_path=env_file,
        )
        with service_file_path.open("w") as f:
            f.write(service_config.service_file_text())
        rich.print()
        rich.print("Generated: ")
        with service_file_path.open("r") as f:
            print(textwrap.indent(f.read(), "    "))  # noqa: T201
    rich.print()
    return service_file_path


@app.command()
def start(*, dry_run: bool = False) -> None:
    """Start systemd service"""
    SystemCtlCommand("start").run(dry_run=dry_run)


@app.command()
def restart(*, dry_run: bool = False) -> None:
    """Restart systemd service"""
    SystemCtlCommand("restart").run(dry_run=dry_run)


@app.command()
def stop(*, dry_run: bool = False) -> None:
    """Stop systemd service"""
    SystemCtlCommand("stop").run(dry_run=dry_run)


@app.command()
def status(*, dry_run: bool = False) -> None:
    """Show status of systemd service"""
    SystemCtlCommand(
        command="status",
        args=["--no-pager", "-n", "0"],
        sudo_required=False,
    ).run(dry_run=dry_run, raise_on_error=False)


@app.command()
def reload(*, dry_run: bool = False) -> None:
    """Call systemctl daemon-reload"""
    SystemCtlCommand(command="daemon-reload", unit_name="").run(dry_run=dry_run)


@app.command()
def log(*, since: str = "-1h", dry_run: bool = False) -> None:
    """Follow the service log"""
    command = [
        "journalctl",
        "-u",
        UNIT_NAME,
        "--no-pager",
        "--output",
        "cat",
        "--follow",
    ]
    if since:
        command.extend(["-S", since])
    logger.info(" ".join(command))
    if dry_run:
        return
    with subprocess.Popen(  # noqa: S603
        command, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True
    ) as p:
        for line in p.stdout:  # type: ignore[union-attr]
            print(line, end="")  # noqa: T201


def _uninstall(*, env_file: str = "", dry_run: bool = False) -> None:
    """Uninstall systemd service"""
    env_file = env_file or str(UploaderApp.default_env_path())
    SystemCtlCommand("stop").run(dry_run=dry_run, raise_on_error=False)
    SystemCtlCommand("disable").run(dry_run=dry_run, raise_on_error=False)
    SystemCtlCommand(command="daemon-reload", unit_name="").run(dry_run=dry_run)
    UnitFilePaths(env_file=env_file).remove_sym_link_command().run(
        dry_run=dry_run, raise_on_error=False
    )


@app.command()
def uninstall(*, env_file: str = "", dry_run: bool = False) -> None:
    """Uninstall the systemd service"""
    _uninstall(env_file=env_file, dry_run=dry_run)


@app.command()
def install(*, env_file: str = "", dry_run: bool = False) -> None:
    """Install the systemd service"""
    logger.info("Ensuring a clean environment by uninstalling prior to installing:")
    env_file = env_file or str(UploaderApp.default_env_path())
    _uninstall(env_file=env_file, dry_run=dry_run)
    logger.info("Installing:")
    unit_paths = UnitFilePaths(env_file=env_file)
    unit_paths.add_sym_link_command().run(dry_run=dry_run)
    SystemCtlCommand(command="enable", unit_name=str(unit_paths.dst_unit_file)).run(
        dry_run=dry_run
    )
    logger.info("Starting service:")
    SystemCtlCommand(command="start").run(dry_run=dry_run)


@app.callback()
def main_app_callback() -> None: ...


# For sphinx:
typer_click_object = typer.main.get_command(app)

if __name__ == "__main__":
    app()
