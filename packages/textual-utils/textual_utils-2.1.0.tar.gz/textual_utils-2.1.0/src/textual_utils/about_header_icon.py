from typing import Any

from textual import on
from textual.app import App
from textual.events import Click, Mount
from textual.widgets import Header
from textual.widgets._header import HeaderIcon

from textual_utils.app_metadata import AppMetadata
from textual_utils.screens import AboutScreen


class AboutHeaderIcon(HeaderIcon):
    def __init__(self, current_app: App[Any], app_metadata: AppMetadata) -> None:
        super().__init__()

        self.current_app = current_app
        self.app_metadata = app_metadata

        self.icon = app_metadata.icon

    @on(Mount)
    def prevent_default_mount(self, event: Mount) -> None:
        event.prevent_default()

    async def on_click(self, event: Click) -> None:
        event.prevent_default()
        event.stop()
        self.current_app.push_screen(AboutScreen(self.current_app, self.app_metadata))


async def mount_about_header_icon(
    current_app: App[Any], app_metadata: AppMetadata
) -> None:
    header_icon = current_app.query_one(HeaderIcon)
    header_icon.remove()

    header = current_app.query_one(Header)
    about_header_icon = AboutHeaderIcon(current_app, app_metadata)
    await header.mount(about_header_icon)
