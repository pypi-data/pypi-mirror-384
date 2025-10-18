"""Scada implementation"""

import logging
import typing
from logging import Logger, LoggerAdapter
from pathlib import Path
from typing import Any, Optional

from gwproactor import App, AppInterface, AppSettings
from gwproactor.actors.actor import PrimeActor
from gwproactor.config import MQTTClient
from gwproactor.config.links import LinkSettings
from gwproactor.config.proactor_config import ProactorName
from gwproactor.message import MQTTReceiptPayload
from gwproactor.persister import PersisterInterface, SimpleDirectoryWriter
from gwproto import HardwareLayout, Message
from gwproto.messages import EventBase
from pydantic_settings import SettingsConfigDict

from gwupload.app import DEFAULT_INGESTER_SHORT_NAME, DEFAULT_UPLOADER_SHORT_NAME
from gwupload.stubs.names import STUB_INGESTER_LONG_NAME


class StubIngesterSettings(AppSettings):
    long_name: str = STUB_INGESTER_LONG_NAME
    short_name: str = DEFAULT_INGESTER_SHORT_NAME
    uploader_long_name: str = ""
    uploader_short_name: str = DEFAULT_UPLOADER_SHORT_NAME
    uploader: MQTTClient = MQTTClient()
    event_logger_level: int = logging.WARNING
    event_logger_content_len: int = 80

    model_config = SettingsConfigDict(
        env_prefix="STUB_INGESTER_APP_",
    )


class StubIngester(PrimeActor):
    EVENT_LOGGER_NAME: str = "events"
    event_logger: Logger | LoggerAdapter[Logger]

    def __init__(self, name: str, services: AppInterface) -> None:
        super().__init__(name, services)
        self.event_logger = self.services.logger.add_category_logger(
            category=self.EVENT_LOGGER_NAME,
            level=self.settings.event_logger_level,
        )

    @property
    def settings(self) -> StubIngesterSettings:
        return typing.cast("StubIngesterSettings", self.services.settings)

    def event_str(self, event: EventBase) -> str:
        content_str = event.model_dump_json(
            exclude={"MessageId", "TimeCreatedMs", "Src", "TypeName", "Version"}
        )
        if len(content_str) > self.settings.event_logger_content_len - 3:
            content_str = (
                content_str[: self.settings.event_logger_content_len - 3] + "..."
            )
        type_str = f"<{event.TypeName}>"
        return f"Received {type_str:50s}  {content_str}"

    def log_event(self, event: EventBase) -> None:
        self.event_logger.info(self.event_str(event))

    def process_mqtt_message(
        self, _: Message[MQTTReceiptPayload], decoded: Message[Any]
    ) -> None:
        if isinstance(decoded.Payload, EventBase):
            self.log_event(decoded.Payload)


class StubIngesterApp(App):
    UPLOADER_LINK: str = "uploader"

    @classmethod
    def app_settings_type(cls) -> type[StubIngesterSettings]:
        return StubIngesterSettings

    @property
    def settings(self) -> StubIngesterSettings:
        return typing.cast("StubIngesterSettings", self._settings)

    @classmethod
    def prime_actor_type(cls) -> type[StubIngester]:
        return StubIngester

    @classmethod
    def paths_name(cls) -> Optional[str]:
        return STUB_INGESTER_LONG_NAME

    def _get_name(self, layout: HardwareLayout) -> ProactorName:  # noqa: ARG002
        return ProactorName(
            long_name=self.settings.long_name,
            short_name=self.settings.short_name,
        )

    def _load_hardware_layout(self, layout_path: str | Path) -> HardwareLayout:  # noqa: ARG002
        return HardwareLayout(
            layout={},
            cacs={},
            components={},
            nodes={},
            data_channels={},
            synth_channels={},
        )

    def _get_link_settings(
        self,
        name: ProactorName,  # noqa: ARG002
        layout: HardwareLayout,  # noqa: ARG002
        brokers: dict[str, MQTTClient],  # noqa: ARG002
    ) -> dict[str, LinkSettings]:
        return {
            self.UPLOADER_LINK: LinkSettings(
                broker_name=self.UPLOADER_LINK,
                peer_long_name=self.settings.uploader_long_name,
                peer_short_name=self.settings.uploader_short_name,
                downstream=True,
            )
        }

    @classmethod
    def _make_persister(cls, settings: AppSettings) -> PersisterInterface:
        return SimpleDirectoryWriter(settings.paths.event_dir)

    @classmethod
    def get_settings(cls, *args: Any, **kwargs: Any) -> StubIngesterSettings:
        return typing.cast(
            "StubIngesterSettings", super().get_settings(*args, **kwargs)
        )
