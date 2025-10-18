import random
import time

import httpx
import rich
import typer

from gwupload.stubs.client.client import SomeData

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode="rich",
    help="Stub client for Gridworks Uploader",
)


@app.command()
def run(
    *,
    num_packets: int = 1,
) -> None:
    """Generate and upload random data to local Gridworks Uploader"""

    for packet_idx in range(num_packets):
        response = httpx.post(
            "http://127.0.0.1:8080/events",
            json=SomeData(
                TimestampUTC=round(time.time(), 3),
                Reading=round(random.random(), 3),
            ).model_dump(),
        )
        rich.print(f"Packet {packet_idx + 1} / {num_packets}: {response.status_code}")
        # noinspection PyProtectedMember
        httpx._main.print_response(response)  # noqa: SLF001


@app.callback()
def _main() -> None: ...


if __name__ == "__main__":
    app()
