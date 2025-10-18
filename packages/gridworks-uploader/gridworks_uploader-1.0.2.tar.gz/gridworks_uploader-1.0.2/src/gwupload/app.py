import typing
from collections.abc import Sequence
from pathlib import Path

from gwproactor import (
    App,
    AppSettings,
    LinkSettings,
    Proactor,
    ProactorName,
    WebEventListener,
)
from gwproactor.actors.web_event_listener import WebEventListenerSettings
from gwproactor.app import ActorConfig
from gwproactor.config import MQTTClient
from gwproactor.external_watchdog import SystemDWatchdogCommandBuilder
from gwproactor.persister import TimedRollingFilePersister
from gwproto import HardwareLayout
from gwproto.named_types.web_server_gt import WebServerGt
from pydantic_settings import SettingsConfigDict

DEFAULT_UPLOADER_SHORT_NAME: str = "u"
DEFAULT_UPLOADER_PATHS_NAME = "uploader"
DEFAULT_INGESTER_SHORT_NAME: str = "i"


class UploaderSettings(AppSettings):
    long_name: str = ""
    short_name: str = DEFAULT_UPLOADER_SHORT_NAME
    ingester_long_name: str = ""
    ingester_short_name: str = DEFAULT_INGESTER_SHORT_NAME
    ingester: MQTTClient = MQTTClient()
    server: WebServerGt = WebServerGt()
    listener: WebEventListenerSettings = WebEventListenerSettings()

    model_config = SettingsConfigDict(
        env_prefix="UPLOADER_APP_",
    )


class UploaderApp(App):
    INGESTER_LINK: str = "ingester"

    @classmethod
    def app_settings_type(cls) -> type[UploaderSettings]:
        return UploaderSettings

    @property
    def settings(self) -> UploaderSettings:
        return typing.cast("UploaderSettings", self._settings)

    @classmethod
    def paths_name(cls) -> str:
        return DEFAULT_UPLOADER_PATHS_NAME

    def _load_hardware_layout(self, layout_path: str | Path) -> HardwareLayout:  # noqa: ARG002
        return HardwareLayout(
            layout={},
            cacs={},
            components={},
            nodes={},
            data_channels={},
            synth_channels={},
        )

    def _get_name(self, layout: HardwareLayout) -> ProactorName:  # noqa: ARG002
        return ProactorName(
            long_name=self.settings.long_name,
            short_name=self.settings.short_name,
        )

    def _get_link_settings(
        self,
        name: ProactorName,  # noqa: ARG002
        layout: HardwareLayout,  # noqa: ARG002
        brokers: dict[str, MQTTClient],  # noqa: ARG002
    ) -> dict[str, LinkSettings]:
        return {
            self.INGESTER_LINK: LinkSettings(
                broker_name=self.INGESTER_LINK,
                peer_long_name=self.settings.ingester_long_name,
                peer_short_name=self.settings.ingester_short_name,
                upstream=True,
            ),
        }

    def _instantiate_proactor(self) -> Proactor:
        proactor = super()._instantiate_proactor()
        proactor.add_web_server_config(
            name=self.settings.server.Name,
            host=self.settings.server.Host,
            port=self.settings.server.Port,
            enabled=self.settings.server.Enabled,
            server_kwargs=self.settings.server.Kwargs,
        )
        return proactor

    def _get_actor_nodes(self) -> Sequence[ActorConfig]:
        return [
            ActorConfig(
                node=self.hardware_layout.add_node(
                    node=WebEventListener.default_node(),
                ),
                constructor_args={"settings": self.settings.listener},
            )
        ]

    @classmethod
    def _make_persister(cls, settings: AppSettings) -> TimedRollingFilePersister:
        return TimedRollingFilePersister(
            settings.paths.event_dir,
            pat_watchdog_args=SystemDWatchdogCommandBuilder.pat_args(
                str(settings.paths.name)
            ),
        )
